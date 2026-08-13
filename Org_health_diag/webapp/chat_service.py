# -*- coding: utf-8 -*-
"""조직운영 챗봇 라우팅 (Streamlit chatbot.py의 웹앱 버전).

14개 중분류 키워드에 매칭되면 부서 내부 비교 기반 로컬 답변을,
매칭되지 않으면 web_advisor(Tavily + OpenAI)로 넘긴다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))

import web_advisor  # noqa: E402
from catalog import MID_CATEGORY_ORDER, MID_INTERPRETATION  # noqa: E402
from chatbot import (  # noqa: E402
    CATEGORY_KEYWORDS,
    GREETING_KEYWORDS,
    NEXT_STEP_KEYWORDS,
    SUMMARY_KEYWORDS,
    DISCLAIMER,
    WELCOME,
)
from insights_questions import SAMPLE_QUESTIONS  # noqa: E402

import analytics  # noqa: E402


def match_category(text: str) -> str | None:
    lowered = text.lower()
    for mid, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lowered:
                return mid
    return None


# 개인을 특정해 징계·문책하려는 의도가 보이는 질문은 어떤 경로로도 응답하지 않는다.
# 데이터 자체가 익명 집계라 개인을 특정할 방법이 없고, 그런 용도로 쓰이는 것도
# 이 도구의 목적(대화 촉진)에 어긋난다.
PUNITIVE_KEYWORDS = [
    "혼내", "징계", "문책", "불이익", "갈구", "조져", "조지", "깨야", "처벌", "책임을 물",
]
IDENTIFY_KEYWORDS = ["누가", "누구", "이름", "직급", "색출", "찾아서"]

FOLLOWUP_MARKERS = ["?", "？", "어떻게", "왜", "방법", "조율", "조언", "해결", "대응", "대처"]


def is_punitive_request(text: str) -> bool:
    has_punitive = any(k in text for k in PUNITIVE_KEYWORDS)
    has_identify = any(k in text for k in IDENTIFY_KEYWORDS)
    return has_punitive and has_identify


def looks_like_followup(text: str) -> bool:
    """중분류 키워드가 포함됐어도, 실제로는 카드 재요청이 아니라 구체적인 질문/상황
    설명인 경우 LLM 대화로 넘긴다. 짧고 단순한 키워드 조회는 카드로 응답한다."""
    stripped = text.strip()
    if len(stripped) > 20:
        return True
    return any(marker in stripped for marker in FOLLOWUP_MARKERS)


def respond(user_text: str, org_key: str) -> dict:
    """반환: {'text': 답변, 'source': 'local' | 'local-llm' | 'web' | 'fallback' | 'info' | 'blocked'}"""
    org_row = analytics.get_org(org_key)
    org = org_row["org"]
    lowered = user_text.lower()

    if is_punitive_request(user_text):
        return {
            "text": (
                "이 데이터는 익명 집계라 특정 개인을 찾아낼 수 없고, 그런 용도로 "
                "만들어지지도 않았습니다. 부정 응답이 몰린 영역이 있다면, 누가 그렇게 "
                "답했는지가 아니라 어떤 업무 상황이 그런 응답으로 이어졌는지를 함께 "
                "들여다보는 편이 실제 개선에 더 도움이 됩니다. 궁금한 영역을 말씀해 "
                "주시면 그 관점에서 안내해드리겠습니다."
            ),
            "source": "blocked",
        }

    if any(k in lowered for k in GREETING_KEYWORDS):
        return {"text": WELCOME.format(org=org), "source": "info"}

    year = analytics.latest_year()
    mids = analytics.mid_ratios(year, org)
    top_neg = analytics.top_mids(year, org, "부정")

    if any(k in lowered for k in NEXT_STEP_KEYWORDS):
        lines = ["다음 30일 동안 확인해볼 대화 주제로는 아래 영역을 참고해보시면 좋겠습니다."]
        for row in top_neg:
            lines.append(f"- [{row['중분류']}] {MID_INTERPRETATION[row['중분류']]['방향']}")
        return {"text": "\n".join(lines), "source": "local"}

    if any(k in lowered for k in SUMMARY_KEYWORDS):
        overall = analytics.overall_ratio(year, org)
        top_pos = analytics.top_mids(year, org, "긍정")
        return {
            "text": (
                f"{org}의 {year}년 결과는 긍정 {overall['긍정']}%, 중립 {overall['중립']}%, "
                f"부정 {overall['부정']}%입니다. "
                f"{', '.join(m['중분류'] for m in top_pos)} 영역은 부서 내 다른 영역보다 "
                f"긍정 비중이 높고, {', '.join(m['중분류'] for m in top_neg)} 영역은 "
                "부정 비중이 높게 나타났습니다. 더 알고 싶은 영역을 말씀해 주세요."
            ),
            "source": "local",
        }

    mid = match_category(user_text)
    if mid:
        row = next((m for m in mids if m["중분류"] == mid), None)
        if row:
            major = row["대분류"]
            peer = analytics.peer_avg_for_mid(mids, mid, major)
            comment = analytics.peer_commentary(
                mid, row, peer, f"대분류({major}) 내 다른 영역 평균 대비"
            )

            # 키워드만 짧게 물어본 경우("가용자원")는 카드로, 상황을 설명하거나
            # 질문을 던진 경우("한정적인 자원을 어떻게 조율해야 할까?")는 데이터를
            # 근거로 실제 답을 하는 LLM 대화로 넘긴다. 후자를 카드로만 응답하면
            # 같은 요약을 반복하는 것처럼 느껴진다는 피드백이 있었다.
            if looks_like_followup(user_text) and web_advisor.llm_available():
                context = (
                    f"영역: {mid} (대분류: {major})\n"
                    f"이 부서의 {mid} 응답 비중 — 긍정 {row['긍정']}% · 중립 {row['중립']}% "
                    f"· 부정 {row['부정']}%\n"
                    f"{comment}\n"
                    f"참고용 권장 대화 방향: {MID_INTERPRETATION[mid]['방향']}"
                )
                llm_reply = web_advisor.answer_grounded(user_text, context)
                if llm_reply:
                    return {"text": llm_reply, "source": "local-llm"}

            parts = [
                f"**{mid}** — 긍정 {row['긍정']}% · 중립 {row['중립']}% · 부정 {row['부정']}%",
                comment,
                f"권장 대화 방향: {MID_INTERPRETATION[mid]['방향']}",
            ]
            qs = SAMPLE_QUESTIONS.get(mid)
            if qs:
                parts.append(f"구성원과 나눠볼 질문 예시: {qs[0]}")
            return {"text": "\n\n".join(parts), "source": "local"}

    if web_advisor.available():
        answer = web_advisor.answer(user_text)
        if answer:
            return {
                "text": (
                    "🔎 이 질문은 조직 진단 데이터와는 무관한 일반 리더십/조직관리 주제로 보여, "
                    "웹 검색 자료를 참고해 답변합니다.\n\n" + answer
                ),
                "source": "web",
            }

    return {
        "text": (
            "구체적으로 어떤 영역이 궁금하신가요? 아래 14개 영역 중 하나를 말씀해 주시면 "
            f"해당 영역의 {year} 데이터와 대화 방향을 안내해드립니다.\n\n"
            f"{', '.join(MID_CATEGORY_ORDER)}"
        ),
        "source": "fallback",
    }


def web_tool_available() -> bool:
    return web_advisor.available()


def summarize_history(history: list[tuple[str, str]]) -> str | None:
    """다운로드 리포트용 대화 요약. LLM을 쓸 수 없으면 None(호출부가 원문만 싣는다)."""
    return web_advisor.summarize_conversation(history)
