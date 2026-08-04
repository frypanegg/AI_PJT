# -*- coding: utf-8 -*-
"""SQLite 기반 집계·해석 계층 (Streamlit 데모의 data.py + insights.py 역할).

부서 간 비교를 지양하라는 지침에 따라, 모든 해석은 '우리 부서 내부의 다른 항목
평균'과 비교한다. 전사 평균은 관리자 화면에서만 사용한다.

"현재 연도"를 코드에 고정하지 않고 DB에 실제 적재된 연도 중 가장 최신 값을 매번
조회해서 쓴다. 내년에 2027 시트가 추가된 4개년 워크북이 업로드되면, 이 모듈은
아무 수정 없이 2027년을 리포트 기준 연도로, 2024~2027을 추이 구간으로 사용한다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))

from catalog import (  # noqa: E402
    MID_CATEGORY_ORDER,
    MID_INTERPRETATION,
    MID_TO_MAJOR,
    OPEN_TEXT_QUESTIONS,
    QUESTION_ORDER,
    QUESTION_TEXT,
    QUESTION_TO_MID,
)
from insights_questions import SAMPLE_QUESTIONS  # noqa: E402

import db  # noqa: E402

BUCKETS = ["긍정", "중립", "부정"]
MIN_RESPONDENTS = 10  # 소수 응답 조직 보호 기준
DIFF_THRESHOLD = 3.0  # 비교 대상과 이 값(%p) 미만 차이면 "비슷한 수준"


# ---------------------------------------------------------------------------
# 연도
# ---------------------------------------------------------------------------

def available_years() -> list[str]:
    """DB에 실제로 적재된 연도를 오름차순으로 반환한다 (예: ["2024","2025","2026","2027"])."""
    with db.session() as conn:
        rows = conn.execute("SELECT DISTINCT year FROM responses ORDER BY year").fetchall()
    return [r["year"] for r in rows]


def latest_year() -> str:
    """리포트의 기준 연도 — 적재된 연도 중 가장 최신 값."""
    years = available_years()
    if not years:
        raise RuntimeError("적재된 응답 데이터가 없습니다.")
    return years[-1]


# ---------------------------------------------------------------------------
# 조직 · 계정
# ---------------------------------------------------------------------------

def list_orgs() -> list[dict]:
    with db.session() as conn:
        rows = conn.execute("SELECT * FROM orgs ORDER BY company, org").fetchall()
    return [dict(r) for r in rows]


def get_org(org_key: str) -> dict | None:
    with db.session() as conn:
        row = conn.execute("SELECT * FROM orgs WHERE org_key=?", (org_key,)).fetchone()
    return dict(row) if row else None


def verify_org_login(org_key: str, birth_code: str) -> bool:
    org = get_org(org_key)
    return bool(org and birth_code.strip() == org["birth_code"])


def verify_admin(admin_id: str, password: str) -> bool:
    from seed import hash_password

    with db.session() as conn:
        row = conn.execute(
            "SELECT password_hash FROM admins WHERE admin_id=?", (admin_id.strip(),)
        ).fetchone()
    return bool(row and row["password_hash"] == hash_password(password))


# ---------------------------------------------------------------------------
# 접근 로그
# ---------------------------------------------------------------------------

def log_access(org_key: str | None, org: str | None, event: str):
    import datetime as dt

    with db.session() as conn:
        conn.execute(
            "INSERT INTO access_logs (ts, org_key, org, event) VALUES (?,?,?,?)",
            (dt.datetime.now().isoformat(timespec="seconds"), org_key, org, event),
        )


def manager_activity() -> list[dict]:
    """부서장별 로그인·챗봇·다운로드 이력 요약."""
    with db.session() as conn:
        agg = conn.execute(
            "SELECT org_key, event, COUNT(*) AS cnt, MAX(ts) AS last_ts"
            " FROM access_logs GROUP BY org_key, event"
        ).fetchall()
    stat = {(r["org_key"], r["event"]): (r["cnt"], r["last_ts"]) for r in agg}

    def fmt(org_key: str, event: str) -> str:
        hit = stat.get((org_key, event))
        if not hit:
            return "이력 없음"
        cnt, last = hit
        return f"{cnt}회 (최근 {last[:16].replace('T', ' ')})"

    return [
        {
            "회사명": o["company"],
            "부서명": o["org"],
            "조직장명": o["manager_name"],
            "로그인 이력": fmt(o["org_key"], "login_success"),
            "챗봇 채팅 이력": fmt(o["org_key"], "chat_message"),
            "보고서 다운로드 이력": fmt(o["org_key"], "report_download"),
        }
        for o in list_orgs()
    ]


# ---------------------------------------------------------------------------
# 집계
# ---------------------------------------------------------------------------

def _ratio(counts: dict) -> dict:
    n = sum(counts.get(b, 0) for b in BUCKETS)
    if n == 0:
        return {"긍정": 0.0, "중립": 0.0, "부정": 0.0, "n": 0}
    return {
        **{b: round(counts.get(b, 0) / n * 100, 1) for b in BUCKETS},
        "n": n,
    }


def _bucket_counts(conn, where: str, params: tuple) -> dict:
    rows = conn.execute(
        f"SELECT bucket, COUNT(*) AS c FROM responses WHERE {where} GROUP BY bucket", params
    ).fetchall()
    return {r["bucket"]: r["c"] for r in rows}


def respondent_count(year: str, org: str) -> int:
    with db.session() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT respondent) AS c FROM responses WHERE year=? AND org=?",
            (year, org),
        ).fetchone()
    return row["c"] or 0


def is_suppressed(year: str, org: str) -> bool:
    return respondent_count(year, org) < MIN_RESPONDENTS


def overall_ratio(year: str, org: str) -> dict:
    with db.session() as conn:
        return _ratio(_bucket_counts(conn, "year=? AND org=?", (year, org)))


def mid_ratios(year: str, org: str) -> list[dict]:
    """중분류별 비중 (MID_CATEGORY_ORDER 순서)."""
    with db.session() as conn:
        rows = conn.execute(
            "SELECT mid, bucket, COUNT(*) AS c FROM responses"
            " WHERE year=? AND org=? GROUP BY mid, bucket",
            (year, org),
        ).fetchall()
    per_mid: dict[str, dict] = {}
    for r in rows:
        per_mid.setdefault(r["mid"], {})[r["bucket"]] = r["c"]

    out = []
    for mid in MID_CATEGORY_ORDER:
        if mid not in per_mid:
            continue
        out.append({"중분류": mid, "대분류": MID_TO_MAJOR[mid], **_ratio(per_mid[mid])})
    return out


def question_ratios(year: str, org: str) -> list[dict]:
    with db.session() as conn:
        rows = conn.execute(
            "SELECT question_id, bucket, COUNT(*) AS c FROM responses"
            " WHERE year=? AND org=? GROUP BY question_id, bucket",
            (year, org),
        ).fetchall()
    per_q: dict[str, dict] = {}
    for r in rows:
        per_q.setdefault(r["question_id"], {})[r["bucket"]] = r["c"]

    out = []
    for qid in QUESTION_ORDER:
        if qid not in per_q:
            continue
        mid = QUESTION_TO_MID[qid]
        out.append(
            {
                "문항ID": qid,
                "문항": QUESTION_TEXT[qid],
                "중분류": mid,
                "대분류": MID_TO_MAJOR[mid],
                **_ratio(per_q[qid]),
            }
        )
    return out


def top_mids(year: str, org: str, by: str = "긍정", k: int = 3) -> list[dict]:
    return sorted(mid_ratios(year, org), key=lambda r: r[by], reverse=True)[:k]


def top_open_texts(year: str, org: str, qid: str, k: int = 3) -> list[str]:
    with db.session() as conn:
        rows = conn.execute(
            "SELECT text, COUNT(*) AS c FROM open_texts"
            " WHERE year=? AND org=? AND question_id=?"
            " GROUP BY text ORDER BY c DESC LIMIT ?",
            (year, org, qid, k),
        ).fetchall()
    return [r["text"] for r in rows]


def multi_year_trend(org: str, mid: str | None = None) -> list[dict]:
    """조직(선택적으로 중분류)의 연도별 비중 추이. 연도 개수는 DB에 적재된 만큼 그대로 따라간다."""
    where = "org=?" + (" AND mid=?" if mid else "")
    out = []
    with db.session() as conn:
        for year in available_years():
            params = (org, mid) if mid else (org,)
            counts = _bucket_counts(conn, f"year=? AND {where}", (year, *params))
            out.append({"year": year, **_ratio(counts)})
    return out


def company_wide_ratio(year: str) -> dict:
    """전 조직 통합 평균 — 관리자 화면 전용."""
    with db.session() as conn:
        return _ratio(_bucket_counts(conn, "year=?", (year,)))


# ---------------------------------------------------------------------------
# 부서 내부 비교 해석
# ---------------------------------------------------------------------------

def peer_avg_for_mid(mids: list[dict], mid: str, major: str) -> float | None:
    peers = [m["긍정"] for m in mids if m["대분류"] == major and m["중분류"] != mid]
    return round(sum(peers) / len(peers), 1) if peers else None


def peer_avg_for_question(questions: list[dict], qid: str, mid: str):
    peers = [q["긍정"] for q in questions if q["중분류"] == mid and q["문항ID"] != qid]
    if peers:
        return round(sum(peers) / len(peers), 1), f"중분류({mid}) 내 다른 문항 평균 대비"

    row = next((q for q in questions if q["문항ID"] == qid), None)
    if not row:
        return None, None
    major = row["대분류"]
    peers = [q["긍정"] for q in questions if q["대분류"] == major and q["문항ID"] != qid]
    if not peers:
        return None, None
    return round(sum(peers) / len(peers), 1), f"대분류({major}) 내 다른 문항 평균 대비"


def peer_commentary(mid: str, ratio: dict, peer_avg: float | None, peer_label: str) -> str:
    card = MID_INTERPRETATION[mid]
    if peer_avg is None:
        dominant = max(BUCKETS, key=lambda b: ratio.get(b, 0))
        return (
            f"긍정 {ratio['긍정']}% · 중립 {ratio['중립']}% · 부정 {ratio['부정']}%로 "
            f"나타났습니다. {card[dominant]}"
        )
    diff = round(ratio["긍정"] - peer_avg, 1)
    if diff >= DIFF_THRESHOLD:
        return f"{peer_label} 긍정 응답 비중이 {diff:+.1f}%p 높은 편입니다. {card['긍정']}"
    if diff <= -DIFF_THRESHOLD:
        return (
            f"{peer_label} 긍정 응답 비중이 {diff:.1f}%p 낮아 상대적으로 관찰이 필요합니다. "
            f"{card['부정']}"
        )
    return f"{peer_label} 비슷한 수준입니다 ({diff:+.1f}%p). {card['중립']}"


def executive_summary(org: str, year: str, overall: dict, top_pos: list, top_neg: list) -> str:
    pos = ", ".join(m["중분류"] for m in top_pos)
    neg = ", ".join(m["중분류"] for m in top_neg)
    return (
        f"{org}은(는) {year}년 진단에서 전체 긍정 응답 비중 {overall['긍정']}%, "
        f"중립 {overall['중립']}%, 부정 {overall['부정']}%로 나타났습니다. "
        f"부서 내 14개 영역을 서로 비교했을 때 {pos} 영역의 긍정 응답 비중이 상대적으로 높아, "
        f"해당 영역의 구성원 경험이 비교적 안정적으로 형성되어 있을 가능성을 시사합니다. "
        f"반면 {neg} 영역은 부서 내 다른 영역에 비해 부정 응답 비중이 높아, "
        f"구성원이 관련 영역에서 불편을 경험했을 가능성이 있어 확인이 필요합니다. "
        f"본 해석은 다른 부서나 전사 평균과의 비교가 아니라 부서 내부 영역 간 비교이며, "
        f"특정 원인을 단정하지 않습니다."
    )


def trend_delta(org: str, mid: str) -> float:
    trend = multi_year_trend(org, mid)
    return round(trend[-1]["긍정"] - trend[0]["긍정"], 1)


def signals_and_topics(top_neg: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    signals, topics, questions = [], [], []
    for row in top_neg:
        mid = row["중분류"]
        card = MID_INTERPRETATION[mid]
        signals.append(f"**{mid}** (부정 {row['부정']}%) — {card['부정']}")
        topics.append(f"[{mid}] {card['방향']}")
        qs = SAMPLE_QUESTIONS.get(mid, [])
        if qs:
            questions.append({"mid": mid, "items": qs})
    return signals, topics, questions


def report_payload(org_key: str) -> dict:
    """리포트 화면에 필요한 모든 데이터를 한 번에 만든다."""
    org_row = get_org(org_key)
    org = org_row["org"]
    years = available_years()
    year = years[-1]

    if is_suppressed(year, org):
        return {"suppressed": True, "org": org, "company": org_row["company"]}

    overall = overall_ratio(year, org)
    mids = mid_ratios(year, org)
    questions = question_ratios(year, org)
    top_pos = top_mids(year, org, "긍정")
    top_neg = top_mids(year, org, "부정")
    respondents = respondent_count(year, org)

    for m in mids:
        m["peer_avg"] = peer_avg_for_mid(mids, m["중분류"], m["대분류"])
        m["comment"] = peer_commentary(
            m["중분류"], m, m["peer_avg"], f"대분류({m['대분류']}) 내 다른 영역 평균 대비"
        )
        m["direction"] = MID_INTERPRETATION[m["중분류"]]["방향"]
        m["definition"] = MID_INTERPRETATION[m["중분류"]]["정의"]

    for q in questions:
        avg, label = peer_avg_for_question(questions, q["문항ID"], q["중분류"])
        q["peer_avg"] = avg
        q["comment"] = peer_commentary(q["중분류"], q, avg, label or "")

    dept_avg = overall["긍정"]
    for card in (*top_pos, *top_neg):
        card["comment"] = peer_commentary(
            card["중분류"], card, dept_avg, "우리 부서 전체 평균 대비"
        )
        card["definition"] = MID_INTERPRETATION[card["중분류"]]["정의"]
        card["direction"] = MID_INTERPRETATION[card["중분류"]]["방향"]

    deltas = []
    for mid in MID_CATEGORY_ORDER:
        if not any(m["중분류"] == mid for m in mids):
            continue
        deltas.append({"중분류": mid, "delta": trend_delta(org, mid)})
    improved = sorted(deltas, key=lambda d: d["delta"], reverse=True)[:5]
    least = sorted(deltas, key=lambda d: d["delta"])[:5]

    signals, topics, sample_qs = signals_and_topics(top_neg)

    return {
        "suppressed": False,
        "org_key": org_key,
        "org": org,
        "company": org_row["company"],
        "respondents": respondents,
        "response_rate": round(respondents / org_row["target_headcount"] * 100, 1),
        "overall": overall,
        "mids": mids,
        "questions": questions,
        "top_pos": top_pos,
        "top_neg": top_neg,
        "open_texts": {
            qid: {"label": label, "items": top_open_texts(year, org, qid)}
            for qid, label in OPEN_TEXT_QUESTIONS.items()
        },
        "executive_summary": executive_summary(org, year, overall, top_pos, top_neg),
        "year": year,
        "years": years,
        "overall_trend": multi_year_trend(org),
        "mid_trends": {m["중분류"]: multi_year_trend(org, m["중분류"]) for m in mids},
        "improved": improved,
        "least_improved": least,
        "signals": signals,
        "topics": topics,
        "sample_questions": sample_qs,
        "mid_order": [m["중분류"] for m in mids],
    }


def admin_payload() -> dict:
    year = latest_year()
    company_wide = company_wide_ratio(year)
    rows = []
    for o in list_orgs():
        org = o["org"]
        if is_suppressed(year, org):
            continue
        ratio = overall_ratio(year, org)
        diff = round(ratio["긍정"] - company_wide["긍정"], 1)
        if diff >= DIFF_THRESHOLD:
            tag, tone = "우수 부서", "good"
        elif diff <= -DIFF_THRESHOLD:
            tag, tone = "관심 필요 부서", "watch"
        else:
            tag, tone = "평균 수준", "mid"
        rows.append(
            {
                "company": o["company"],
                "org": org,
                "respondents": respondent_count(year, org),
                **ratio,
                "diff": diff,
                "tag": tag,
                "tone": tone,
                "trend": multi_year_trend(org),
            }
        )
    rows.sort(key=lambda r: r["긍정"], reverse=True)
    return {
        "year": year,
        "years": available_years(),
        "company_wide": company_wide,
        "departments": rows,
        "activity": manager_activity(),
    }
