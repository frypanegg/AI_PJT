# -*- coding: utf-8 -*-
"""2026 조직건강도 진단 - Streamlit MVP 데모.

로컬 PC 시연 전용. 조직 LOV + 생년월일 6자리로 데모 인증한 뒤,
부서장 본인 조직의 2026 진단 리포트를 스크롤로 확인한다.
"""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import auth
import chatbot
import data
import insights
import report_export
import web_advisor
from catalog import (
    MID_CATEGORY_ORDER,
    MID_INTERPRETATION,
    OPEN_TEXT_QUESTIONS,
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
.oh-item-title {
    font-size: 1.3rem; font-weight: 700; line-height: 1.45;
    margin-top: 0.2rem; margin-bottom: 0.1rem;
}
.oh-item-meta {
    color: #808898; font-size: 0.9rem; letter-spacing: 0.02em;
    margin-bottom: 0.1rem;
}
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


def trend_bucket_chart(trend_df: pd.DataFrame, bucket: str):
    """긍정/중립/부정을 각각 독립된 스케일로 보여주는 단일 시리즈 3개년 추이 차트."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend_df["year"],
            y=trend_df[bucket],
            mode="lines+markers",
            line=dict(color=COLORS[bucket], width=3),
            marker=dict(size=9),
            hovertemplate="%{x}년 " + bucket + " %{y}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=bucket, font=dict(size=17, color=COLORS[bucket])),
        height=260,
        margin=dict(t=45, b=10, l=10, r=10),
        yaxis=dict(range=padded_y_range(trend_df[bucket]), title="비중(%)"),
        xaxis=dict(type="category"),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
        showlegend=False,
    )
    return fig


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
    top_l, top_r = st.columns([5, 1])
    with top_r:
        if st.button("🔐 Admin", use_container_width=True):
            st.session_state.show_admin_login = True
            st.rerun()

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


def admin_login_page():
    left, mid, right = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("## 🔐 관리자 로그인")
        st.markdown(
            '<div class="oh-caption">HR 관리자/경영진 전용 화면입니다. '
            "부서별 결과 비교와 부서장 접근 이력을 확인할 수 있습니다.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        with st.form("admin_login_form"):
            admin_id = st.text_input("관리자 ID")
            admin_pw = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("관리자 로그인", use_container_width=True)

        if submitted:
            if auth.verify_admin(admin_id, admin_pw):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("ID 또는 비밀번호가 일치하지 않습니다.")

        if st.button("← 부서장 로그인으로 돌아가기"):
            st.session_state.show_admin_login = False
            st.rerun()


# ---------------------------------------------------------------------------
# 리포트 페이지
# ---------------------------------------------------------------------------

def donut_chart(ratio: dict, respondents: int):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=BUCKETS,
                values=[ratio[b] for b in BUCKETS],
                hole=0.55,
                marker=dict(colors=[COLORS[b] for b in BUCKETS]),
                hovertemplate="%{label}: %{value}%<br>문항 응답 %{customdata}건<extra></extra>",
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
        annotations=[
            dict(text=f"{respondents}명", x=0.5, y=0.5, font_size=19, showarrow=False)
        ],
    )
    return fig


def ratio_bar(row, height: int = 74):
    """단일 항목의 긍정/중립/부정 비중을 하나의 막대로 보여준다.

    비율 수치를 막대 안에 직접 넣어(범례·축 없이) 컴팩트하게 만들고, y축 라벨을
    쓰지 않아 문항 길이와 무관하게 모든 막대가 같은 위치에서 시작한다.

    주의: 스택 막대에서는 Plotly가 바깥쪽 텍스트 배치를 지원하지 않아, 폭이 좁아
    글자가 안 들어가면 라벨을 통째로 감춘다. 그래서 좁은 구간은 막대 안에 넣지 않고
    막대 오른쪽에 주석으로 따로 표시한다.
    """
    INSIDE_MIN = 11.0  # 이 비중 미만이면 막대 안에 글자가 안정적으로 들어가지 않는다
    fig = go.Figure()
    overflow = []

    for b in BUCKETS:
        value = float(row[b])
        if value >= INSIDE_MIN:
            label = f"{b} {value}%" if value >= 16 else f"{value}%"
        else:
            label = ""
            if value > 0:
                overflow.append((b, value))
        fig.add_trace(
            go.Bar(
                y=[""],
                x=[value],
                name=b,
                orientation="h",
                marker_color=COLORS[b],
                text=[label],
                textposition="inside",
                insidetextanchor="middle",
                textangle=0,
                constraintext="none",
                insidetextfont=dict(color="white", size=14),
                hovertemplate=f"{b} {value}%<extra></extra>",
            )
        )

    for i, (b, value) in enumerate(overflow):
        fig.add_annotation(
            # 축 좌표(0~100) 밖은 그려지지 않으므로 paper 좌표로 오른쪽 여백에 배치한다
            xref="paper",
            yref="paper",
            x=1.005,
            y=0.5,
            yshift=(len(overflow) - 1 - 2 * i) * 9,  # 여러 개면 위아래로 나눠 겹치지 않게
            text=f"{b} {value}%",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(color=COLORS[b], size=13),
        )

    fig.update_layout(
        barmode="stack",
        height=height,
        # 막대 밖 주석이 잘리지 않도록 오른쪽 여백 확보
        margin=dict(t=8, b=8, l=0, r=96 if overflow else 8),
        xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        showlegend=False,
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
        bargap=0.15,
    )
    return fig


def rank_list_html(ranked_items, tone: str = "positive") -> str:
    rows = []
    for i, d in enumerate(ranked_items, start=1):
        sign = "+" if d["delta"] >= 0 else ""
        if d["delta"] < 0:
            color = COLORS["부정"]
        elif tone == "attention":
            color = "#9a7b00"  # 하락은 아니지만 상대적으로 개선 폭이 작은 항목 (주의색)
        else:
            color = COLORS["긍정"]
        rows.append(
            '<div style="display:flex; align-items:center; padding:14px 4px; '
            'border-bottom:1px solid rgba(128,128,128,0.15);">'
            f'<div style="font-size:1.5rem; font-weight:800; width:2.4rem; color:#9aa1ab;">{i}</div>'
            f'<div style="flex:1; font-size:1.2rem; font-weight:600;">{d["중분류"]}</div>'
            f'<div style="font-size:1.4rem; font-weight:800; color:{color};">{sign}{d["delta"]}%p</div>'
            "</div>"
        )
    return "".join(rows)


def proportion_bar(row) -> str:
    return (
        '<div style="display:flex; height:16px; border-radius:5px; overflow:hidden; '
        'margin:8px 0 10px 0;">'
        f'<div style="width:{row["긍정"]}%; background:{COLORS["긍정"]};"></div>'
        f'<div style="width:{row["중립"]}%; background:{COLORS["중립"]};"></div>'
        f'<div style="width:{row["부정"]}%; background:{COLORS["부정"]};"></div>'
        "</div>"
    )


def category_card(row, peer_avg_positive, peer_label: str):
    mid = row["중분류"]
    with st.container():
        st.markdown(
            f'<div class="oh-card"><b style="font-size:1.15rem;">{mid}</b>'
            + proportion_bar(row)
            + badge("긍정", row["긍정"])
            + badge("중립", row["중립"])
            + badge("부정", row["부정"])
            + "</div>",
            unsafe_allow_html=True,
        )
        with st.popover("자세히 보기", use_container_width=True):
            card = MID_INTERPRETATION[mid]
            st.markdown(f"**정의**  \n{card['정의']}")
            st.markdown(insights.peer_commentary(mid, row, peer_avg_positive, peer_label))
            st.markdown(f"**권장 대화 방향**  \n{card['방향']}")
            st.caption(
                "우리 부서 내부 영역 간 비교 결과이며, 다른 부서·전사 평균과 비교하지 않습니다. "
                "점수·등급·순위는 제공하지 않습니다."
            )


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

    mid_df = data.all_mid_ratios(obj_df, "2026", org)
    q_df_all = data.all_question_ratios(obj_df, "2026", org)

    # 부서 간 비교를 지양하라는 지침에 따라, 비교 기준은 전사 평균이 아니라
    # '우리 부서 안의 다른 항목 평균'이다.
    dept_avg_positive = overall["긍정"]
    DEPT_PEER_LABEL = "우리 부서 전체 평균 대비"

    # ---- Section 1: 2026 요약 ----
    anchor("summary")
    section_title("1. 2026 진단 요약")

    m1, m2, m3 = st.columns(3)
    m1.metric("응답 인원", f"{respondents}명")
    m2.metric("응답률(가정치)", f"{rate}%", help=f"대상 인원(가정) {target}명 기준 데모 수치")
    m3.metric("전체 긍정 응답 비중", f"{overall['긍정']}%")

    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.plotly_chart(
            donut_chart(overall, respondents), use_container_width=True, config={"displayModeBar": False}
        )
    with c2:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**긍정 응답 Top3 영역**")
            for _, row in top_pos.iterrows():
                category_card(row, dept_avg_positive, DEPT_PEER_LABEL)
        with cc2:
            st.markdown("**부정 응답 Top3 영역**")
            for _, row in top_neg.iterrows():
                category_card(row, dept_avg_positive, DEPT_PEER_LABEL)

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
    st.caption(
        "각 영역을 같은 대분류 안의 다른 영역 평균과 비교해 서술합니다. "
        "다른 부서·전사 평균과는 비교하지 않습니다."
    )

    major_tab1, major_tab2 = st.tabs(["직원 몰입 수준", "회사 지원 수준"])
    for tab, major in zip((major_tab1, major_tab2), ["직원 몰입 수준", "회사 지원 수준"]):
        with tab:
            sub = mid_df[mid_df["대분류"] == major].reset_index(drop=True)
            for _, row in sub.iterrows():
                mid = row["중분류"]
                card = MID_INTERPRETATION[mid]
                peer_avg = data.peer_avg_for_mid(mid_df, mid, major)
                st.markdown(f'<div class="oh-item-title">{mid}</div>', unsafe_allow_html=True)
                st.plotly_chart(
                    ratio_bar(row),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    # 비율이 같은 영역끼리 figure가 완전히 동일해져 자동 ID가 충돌하므로 key를 명시한다
                    key=f"midbar_{major}_{mid}",
                )
                st.write(
                    insights.peer_commentary(
                        mid, row, peer_avg, f"대분류({major}) 내 다른 영역 평균 대비"
                    )
                )
                st.caption(f"권장 대화 방향: {card['방향']}")
                st.divider()

    # ---- Section 3: 32개 문항별 근거 ----
    anchor("questions")
    section_title("3. 32개 문항별 근거")
    st.caption(
        "각 문항을 같은 중분류 안의 다른 문항 평균과 비교해 서술합니다. "
        "점수·등급·순위는 표시하지 않으며, 다른 부서·전사 평균과는 비교하지 않습니다."
    )

    q_df = q_df_all
    filt_col, sort_col = st.columns([1, 1])
    with filt_col:
        mid_filter = st.selectbox("중분류 필터", ["전체"] + MID_CATEGORY_ORDER, key="qfilter")
    with sort_col:
        sort_by = st.radio("정렬 기준", ["긍정 높은 순", "부정 높은 순"], horizontal=True)

    view = q_df if mid_filter == "전체" else q_df[q_df["중분류"] == mid_filter]
    view = view.sort_values("긍정" if sort_by == "긍정 높은 순" else "부정", ascending=False)

    for _, row in view.iterrows():
        qid = row["문항ID"]
        mid = row["중분류"]
        peer_avg, peer_label = data.peer_avg_for_question(q_df, qid, mid)
        # 문항 원문을 크게 두어 서로 다른 문항임이 먼저 보이게 하고,
        # 중분류·문항ID는 보조 정보로 작게 표시한다.
        st.markdown(f'<div class="oh-item-title">{row["문항"]}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="oh-item-meta">{qid} · {mid}</div>', unsafe_allow_html=True
        )
        st.plotly_chart(
            ratio_bar(row),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"qbar_{qid}",
        )
        st.caption(insights.peer_commentary(mid, row, peer_avg, peer_label or ""))
        st.divider()

    # ---- Section 4: 3개년 변화 분석 ----
    anchor("trend")
    section_title("4. 3개년 변화 분석 (2024–2026)")

    overall_trend = data.three_year_trend(obj_df, org, level="overall")
    st.markdown("**전체 응답 비중 추이**")
    st.caption("긍정/중립/부정을 각각 독립된 축으로 확대해, 작은 변화도 보이도록 했습니다 (0~100 공통 척도 아님).")
    ov_cols = st.columns(3)
    for col, b in zip(ov_cols, BUCKETS):
        with col:
            st.plotly_chart(
                trend_bucket_chart(overall_trend, b),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"trend_overall_{b}",
            )

    deltas = []
    for mid in MID_CATEGORY_ORDER:
        trend_df = data.three_year_trend(obj_df, org, level="mid", key=mid)
        tag, text, delta = insights.trend_commentary(mid, trend_df)
        deltas.append({"중분류": mid, "tag": tag, "text": text, "trend": trend_df, "delta": delta})

    TOP_N_TREND = 5
    ranked_desc = sorted(deltas, key=lambda d: d["delta"], reverse=True)
    top_improved = ranked_desc[:TOP_N_TREND]
    least_improved = sorted(deltas, key=lambda d: d["delta"])[:TOP_N_TREND]

    st.markdown("**2024 → 2026 긍정 응답 비중 변화 순위**")
    st.caption(
        "연도별 절대 변화폭은 크지 않아, 오르내림 여부보다 상대적인 순위로 참고하시는 것을 권장합니다."
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("##### 개선 순위 (상위 5개)")
        st.markdown(rank_list_html(top_improved), unsafe_allow_html=True)
    with rc2:
        worst_delta = least_improved[0]["delta"] if least_improved else 0
        title = "약화 순위 (상위 5개)" if worst_delta < 0 else "관찰이 필요한 영역 (하위 5개)"
        st.markdown(f"##### {title}")
        if worst_delta >= 0:
            st.caption("뚜렷한 하락은 없었지만, 상대적으로 개선 폭이 가장 작았던 영역입니다.")
        st.markdown(rank_list_html(least_improved, tone="attention"), unsafe_allow_html=True)

    st.markdown("**중분류 선택해서 3개년 추이 보기**")
    picked_trend_mid = st.selectbox("중분류", MID_CATEGORY_ORDER, key="trend_pick")
    trend_row = next(d for d in deltas if d["중분류"] == picked_trend_mid)
    mid_cols = st.columns(3)
    for col, b in zip(mid_cols, BUCKETS):
        with col:
            st.plotly_chart(
                trend_bucket_chart(trend_row["trend"], b),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"trend_mid_{b}",
            )
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

    if web_advisor.available():
        st.caption("🔎 일반 리더십/조직관리 질문은 웹검색 기반 답변 Tool이 연결되어 있습니다.")
    else:
        st.caption("일반 리더십 질문용 웹검색 Tool은 API 키가 설정되지 않아 비활성 상태입니다 (DEMO_GUIDE.md 참고).")

    quick_topics = ["전체 요약", "다음 30일"] + top_neg["중분류"].tolist()
    quick_cols = st.columns(len(quick_topics))
    for col, label in zip(quick_cols, quick_topics):
        if col.button(label, key=f"quick_{org_key}_{label}", use_container_width=True):
            with st.spinner("답변 생성 중..."):
                reply = chatbot.respond(label, org, overall, mid_df, top_pos, top_neg)
            st.session_state.chat_history.append(("user", label))
            st.session_state.chat_history.append(("assistant", reply))
            auth.log_access(org_key, "chat_message")

    chat_box = st.container(height=520, border=True)
    with chat_box:
        for role, content in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(content)

        user_msg = st.chat_input(
            "궁금한 조직운영 주제를 입력해보세요 (예: 협업, 성과관리, 리더십 일반)", key=f"chat_input_{org_key}"
        )
    if user_msg:
        with st.spinner("답변 생성 중..."):
            reply = chatbot.respond(user_msg, org, overall, mid_df, top_pos, top_neg)
        st.session_state.chat_history.append(("user", user_msg))
        st.session_state.chat_history.append(("assistant", reply))
        auth.log_access(org_key, "chat_message")
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
    downloaded = st.download_button(
        "📩 리포트 파일 다운로드 (요약 + 대화 기록 포함)",
        data=report_html,
        file_name=f"{org}_2026_조직건강도_리포트.html",
        mime="text/html",
        use_container_width=True,
    )
    if downloaded:
        auth.log_access(org_key, "report_download")
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
# 관리자 화면
# ---------------------------------------------------------------------------

def render_data_upload():
    """Raw Data 엑셀 업로드 · 검증 · 되돌리기 (관리자 전용)."""
    section_title("1. Raw Data 업로드")

    if data.is_using_uploaded():
        st.success(
            "현재 **업로드된 Raw Data**를 사용 중입니다. "
            f"(파일: `{os.path.basename(data.UPLOADED_EXCEL_PATH)}`)"
        )
    else:
        st.info(
            "현재 **기본 제공 더미 데이터**를 사용 중입니다. "
            f"(파일: `{os.path.basename(data.DEFAULT_EXCEL_PATH)}`)"
        )

    with st.expander("업로드 파일 형식 안내", expanded=False):
        st.markdown(
            "- **시트**: `2024`, `2025`, `2026` 3개가 모두 있어야 합니다.\n"
            "- **1행**: 컬럼 ID (`회사명`, `조직명`, `OS02`, `OM12` … 32개 문항ID, `C1`~`C3`)\n"
            "- **2행**: 문항 원문 (읽지 않고 건너뜁니다)\n"
            "- **3행부터**: 응답 데이터 1인 1행\n"
            "- **응답값**: `전적으로 동의(공감)함` / `동의(공감)함` / `어느 쪽도 아님` / "
            "`동의(공감)하지 않음` / `전혀 동의(공감)하지 않음`\n"
            "- **조직명**은 시스템에 등록된 부서명과 일치해야 해당 부서 결과가 표시됩니다."
        )

    # 되돌리기 후에도 업로더가 이전 파일을 들고 있으면 rerun 직후 그 파일이 다시 적용된다.
    # key에 세대(generation) 번호를 붙여, 되돌릴 때 위젯 자체를 비운다.
    gen = st.session_state.get("uploader_generation", 0)
    uploaded = st.file_uploader(
        "조직건강도 설문 Raw Data 엑셀 파일 (.xlsx)", type=["xlsx"], key=f"raw_data_uploader_{gen}"
    )

    if uploaded is not None:
        signature = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("last_upload_signature") != signature:
            with st.spinner("파일을 검증하고 있습니다..."):
                ok, errors, warnings, stats = data.save_uploaded_workbook(uploaded.getvalue())
            st.session_state.last_upload_signature = signature
            st.session_state.last_upload_result = (ok, errors, warnings, stats, uploaded.name)
            if ok:
                st.rerun()

    result = st.session_state.get("last_upload_result")
    if result:
        ok, errors, warnings, stats, fname = result
        if ok:
            st.success(f"`{fname}` 적용 완료. 아래 분석 결과와 부서장 리포트에 반영되었습니다.")
            if stats:
                cols = st.columns(len(stats))
                for col, (label, value) in zip(cols, stats.items()):
                    col.metric(label, value)
        else:
            st.error(f"`{fname}` 을(를) 적용하지 못했습니다. 기존 데이터가 그대로 유지됩니다.")
            for msg in errors:
                st.markdown(f"- {msg}")
        for msg in warnings:
            st.warning(msg)

    if data.is_using_uploaded():
        if st.button("기본 더미 데이터로 되돌리기"):
            data.reset_to_default_workbook()
            st.session_state.pop("last_upload_signature", None)
            st.session_state.pop("last_upload_result", None)
            st.session_state.uploader_generation = gen + 1  # 업로더 위젯 초기화
            st.rerun()

    st.divider()


def render_admin():
    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.markdown("## 🔐 관리자 화면")
        st.caption("Raw Data 관리 · 부서별 결과 비교 · 부서장 접근 이력 (HR 관리자·경영진 전용)")
    with top_r:
        if st.button("로그아웃", use_container_width=True, key="admin_logout"):
            st.session_state.is_admin = False
            st.session_state.show_admin_login = False
            st.rerun()

    render_data_upload()

    obj_df, text_df, count_df = data.load_data()
    company_wide_2026 = data.company_wide_ratio(obj_df, "2026")

    # ---- 2. 부서별 2026 결과 비교 ----
    section_title("2. 부서별 2026 결과 비교")
    st.caption(
        f"점수·등급은 제공하지 않으며, 전사 평균(긍정 {company_wide_2026['긍정']}%) 대비 "
        f"±{insights.CATEGORY_DIFF_THRESHOLD}%p를 기준으로 우수/관심 필요를 구분합니다. "
        "문항별 세부 정의는 이 화면의 목적이 아닙니다."
    )

    dept_rows = []
    for org_key, entry in auth.ORG_REGISTRY.items():
        org_name = entry["org"]
        if data.is_suppressed(count_df, "2026", org_name):
            continue
        ratio = data.org_overall_ratio(obj_df, "2026", org_name)
        respondents = data.respondent_count(count_df, "2026", org_name)
        diff = round(ratio["긍정"] - company_wide_2026["긍정"], 1)
        if diff >= insights.CATEGORY_DIFF_THRESHOLD:
            tag = "🟢 우수 부서"
        elif diff <= -insights.CATEGORY_DIFF_THRESHOLD:
            tag = "🔴 관심 필요 부서"
        else:
            tag = "⚪ 평균 수준"
        dept_rows.append(
            {
                "회사명": entry["company"],
                "부서명": org_name,
                "응답인원": respondents,
                "긍정%": ratio["긍정"],
                "중립%": ratio["중립"],
                "부정%": ratio["부정"],
                "전사 평균 대비": f"{diff:+.1f}%p",
                "구분": tag,
            }
        )
    dept_df = pd.DataFrame(dept_rows).sort_values("긍정%", ascending=False).reset_index(drop=True)
    st.dataframe(dept_df, use_container_width=True, hide_index=True)

    fig = go.Figure()
    bar_colors = []
    for tag in dept_df["구분"]:
        if tag == "🟢 우수 부서":
            bar_colors.append(COLORS["긍정"])
        elif tag == "🔴 관심 필요 부서":
            bar_colors.append(COLORS["부정"])
        else:
            bar_colors.append(COLORS["중립"])
    fig.add_trace(
        go.Bar(
            x=dept_df["부서명"],
            y=dept_df["긍정%"],
            marker_color=bar_colors,
            hovertemplate="%{x}<br>긍정 %{y}%<extra></extra>",
        )
    )
    fig.add_hline(
        y=company_wide_2026["긍정"],
        line_dash="dash",
        line_color="black",
        annotation_text=f"전사 평균 {company_wide_2026['긍정']}%",
        annotation_position="top left",
    )
    fig.update_layout(
        height=320,
        margin=dict(t=30, b=10, l=10, r=10),
        yaxis=dict(title="긍정 비중(%)", range=[0, 100]),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # ---- 2. 부서별 2024-2026 변화 추이 ----
    section_title("3. 부서별 2024–2026 변화 추이")
    st.caption("부서별 긍정 응답 비중의 3개년 추이를 함께 비교합니다.")

    trend_fig = go.Figure()
    trend_rows = []
    for org_key, entry in auth.ORG_REGISTRY.items():
        org_name = entry["org"]
        if data.is_suppressed(count_df, "2026", org_name):
            continue
        trend = data.three_year_trend(obj_df, org_name, level="overall")
        trend_fig.add_trace(
            go.Scatter(
                x=trend["year"],
                y=trend["긍정"],
                mode="lines+markers",
                name=f"{entry['company']}·{org_name}",
                hovertemplate=f"%{{x}}년 {org_name} 긍정 %{{y}}%<extra></extra>",
            )
        )
        delta = round(
            float(trend.loc[trend["year"] == "2026", "긍정"].iloc[0])
            - float(trend.loc[trend["year"] == "2024", "긍정"].iloc[0]),
            1,
        )
        trend_rows.append(
            {"회사명": entry["company"], "부서명": org_name, "2024→2026 긍정 비중 변화": f"{delta:+.1f}%p"}
        )
    trend_fig.update_layout(
        height=340,
        margin=dict(t=20, b=10, l=10, r=10),
        xaxis=dict(type="category"),
        yaxis=dict(title="긍정 비중(%)"),
        font=PLOTLY_FONT,
        hoverlabel=dict(font_size=15),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(trend_fig, use_container_width=True, config={"displayModeBar": False})

    trend_df_display = pd.DataFrame(trend_rows).sort_values(
        "2024→2026 긍정 비중 변화", ascending=False
    )
    st.dataframe(trend_df_display, use_container_width=True, hide_index=True)

    st.divider()

    # ---- 3. 부서장별 접근 이력 ----
    section_title("4. 부서장별 접근 이력")
    st.caption("로그인 · 챗봇 대화 · 리포트 다운로드 이력을 한눈에 확인합니다 (로컬 접근 로그 기반).")
    st.dataframe(auth.manager_activity_table(), use_container_width=True, hide_index=True)

    st.divider()
    st.caption(
        "본 화면은 시연용 데모이며, 실제 운영 환경에서는 06_guardrails.md에 따라 "
        "HR 관리자 권한 검증과 접근 로그 감사가 함께 적용되어야 합니다."
    )


# ---------------------------------------------------------------------------
# 라우팅
# ---------------------------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False

if st.session_state.is_admin:
    render_admin()
elif st.session_state.authenticated:
    render_report()
elif st.session_state.show_admin_login:
    admin_login_page()
else:
    login_page()
