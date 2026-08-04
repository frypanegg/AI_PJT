# -*- coding: utf-8 -*-
"""규칙 기반 AI 리포트 문장 생성기.

실제 LLM(Report Writer / Action Guide Agent) 호출을 대체하는 로컬 데모 로직이다.
문항 해석 사전(catalog.MID_INTERPRETATION)과 06_guardrails.md의 표현 원칙을 따라
점수·등급·순위·개인 추정 표현 없이 "가능성"과 "점검 방향" 중심 문장을 만든다.
"""

from catalog import MID_INTERPRETATION

# 전사 평균과의 차이가 이 값(%p) 미만이면 "비슷한 수준"으로 본다.
CATEGORY_DIFF_THRESHOLD = 3.0


def category_commentary(mid: str, ratio: dict, company_avg_positive: float) -> str:
    """전사 평균(긍정 비중) 대비 해당 영역이 양호/관찰 필요/비슷한 수준인지 평가한다.

    조직 자체 응답에서 어느 버킷이 큰지가 아니라, 같은 영역의 전사 평균과 비교해
    상대적으로 판단한다 (06_guardrails.md에 따라 절대 점수·등급은 사용하지 않음).
    """
    card = MID_INTERPRETATION[mid]
    diff = round(ratio["긍정"] - company_avg_positive, 1)
    if diff >= CATEGORY_DIFF_THRESHOLD:
        lead = f"{mid} 영역은 전사 평균 대비 긍정 응답 비중이 {diff:+.1f}%p 높아 양호한 편입니다."
        detail = card["긍정"]
    elif diff <= -CATEGORY_DIFF_THRESHOLD:
        lead = f"{mid} 영역은 전사 평균 대비 긍정 응답 비중이 {diff:.1f}%p 낮아 관찰이 필요합니다."
        detail = card["부정"]
    else:
        lead = f"{mid} 영역은 전사 평균과 비슷한 수준입니다 ({diff:+.1f}%p)."
        detail = card["중립"]
    return f"{lead} {detail}"


def executive_summary(org: str, overall: dict, top_pos_df, top_neg_df) -> str:
    pos_names = ", ".join(top_pos_df["중분류"].tolist())
    neg_names = ", ".join(top_neg_df["중분류"].tolist())
    return (
        f"{org}은(는) 2026년 진단에서 전체 긍정 응답 비중 {overall['긍정']}%, "
        f"중립 {overall['중립']}%, 부정 {overall['부정']}%로 나타났습니다. "
        f"특히 {pos_names} 영역에서 긍정 응답 비중이 상대적으로 높게 나타나, "
        f"해당 영역의 구성원 경험이 비교적 안정적으로 형성되어 있을 가능성을 시사합니다. "
        f"반면 {neg_names} 영역은 상대적으로 부정 응답 비중이 높아, "
        f"구성원이 관련 영역에서 불편을 경험했을 가능성이 있어 확인이 필요합니다. "
        f"이 리포트는 특정 원인을 단정하지 않으며, 조직장이 구성원과 나눌 대화의 "
        f"출발점으로 활용하는 것을 권장합니다."
    )


def trend_commentary(mid: str, trend_df):
    pos_2024 = float(trend_df.loc[trend_df["year"] == "2024", "긍정"].iloc[0])
    pos_2026 = float(trend_df.loc[trend_df["year"] == "2026", "긍정"].iloc[0])
    delta = round(pos_2026 - pos_2024, 1)
    if delta >= 5:
        tag = "개선 신호"
        text = f"2024년 대비 2026년 긍정 응답 비중이 {delta}%p 높아져, {mid} 영역에서 개선 신호가 관찰됩니다."
    elif delta <= -5:
        tag = "약화 신호"
        text = f"2024년 대비 2026년 긍정 응답 비중이 {abs(delta)}%p 낮아져, {mid} 영역에서 약화 신호가 관찰됩니다."
    else:
        tag = "큰 변화 없음"
        text = f"2024년부터 2026년까지 {mid} 영역의 긍정 응답 비중은 큰 변화 없이 유지되고 있습니다."
    return tag, text, delta


def signals_to_watch(top_neg_df) -> list:
    signals = []
    for _, row in top_neg_df.iterrows():
        card = MID_INTERPRETATION[row["중분류"]]
        signals.append(f"**{row['중분류']}** (부정 {row['부정']}%) — {card['부정']}")
    return signals


def conversation_topics(top_neg_df) -> list:
    topics = []
    for _, row in top_neg_df.iterrows():
        card = MID_INTERPRETATION[row["중분류"]]
        topics.append(f"[{row['중분류']}] {card['방향']}")
    return topics
