# -*- coding: utf-8 -*-
"""조직운영 대화형 도우미 (Action Guide Agent 데모).

사용자의 자유 입력을 14개 중분류 키워드와 매칭해 해당 영역의 해석 카드
(catalog.MID_INTERPRETATION)와 조직의 2026 실제 응답 비중을 조합한
guardrail-safe 응답을 로컬에서 생성한다.

중분류와 매칭되지 않는 일반적인 리더십/조직관리 질문은 web_advisor Tool로
넘겨 웹검색 기반 답변을 시도한다 (API 키가 없거나 실패하면 조용히 오프라인
주제 목록 안내로 대체한다).
"""

import insights
import web_advisor
from catalog import MID_CATEGORY_ORDER, MID_INTERPRETATION
from insights_questions import SAMPLE_QUESTIONS

# 중분류별 매칭 키워드(중분류명 자체 + 자연어 동의어)
CATEGORY_KEYWORDS = {
    "자발적 몰입": ["자발적 몰입", "몰입", "자긍심", "애사심", "이직"],
    "방향성 제시": ["방향성", "전략", "목표"],
    "리더에 대한 신뢰": ["리더", "신뢰", "상사"],
    "존경과 인정": ["존경", "인정", "존중"],
    "급여 및 복리후생": ["급여", "복리후생", "보상", "연봉", "복지"],
    "개발기회": ["개발기회", "성장", "커리어", "경력"],
    "실행환경 조성": ["실행환경", "업무환경", "환경"],
    "권한/임파워먼트": ["권한", "임파워먼트", "위임"],
    "협업": ["협업", "협력", "팀워크"],
    "업무/구조/프로세스": ["프로세스", "구조", "업무방식", "일하는 방식"],
    "교육훈련": ["교육", "훈련", "트레이닝"],
    "가용자원": ["자원", "인력", "예산"],
    "성과관리": ["성과관리", "피드백", "평가"],
    "DEIB": ["deib", "다양성", "포용", "공정", "차별"],
}

GREETING_KEYWORDS = ["안녕", "hi", "hello", "시작"]
SUMMARY_KEYWORDS = ["요약", "전체", "종합", "어때"]
NEXT_STEP_KEYWORDS = ["다음", "30일", "무엇부터", "뭐부터", "먼저", "우선순위"]

DISCLAIMER = (
    "이 대화는 평가·처방이 아닌 점검 방향을 제안하는 참고용입니다. 특정 원인을 단정하지 않습니다. "
    "조직의 진단 데이터(14개 영역) 관련 답변은 사전 정의된 해석 로직으로 완전히 로컬에서 처리되며, "
    "데이터가 외부로 전송되지 않습니다. 그 외 일반적인 리더십/조직관리 질문은 (설정된 경우) 웹검색 "
    "Tool을 통해 질문 문장만 외부 API로 전달되어 답변을 생성합니다 — 이 경우에도 조직의 진단 데이터는 전달되지 않습니다."
)

WELCOME = (
    "안녕하세요. {org} 2026 진단 결과를 바탕으로 대화하는 조직운영 도우미입니다. "
    "궁금한 영역(예: 협업, 성과관리, 가용자원 등)을 말씀해 주시거나, "
    "'요약'이라고 입력하시면 전체 결과를 다시 안내해드립니다. "
    "14개 영역과 무관한 일반적인 리더십 질문도 편하게 물어보세요."
)


def match_category(text: str):
    lowered = text.lower()
    for mid, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lowered:
                return mid
    return None


def category_reply(mid: str, mid_df, company_avg_df) -> str:
    row = mid_df[mid_df["중분류"] == mid].iloc[0]
    avg_positive = company_avg_df.loc[company_avg_df["중분류"] == mid, "긍정"].iloc[0]
    card = MID_INTERPRETATION[mid]
    lines = [
        f"**{mid}** — 긍정 {row['긍정']}% · 중립 {row['중립']}% · 부정 {row['부정']}%",
        insights.category_commentary(mid, row, avg_positive),
        f"권장 대화 방향: {card['방향']}",
    ]
    qs = SAMPLE_QUESTIONS.get(mid)
    if qs:
        lines.append(f"구성원과 나눠볼 질문 예시: {qs[0]}")
    return "\n\n".join(lines)


def fallback_reply() -> str:
    topics = ", ".join(MID_CATEGORY_ORDER)
    return (
        "구체적으로 어떤 영역이 궁금하신가요? 아래 14개 영역 중 하나를 말씀해 주시면 "
        f"해당 영역의 2026 데이터와 대화 방향을 안내해드립니다.\n\n{topics}"
    )


def respond(
    user_text: str, org: str, overall: dict, mid_df, top_pos_df, top_neg_df, company_avg_df
) -> str:
    lowered = user_text.lower()

    if any(k in lowered for k in GREETING_KEYWORDS):
        return WELCOME.format(org=org)

    if any(k in lowered for k in NEXT_STEP_KEYWORDS):
        lines = ["다음 30일 동안 확인해볼 대화 주제로는 아래 영역을 참고해보시면 좋겠습니다."]
        for _, row in top_neg_df.iterrows():
            card = MID_INTERPRETATION[row["중분류"]]
            lines.append(f"- [{row['중분류']}] {card['방향']}")
        return "\n".join(lines)

    if any(k in lowered for k in SUMMARY_KEYWORDS):
        pos_names = ", ".join(top_pos_df["중분류"].tolist())
        neg_names = ", ".join(top_neg_df["중분류"].tolist())
        return (
            f"{org}의 2026년 결과는 긍정 {overall['긍정']}%, 중립 {overall['중립']}%, "
            f"부정 {overall['부정']}%입니다. {pos_names} 영역은 상대적으로 긍정 비중이 높고, "
            f"{neg_names} 영역은 상대적으로 부정 비중이 높게 나타났습니다. "
            "더 자세히 알고 싶은 영역이 있으면 이름을 말씀해 주세요."
        )

    mid = match_category(user_text)
    if mid:
        return category_reply(mid, mid_df, company_avg_df)

    if web_advisor.available():
        web_answer = web_advisor.answer(user_text)
        if web_answer:
            return (
                "🔎 이 질문은 조직 진단 데이터와는 무관한 일반 리더십/조직관리 주제로 보여, "
                "웹 검색 자료를 참고해 답변합니다.\n\n" + web_answer
            )

    return fallback_reply()
