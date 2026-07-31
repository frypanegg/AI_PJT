# -*- coding: utf-8 -*-
"""2026 조직건강도 진단 - Streamlit MVP 데모.

로컬 PC 시연 전용. 조직 LOV + 생년월일 6자리로 데모 인증한 뒤,
부서장 본인 조직의 2026 진단 리포트를 스크롤로 확인한다.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import auth
import chatbot
import data
import insights
import report_export
from catalog import (
    MID_CATEGORY_ORDER,
    MID_TO_MAJOR,
    MID_INTERPRETATION,
    OPEN_TEXT_QUESTIONS,
    QUESTION_ORDER,
    QUESTION_TO_MID,
)

st.set_page_config(
    page_title="2026 조직건강도 진단",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {"긍정": "#3E8E5A", "중립": "#B0B7C3", "부정": "#D9534F"}
BUCKETS = ["긍정", "중립", "부정"]

CUSTOM_CSS = """
<style>
html {scroll-behavior: smooth; font-size: 120%;}
.block-container {padding-top: 2rem; padding-bottom: 6rem; font-size: 1.05rem;}
p, li, label, .stMarkdown, [data-testid="stCaptionContainer"] {font-size: 1.05rem !important; line-height: 1.65;}
h1 {font-size: 2.3rem !important;}
h2 {font-size: 1.9rem !important;}
h3 {font-size: 1.5rem !important;}
[data-testid="stMetricValue"] {font-size: 2.2rem !important;}
[data-testid="stMetricLabel"] {font-size: 1.1rem !important;}
[data-testid="stMetricDelta"] {font-size: 1rem !important;}
button, .stButton button, .stFormSubmitButton button {font-size: 1.1rem !important; padding: 0.6rem 1rem !important;}
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] div {font-size: 1.1rem !important;}
[data-testid="stChatInput"] textarea {font-size: 1.1rem !important;}
[data-testid="stChatMessage"] p {font-size: 1.05rem !important;}
section[data-testid="stSidebar"] {font-size: 1.05rem;}
.oh-card {
    background: var(--secondary-background-color, #f4f6f8);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.7rem;
    border: 1px solid rgba(128,128,128,0.18);
    font-size: 1.05rem;
}
.oh-badge {
    display:inline-block; padding: 4px 13px; border-radius: 999px;
    font-size: 0.95rem; font-weight: 600; color:white; margin-right:6px;
}
.oh-section-title {
    font-size: 1.8rem; font-weight: 700; margin-top: 2.4rem; margin-bottom: 0.7rem;
    border-bottom: 3px solid #3E8E5A; padding-bottom: 0.4rem;
}
.oh-caption {color: #808898; font-size: 0.95rem;}
a.oh-nav {text-decoration:none; display:block; padding:6px 0; color: inherit; font-size: 1.05rem;}
a.oh-nav:hover {color:#3E8E5A;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_FONT = dict(size=15)


def padded_y_range(*value_lists):
    """3개년 추이처럼 변동폭이 작은 데이터를 위해 0-100 고정 대신 데이터 범위에 맞춰 확대."""
    values = [v for series in value_lists for v in series]
    lo, hi = min(values), max(values)
    pad = max((hi - lo) * 0.25, 5)
    return [max(0, lo - pad), min(100, hi + pad)]


def anchor(id_: str):
    st.markdown(f'<div id="{id_}"></div>', unsafe_allow_html=True)


def section_title(text: str):
    st.markdown(f'<div class="oh-section-title">{text}</div>', unsafe_allow_html=True)


def badge(bucket: str, value: float) -> str:
    return f'<span class="oh-badge" style="background:{COLORS[bucket]}">{bucket} {value}%</span>'


# ---------------------------------------------------------------------------
# 인증 페이지
# ---------------------------------------------------------------------------

def login_page():
    left, mid, right = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("## 🧭 2026 조직건강도 진단")
        st.markdown("본인 담당 조직을 선택하고, 등록된 생년월일 6자리를 입력해 주세요.")
        st.markdown(
            '<div class="oh-caption">본 페이지는 사외 시연용 데모입니다. '
            "실제 운영 환경에서는 사내 SSO 인증과 권한 매핑이 적용됩니다.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        options = auth.org_options()
        keys = [k for k, _ in options]
        labels = [v for _, v in options]

        query_org = st.query_params.get("org", "")
        default_idx = keys.index(query_org) if query_org in keys else 0

        with st.form("login_form"):
            picked_label = st.selectbox("조직 선택", labels, index=default_idx)
            picked_key = keys[labels.index(picked_label)]
            birth = st.text_input(
                "생년월일 6자리 (YYMMDD)", max_chars=6, type="password", placeholder="예: 900101"
            )
            submitted = st.form_submit_button("인증하기", use_container_width=True)

        if submitted:
            if len(birth.strip()) != 6 or not birth.strip().isdigit():
                st.error("생년월일 6자리 숫자를 정확히 입력해 주세요.")
            elif auth.verify(picked_key, birth):
                st.session_state.authenticated = True
                st.session_state.org_key = picked_key
                auth.log_access(picked_key, "login_success")
                st.rerun()
            else:
                auth.log_access(picked_key, "login_failed")
                st.error("조직 또는 생년월일 정보가 일치하지 않습니다. 다시 확인해 주세요.")


# ---------------------------------------------------------------------------
# 리포트 페이지
# ---------------------------------------------------------------------------

def donut_chart(ratio: dict):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=BUCKETS,
                values=[ratio[b] for b in BUCKETS],
                hole=0.55,
                marker=dict(colors=[COLORS[b] for b in BUCKETS]),
                hovertemplate="%{label}: %{value}%<br>표본 %{customdata}명<extra></extra>",
                customdata=[ratio["n"]] * 3,
                textinfo="label+percent",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        showlegend=False,
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
        annotations=[dict(text=f"n={ratio['n']}", x=0.5, y=0.5, font_size=19, showarrow=False)],
    )
    return fig


def category_stacked_bar(df: pd.DataFrame, y_col: str, company_avg: pd.DataFrame | None = None):
    order = df[y_col].tolist()
    fig = go.Figure()
    for b in BUCKETS:
        fig.add_trace(
            go.Bar(
                y=df[y_col],
                x=df[b],
                name=b,
                orientation="h",
                marker_color=COLORS[b],
                customdata=df[["n", "대분류"]] if "대분류" in df.columns else None,
                hovertemplate=(
                    f"{b} %{{x}}%%<br>표본 크기 %{{customdata[0]}}명"
                    "<br>대분류 %{customdata[1]}<extra></extra>"
                    if "대분류" in df.columns
                    else f"{b} %{{x}}%<extra></extra>"
                ),
            )
        )
    if company_avg is not None:
        fig.add_trace(
            go.Scatter(
                y=company_avg[y_col],
                x=company_avg["긍정"],
                mode="markers",
                marker=dict(color="black", size=9, symbol="diamond"),
                name="전사 평균(긍정%)",
                hovertemplate="전사 평균 긍정 %{x}%<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="stack",
        height=max(340, 38 * len(order)),
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(title="응답 비중(%)", range=[0, 100]),
        yaxis=dict(categoryorder="array", categoryarray=order[::-1], automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
    )
    return fig


def category_card(row, key_suffix=""):
    mid = row["중분류"]
    with st.container():
        st.markdown(
            f'<div class="oh-card"><b>{mid}</b><br>'
            + badge("긍정", row["긍정"])
            + badge("중립", row["중립"])
            + badge("부정", row["부정"])
            + "</div>",
            unsafe_allow_html=True,
        )
        with st.popover(f"자세히 보기 · {mid}", use_container_width=True):
            card = MID_INTERPRETATION[mid]
            st.markdown(f"**정의**  \n{card['정의']}")
            st.markdown(insights.category_commentary(mid, row))
            st.markdown(f"**권장 대화 방향**  \n{card['방향']}")
            st.caption("점수·등급·순위는 제공하지 않으며, 특정 원인을 단정하지 않습니다.")


def render_report():
    obj_df, text_df, count_df = data.load_data()
    org_key = st.session_state.org_key
    entry = auth.ORG_REGISTRY[org_key]
    org = entry["org"]
    company = entry["company"]

    if data.is_suppressed(count_df, "2026", org):
        st.warning(
            "해당 조직은 응답 인원이 소수 응답 보호 기준 미만이라 결과를 표시할 수 없습니다. "
            "(06_guardrails.md 소수 응답 조직 보호 원칙)"
        )
        return

    # ---- Header ----
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown(f"## {company} · {org}")
        st.caption("2026 조직건강도 진단 리포트 · 본인 담당 조직 전용 · 개인 응답 원문 미노출")
    with top_r:
        if st.button("로그아웃", use_container_width=True):
            auth.log_access(org_key, "logout")
            st.session_state.authenticated = False
            st.session_state.pop("org_key", None)
            st.session_state.pop("chat_history", None)
            st.session_state.pop("chat_org", None)
            st.rerun()

    with st.sidebar:
        st.markdown(f"**{org}**")
        st.caption(company)
        st.markdown("### 바로가기")
        nav = [
            ("summary", "1. 2026 진단 요약"),
            ("category", "2. 카테고리별 결과"),
            ("questions", "3. 32개 문항 근거"),
            ("trend", "4. 3개년 변화 분석"),
            ("aiinsight", "5. AI 조직 운영 인사이트"),
        ]
        for id_, label in nav:
            st.markdown(f'<a class="oh-nav" href="#{id_}">{label}</a>', unsafe_allow_html=True)
        st.divider()
        st.caption("데모 안내: 점수·등급·순위 미제공 / 소수 응답 보호 / 접근 로그 기록")

    respondents = data.respondent_count(count_df, "2026", org)
    target = entry["target_headcount"]
    rate = round(respondents / target * 100, 1)
    overall = data.org_overall_ratio(obj_df, "2026", org)
    top_pos = data.top3_mid(obj_df, "2026", org, by="긍정", ascending=False)
    top_neg = data.top3_mid(obj_df, "2026", org, by="부정", ascending=False)

    # ---- Section 1: 2026 요약 ----
    anchor("summary")
    section_title("1. 2026 진단 요약")

    m1, m2, m3 = st.columns(3)
    m1.metric("응답 인원", f"{respondents}명")
    m2.metric("응답률(가정치)", f"{rate}%", help=f"대상 인원(가정) {target}명 기준 데모 수치")
    m3.metric("전체 긍정 응답 비중", f"{overall['긍정']}%")

    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.plotly_chart(donut_chart(overall), use_container_width=True, config={"displayModeBar": False})
    with c2:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**긍정 응답 Top3 영역**")
            for _, row in top_pos.iterrows():
                category_card(row)
        with cc2:
            st.markdown("**부정 응답 Top3 영역**")
            for _, row in top_neg.iterrows():
                category_card(row)

    st.markdown("**주관식 Top3 요약** (원문 대신 반복적으로 나타난 응답 경향만 요약)")
    t1, t2, t3 = st.columns(3)
    for col, qid in zip((t1, t2, t3), OPEN_TEXT_QUESTIONS):
        with col:
            st.markdown(f"*{OPEN_TEXT_QUESTIONS[qid]}*")
            top3 = data.top3_open_text(text_df, "2026", org, qid)
            if not top3:
                st.caption("데이터 없음")
            for txt in top3:
                st.markdown(f"- {txt}")

    st.markdown("**AI Executive Summary**")
    st.info(insights.executive_summary(org, overall, top_pos, top_neg))

    # ---- Section 2: 카테고리별 결과 ----
    anchor("category")
    section_title("2. 카테고리별 2026 결과")
    st.caption("점 표시는 전사(전체 조직 통합) 평균 긍정 비중입니다. 조직 간 순위 비교 목적이 아닙니다.")

    mid_df = data.all_mid_ratios(obj_df, "2026", org)
    company_avg_rows = []
    for mid in MID_CATEGORY_ORDER:
        company_avg_rows.append({"중분류": mid, **data.company_wide_ratio(obj_df, "2026", mid)})
    company_avg_df = pd.DataFrame(company_avg_rows)

    major_tab1, major_tab2 = st.tabs(["직원 몰입 수준", "회사 지원 수준"])
    for tab, major in zip((major_tab1, major_tab2), ["직원 몰입 수준", "회사 지원 수준"]):
        with tab:
            sub = mid_df[mid_df["대분류"] == major].reset_index(drop=True)
            sub_avg = company_avg_df[company_avg_df["중분류"].isin(sub["중분류"])]
            st.plotly_chart(
                category_stacked_bar(sub, "중분류", sub_avg),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            picked = st.selectbox(
                "중분류 선택해서 해석 보기", sub["중분류"].tolist(), key=f"pick_{major}"
            )
            row = sub[sub["중분류"] == picked].iloc[0]
            card = MID_INTERPRETATION[picked]
            st.markdown(
                badge("긍정", row["긍정"]) + badge("중립", row["중립"]) + badge("부정", row["부정"]),
                unsafe_allow_html=True,
            )
            st.write(insights.category_commentary(picked, row))
            st.caption(f"권장 대화 방향: {card['방향']}")

    # ---- Section 3: 32개 문항별 근거 ----
    anchor("questions")
    section_title("3. 32개 문항별 근거")
    st.caption("점수·등급·순위는 표시하지 않으며 문항별 긍정/중립/부정 비중만 제공합니다.")

    q_df = data.all_question_ratios(obj_df, "2026", org)
    filt_col, sort_col = st.columns([1, 1])
    with filt_col:
        mid_filter = st.selectbox("중분류 필터", ["전체"] + MID_CATEGORY_ORDER, key="qfilter")
    with sort_col:
        sort_by = st.radio("정렬 기준", ["긍정 높은 순", "부정 높은 순"], horizontal=True)

    view = q_df if mid_filter == "전체" else q_df[q_df["중분류"] == mid_filter]
    view = view.sort_values("긍정" if sort_by == "긍정 높은 순" else "부정", ascending=False)

    st.plotly_chart(
        category_stacked_bar(view, "문항"),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption("문항 문구가 길어 그래프 막대 영역이 화면 전체를 채우지 않을 수 있습니다.")

    with st.expander("문항 해석 보기"):
        for _, row in view.iterrows():
            qid = row["문항ID"]
            mid = row["중분류"]
            st.markdown(
                f"**{row['문항']}** ({qid} · {mid}) — "
                + badge("긍정", row["긍정"])
                + badge("중립", row["중립"])
                + badge("부정", row["부정"]),
                unsafe_allow_html=True,
            )
            st.caption(insights.category_commentary(mid, row))
            st.divider()

    # ---- Section 4: 3개년 변화 분석 ----
    anchor("trend")
    section_title("4. 3개년 변화 분석 (2024–2026)")

    overall_trend = data.three_year_trend(obj_df, org, level="overall")
    fig_overall = go.Figure()
    for b in BUCKETS:
        fig_overall.add_trace(
            go.Scatter(
                x=overall_trend["year"],
                y=overall_trend[b],
                mode="lines+markers",
                name=b,
                line=dict(color=COLORS[b], width=3),
                hovertemplate="%{x}년 " + b + " %{y}%<extra></extra>",
            )
        )
    fig_overall.update_layout(
        height=340,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(title="비중(%)", range=padded_y_range(*[overall_trend[b] for b in BUCKETS])),
        xaxis=dict(type="category"),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
    )
    st.plotly_chart(fig_overall, use_container_width=True, config={"displayModeBar": False})
    st.caption("Y축은 실제 변동 폭에 맞춰 확대된 범위이며, 0~100 전체 척도가 아닙니다.")

    deltas = []
    for mid in MID_CATEGORY_ORDER:
        trend_df = data.three_year_trend(obj_df, org, level="mid", key=mid)
        tag, text, delta = insights.trend_commentary(mid, trend_df)
        deltas.append({"중분류": mid, "tag": tag, "text": text, "trend": trend_df, "delta": delta})

    TOP_N_TREND = 5
    improved = sorted(
        [d for d in deltas if d["tag"] == "개선 신호"], key=lambda d: d["delta"], reverse=True
    )[:TOP_N_TREND]
    worsened = sorted([d for d in deltas if d["tag"] == "약화 신호"], key=lambda d: d["delta"])[
        :TOP_N_TREND
    ]

    ic, wc = st.columns(2)
    with ic:
        st.markdown(f"**좋아진 영역 (상위 {TOP_N_TREND}개)**")
        if not improved:
            st.caption("뚜렷한 개선 신호(5%p 이상)가 관찰된 영역이 없습니다.")
        for d in improved:
            st.markdown(f"- {d['text']}")
    with wc:
        st.markdown(f"**약화된 영역 (상위 {TOP_N_TREND}개)**")
        if not worsened:
            st.caption("뚜렷한 약화 신호(5%p 이상)가 관찰된 영역이 없습니다.")
        for d in worsened:
            st.markdown(f"- {d['text']}")

    st.markdown("**중분류 선택해서 3개년 추이 보기**")
    picked_trend_mid = st.selectbox("중분류", MID_CATEGORY_ORDER, key="trend_pick")
    trend_row = next(d for d in deltas if d["중분류"] == picked_trend_mid)
    fig_mid = go.Figure()
    for b in BUCKETS:
        fig_mid.add_trace(
            go.Scatter(
                x=trend_row["trend"]["year"],
                y=trend_row["trend"][b],
                mode="lines+markers",
                name=b,
                line=dict(color=COLORS[b], width=3),
                hovertemplate="%{x}년 " + b + " %{y}%<extra></extra>",
            )
        )
    fig_mid.update_layout(
        height=300,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(range=padded_y_range(*[trend_row["trend"][b] for b in BUCKETS])),
        xaxis=dict(type="category"),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
    )
    st.plotly_chart(fig_mid, use_container_width=True, config={"displayModeBar": False})
    st.caption("Y축은 실제 변동 폭에 맞춰 확대된 범위이며, 0~100 전체 척도가 아닙니다.")
    st.caption(trend_row["text"])

    consistent_low = [
        d["중분류"]
        for d in deltas
        if all(
            float(d["trend"].loc[d["trend"]["year"] == y, "부정"].iloc[0])
            >= float(d["trend"].loc[d["trend"]["year"] == y, "긍정"].iloc[0]) * 0.3
            for y in data.YEARS
        )
    ]
    if consistent_low:
        st.markdown("**3년 연속 관찰이 필요한 영역**")
        st.markdown(
            ", ".join(consistent_low)
            + " — 3개년 동안 상대적으로 부정 응답 비중이 꾸준히 관찰되는 영역입니다. "
            "단정적 원인 진단보다는 반복 관찰 후 대화를 제안합니다."
        )

    # ---- Section 5: AI 조직 운영 인사이트 ----
    anchor("aiinsight")
    section_title("5. AI 조직 운영 인사이트")
    st.caption("AI는 평가자가 아니라 해석자·대화 촉진자입니다. 처방이 아닌 점검 방향을 제안합니다.")

    st.markdown("**현재 조직 건강도 해석**")
    st.write(insights.executive_summary(org, overall, top_pos, top_neg))

    st.markdown("**조직장이 주의해서 살펴볼 신호**")
    for line in insights.signals_to_watch(top_neg):
        st.markdown(f"- {line}")

    st.markdown("**다음 30일 동안 확인해볼 대화 주제**")
    for line in insights.conversation_topics(top_neg):
        st.markdown(f"- {line}")

    st.markdown("**구성원과 나눠볼 수 있는 질문 예시**")
    from insights_questions import SAMPLE_QUESTIONS

    for _, row in top_neg.iterrows():
        mid = row["중분류"]
        qs = SAMPLE_QUESTIONS.get(mid, [])
        if qs:
            with st.expander(f"{mid} 관련 질문 예시"):
                for q in qs:
                    st.markdown(f"- {q}")

    st.divider()
    st.markdown("**조직운영 방식, 대화로 물어보기**")
    st.caption(chatbot.DISCLAIMER)

    if st.session_state.get("chat_org") != org_key:
        st.session_state.chat_history = [("assistant", chatbot.WELCOME.format(org=org))]
        st.session_state.chat_org = org_key

    chat_box = st.container(height=520, border=True)

    quick_topics = ["전체 요약", "다음 30일 무엇부터"] + top_neg["중분류"].tolist()
    quick_cols = st.columns(len(quick_topics))
    for col, label in zip(quick_cols, quick_topics):
        if col.button(label, key=f"quick_{org_key}_{label}", use_container_width=True):
            reply = chatbot.respond(label, org, overall, mid_df, top_pos, top_neg)
            st.session_state.chat_history.append(("user", label))
            st.session_state.chat_history.append(("assistant", reply))

    with chat_box:
        for role, content in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(content)

        user_msg = st.chat_input(
            "궁금한 조직운영 주제를 입력해보세요 (예: 협업, 성과관리, 가용자원)", key=f"chat_input_{org_key}"
        )
    if user_msg:
        reply = chatbot.respond(user_msg, org, overall, mid_df, top_pos, top_neg)
        st.session_state.chat_history.append(("user", user_msg))
        st.session_state.chat_history.append(("assistant", reply))
        st.rerun()

    st.divider()
    st.markdown("**리포트 보관하기**")
    report_html = report_export.build_report_html(
        org=org,
        company=company,
        overall=overall,
        top_pos_df=top_pos,
        top_neg_df=top_neg,
        executive_summary=insights.executive_summary(org, overall, top_pos, top_neg),
        chat_history=st.session_state.chat_history,
    )
    st.download_button(
        "📩 리포트 파일 다운로드 (요약 + 대화 기록 포함)",
        data=report_html,
        file_name=f"{org}_2026_조직건강도_리포트.html",
        mime="text/html",
        use_container_width=True,
    )
    st.caption(
        "이 페이지는 로컬 PC 시연용이라 사내 메일 서버에 직접 연결되어 있지 않습니다. "
        "위 버튼으로 리포트와 챗봇 대화 내용을 담은 파일을 다운로드한 뒤, 본인 회사 메일에 "
        "첨부해 보내시면 자료를 보관하거나 공유하실 수 있습니다."
    )

    st.divider()
    st.caption(
        "본 리포트는 시연용 데모이며 평가 점수·등급·순위를 제공하지 않습니다. "
        "AI 해석 문장은 사전 정의된 해석 로직 기반 예시로, 실제 적용 시 Guardrail Reviewer Agent의 "
        "최종 검수를 거치도록 설계되어 있습니다."
    )


# ---------------------------------------------------------------------------
# 라우팅
# ---------------------------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    render_report()
else:
    login_page()
