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


def respond(user_text: str, org_key: str) -> dict:
    """반환: {'text': 답변, 'source': 'local' | 'web' | 'fallback' | 'info'}"""
    org_row = analytics.get_org(org_key)
    org = org_row["org"]
    lowered = user_text.lower()

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
            parts = [
                f"**{mid}** — 긍정 {row['긍정']}% · 중립 {row['중립']}% · 부정 {row['부정']}%",
                analytics.peer_commentary(
                    mid, row, peer, f"대분류({major}) 내 다른 영역 평균 대비"
                ),
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
