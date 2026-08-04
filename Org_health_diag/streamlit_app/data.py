# -*- coding: utf-8 -*-
"""더미 엑셀 데이터 로딩 및 집계 (Data Analyst Agent 역할의 코드화).

- 실제 채택 32개 객관식 문항만 사용
- 개인 원문 응답은 상위 화면에 그대로 노출하지 않고, 집계된 비중만 전달
- 소수 응답 조직은 auth.MIN_RESPONDENTS 미만이면 결과를 숨긴다
"""

import os

import pandas as pd
import streamlit as st

from catalog import (
    QUESTION_TO_MID,
    QUESTION_ORDER,
    QUESTION_TEXT,
    MID_TO_MAJOR,
    MID_CATEGORY_ORDER,
    OPEN_TEXT_QUESTIONS,
    POSITIVE_LABELS,
    NEUTRAL_LABELS,
    NEGATIVE_LABELS,
)
from auth import MIN_RESPONDENTS

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "dummy_data")

# 기본 제공 더미 데이터 (관리자가 파일을 올리지 않았을 때 사용)
DEFAULT_EXCEL_PATH = os.path.join(
    _DATA_DIR, "organization_health_survey_2024_2026_extended.xlsx"
)
# 관리자 화면에서 업로드한 Raw Data가 저장되는 위치
UPLOADED_EXCEL_PATH = os.path.join(_DATA_DIR, "uploaded_survey.xlsx")

YEARS = ["2024", "2025", "2026"]


def active_excel_path() -> str:
    """현재 사용 중인 엑셀 경로. 업로드본이 있으면 그것을 우선 사용한다."""
    return UPLOADED_EXCEL_PATH if os.path.exists(UPLOADED_EXCEL_PATH) else DEFAULT_EXCEL_PATH


def is_using_uploaded() -> bool:
    return os.path.exists(UPLOADED_EXCEL_PATH)


def validate_workbook(path: str):
    """업로드된 엑셀이 앱이 기대하는 구조인지 검사한다.

    반환: (ok, errors, warnings, stats)
    - errors 가 하나라도 있으면 해당 파일은 사용할 수 없다.
    - warnings 는 사용은 가능하지만 화면에 결과가 일부 비어 보일 수 있는 경우.
    """
    from auth import ORG_REGISTRY

    errors, warnings, stats = [], [], {}
    found_orgs, total_rows, found_qids = set(), 0, set()

    # Windows에서는 열린 파일 핸들이 남아 있으면 임시파일 교체(os.replace)가 실패하므로,
    # 검증에 필요한 값만 뽑고 반드시 핸들을 닫는다.
    try:
        with pd.ExcelFile(path) as xls:
            sheet_names = list(xls.sheet_names)
            missing_sheets = [y for y in YEARS if y not in sheet_names]
            if missing_sheets:
                errors.append(
                    f"연도 시트가 없습니다: {', '.join(missing_sheets)} "
                    f"(현재 시트: {', '.join(map(str, sheet_names))})"
                )
                return False, errors, warnings, stats

            for year in YEARS:
                raw = pd.read_excel(xls, sheet_name=year, header=None)
                if raw.shape[0] < 3:
                    errors.append(
                        f"'{year}' 시트에 응답 데이터 행이 없습니다. "
                        "(1행 문항ID, 2행 문항 원문, 3행부터 응답)"
                    )
                    continue

                header = [str(c) for c in raw.iloc[0, :].tolist()]
                for required in ("회사명", "조직명"):
                    if required not in header:
                        errors.append(f"'{year}' 시트 1행에 '{required}' 컬럼이 없습니다.")

                body = raw.iloc[2:, :].copy()
                body.columns = header
                total_rows += len(body)

                if "조직명" in header:
                    found_orgs.update(body["조직명"].dropna().astype(str).unique())
                found_qids.update(q for q in QUESTION_ORDER if q in header)
    except Exception as exc:  # 손상 파일 · 비엑셀 파일
        return False, [f"엑셀 파일을 읽을 수 없습니다: {exc}"], [], {}

    if errors:
        return False, errors, warnings, stats

    if not found_qids:
        errors.append(
            "32개 채택 문항(OS02, OM12 …) 중 일치하는 문항 컬럼을 찾지 못했습니다. "
            "1행에 문항ID가 있는지 확인해 주세요."
        )
        return False, errors, warnings, stats

    missing_qids = [q for q in QUESTION_ORDER if q not in found_qids]
    if missing_qids:
        warnings.append(
            f"32개 문항 중 {len(missing_qids)}개가 파일에 없습니다: {', '.join(missing_qids[:8])}"
            + (" …" if len(missing_qids) > 8 else "")
        )

    registry_orgs = {v["org"] for v in ORG_REGISTRY.values()}
    matched = found_orgs & registry_orgs
    if not matched:
        errors.append(
            "파일의 조직명이 시스템에 등록된 조직과 하나도 일치하지 않습니다. "
            f"등록 조직: {', '.join(sorted(registry_orgs))} / "
            f"파일 조직: {', '.join(sorted(found_orgs)) or '없음'}"
        )
        return False, errors, warnings, stats

    unmatched_registry = registry_orgs - found_orgs
    if unmatched_registry:
        warnings.append(
            f"등록된 조직 중 {len(unmatched_registry)}개가 파일에 없어 해당 부서는 결과가 표시되지 않습니다: "
            f"{', '.join(sorted(unmatched_registry))}"
        )

    stats = {
        "시트": ", ".join(YEARS),
        "총 응답 행": total_rows,
        "인식된 문항 수": f"{len(found_qids)} / {len(QUESTION_ORDER)}",
        "일치 조직 수": f"{len(matched)} / {len(registry_orgs)}",
    }
    return True, errors, warnings, stats


def save_uploaded_workbook(file_bytes: bytes):
    """업로드 파일을 검증한 뒤 저장한다. 반환: (ok, errors, warnings, stats)"""
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp_path = UPLOADED_EXCEL_PATH + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    ok, errors, warnings, stats = validate_workbook(tmp_path)
    if not ok:
        os.remove(tmp_path)  # 검증 실패 시 기존 데이터를 덮어쓰지 않는다
        return False, errors, warnings, stats

    os.replace(tmp_path, UPLOADED_EXCEL_PATH)
    clear_data_cache()
    return True, errors, warnings, stats


def reset_to_default_workbook() -> bool:
    """업로드본을 삭제하고 기본 더미 데이터로 되돌린다."""
    if os.path.exists(UPLOADED_EXCEL_PATH):
        os.remove(UPLOADED_EXCEL_PATH)
        clear_data_cache()
        return True
    return False


def _bucket(value: str) -> str:
    if value in POSITIVE_LABELS:
        return "긍정"
    if value in NEUTRAL_LABELS:
        return "중립"
    if value in NEGATIVE_LABELS:
        return "부정"
    return "무응답"


@st.cache_data(show_spinner=False)
def _load_from(path: str, _mtime: float):
    """엑셀을 읽어 (객관식 long-format df, 주관식 long-format df, 응답인원 df)를 반환.

    path/_mtime 을 캐시 키로 써서, 파일이 교체되면 자동으로 다시 읽는다.
    """
    obj_rows = []
    text_rows = []
    count_rows = []

    # with 문으로 핸들을 닫아, 이후 업로드 파일 교체가 Windows에서 막히지 않게 한다.
    with pd.ExcelFile(path) as xls:
        sheets = {year: pd.read_excel(xls, sheet_name=year, header=None) for year in YEARS}

    for year in YEARS:
        raw = sheets[year]
        header = raw.iloc[0, :].tolist()
        body = raw.iloc[2:, :].copy()
        body.columns = header
        body = body.reset_index(drop=True)

        count_rows.append(
            body.groupby(["회사명", "조직명"]).size().reset_index(name="respondents").assign(year=year)
        )

        for qid in QUESTION_ORDER:
            if qid not in body.columns:
                continue
            sub = body[["회사명", "조직명", qid]].rename(columns={qid: "response"})
            sub["year"] = year
            sub["question_id"] = qid
            sub["mid"] = QUESTION_TO_MID[qid]
            sub["major"] = MID_TO_MAJOR[QUESTION_TO_MID[qid]]
            sub["bucket"] = sub["response"].map(_bucket)
            obj_rows.append(sub)

        for qid in OPEN_TEXT_QUESTIONS:
            if qid not in body.columns:
                continue
            sub = body[["회사명", "조직명", qid]].rename(columns={qid: "text"})
            sub["year"] = year
            sub["question_id"] = qid
            sub = sub.dropna(subset=["text"])
            text_rows.append(sub)

    obj_df = pd.concat(obj_rows, ignore_index=True).rename(
        columns={"회사명": "company", "조직명": "org"}
    )
    obj_df = obj_df[obj_df["bucket"] != "무응답"]

    text_df = pd.concat(text_rows, ignore_index=True).rename(
        columns={"회사명": "company", "조직명": "org"}
    )

    count_df = pd.concat(count_rows, ignore_index=True).rename(
        columns={"회사명": "company", "조직명": "org"}
    )

    return obj_df, text_df, count_df


def load_data():
    """현재 활성 엑셀(업로드본 우선)을 읽어 집계 DataFrame 3종을 반환한다."""
    path = active_excel_path()
    return _load_from(path, os.path.getmtime(path))


def clear_data_cache():
    _load_from.clear()


def is_suppressed(count_df: pd.DataFrame, year: str, org: str) -> bool:
    n = respondent_count(count_df, year, org)
    return n < MIN_RESPONDENTS


def respondent_count(count_df: pd.DataFrame, year: str, org: str) -> int:
    row = count_df[(count_df["year"] == year) & (count_df["org"] == org)]
    if row.empty:
        return 0
    return int(row["respondents"].sum())


def ratio_from_subset(sub: pd.DataFrame) -> dict:
    n = len(sub)
    if n == 0:
        return {"긍정": 0.0, "중립": 0.0, "부정": 0.0, "n": 0}
    counts = sub["bucket"].value_counts()
    return {
        "긍정": round(counts.get("긍정", 0) / n * 100, 1),
        "중립": round(counts.get("중립", 0) / n * 100, 1),
        "부정": round(counts.get("부정", 0) / n * 100, 1),
        "n": n,
    }


def org_overall_ratio(obj_df: pd.DataFrame, year: str, org: str) -> dict:
    sub = obj_df[(obj_df["year"] == year) & (obj_df["org"] == org)]
    return ratio_from_subset(sub)


def mid_ratio(obj_df: pd.DataFrame, year: str, org: str, mid: str) -> dict:
    sub = obj_df[(obj_df["year"] == year) & (obj_df["org"] == org) & (obj_df["mid"] == mid)]
    return ratio_from_subset(sub)


def major_ratio(obj_df: pd.DataFrame, year: str, org: str, major: str) -> dict:
    sub = obj_df[(obj_df["year"] == year) & (obj_df["org"] == org) & (obj_df["major"] == major)]
    return ratio_from_subset(sub)


def question_ratio(obj_df: pd.DataFrame, year: str, org: str, qid: str) -> dict:
    sub = obj_df[(obj_df["year"] == year) & (obj_df["org"] == org) & (obj_df["question_id"] == qid)]
    return ratio_from_subset(sub)


def peer_avg_for_mid(mid_df: pd.DataFrame, mid: str, major: str) -> float | None:
    """같은 대분류 안의 '다른' 중분류들의 긍정 비중 평균 (자기 자신 제외).

    부서 간 비교를 지양하라는 지침에 따라, 전사 평균 대신 이 값을 비교 기준으로 쓴다.
    비교 대상이 없으면 None.
    """
    peers = mid_df[(mid_df["대분류"] == major) & (mid_df["중분류"] != mid)]
    if peers.empty:
        return None
    return round(float(peers["긍정"].mean()), 1)


def peer_avg_for_question(q_df: pd.DataFrame, qid: str, mid: str):
    """같은 중분류 안의 '다른' 문항들의 긍정 비중 평균 (자기 자신 제외).

    해당 중분류에 문항이 하나뿐이면 같은 대분류의 다른 문항들로 범위를 넓힌다.
    반환: (평균, 비교범위 라벨). 비교 대상이 아예 없으면 (None, None).
    """
    peers = q_df[(q_df["중분류"] == mid) & (q_df["문항ID"] != qid)]
    if not peers.empty:
        return round(float(peers["긍정"].mean()), 1), f"중분류({mid}) 내 다른 문항 평균 대비"

    row = q_df[q_df["문항ID"] == qid]
    if row.empty:
        return None, None
    major = row.iloc[0]["대분류"]
    peers = q_df[(q_df["대분류"] == major) & (q_df["문항ID"] != qid)]
    if peers.empty:
        return None, None
    return round(float(peers["긍정"].mean()), 1), f"대분류({major}) 내 다른 문항 평균 대비"


def company_wide_ratio(obj_df: pd.DataFrame, year: str, mid: str | None = None) -> dict:
    """전사(모든 조직 통합) 평균 비중 — 특정 조직 순위 비교가 아닌 참고용 기준선."""
    sub = obj_df[obj_df["year"] == year]
    if mid:
        sub = sub[sub["mid"] == mid]
    return ratio_from_subset(sub)


def company_wide_question_ratio(obj_df: pd.DataFrame, year: str, question_id: str) -> dict:
    """전사(모든 조직 통합) 문항 단위 평균 비중."""
    sub = obj_df[(obj_df["year"] == year) & (obj_df["question_id"] == question_id)]
    return ratio_from_subset(sub)


def all_mid_ratios(obj_df: pd.DataFrame, year: str, org: str) -> pd.DataFrame:
    rows = []
    for mid in MID_CATEGORY_ORDER:
        r = mid_ratio(obj_df, year, org, mid)
        rows.append({"중분류": mid, "대분류": MID_TO_MAJOR[mid], **r})
    return pd.DataFrame(rows)


def all_question_ratios(obj_df: pd.DataFrame, year: str, org: str) -> pd.DataFrame:
    rows = []
    for qid in QUESTION_ORDER:
        r = question_ratio(obj_df, year, org, qid)
        rows.append(
            {
                "문항ID": qid,
                "문항": QUESTION_TEXT[qid],
                "중분류": QUESTION_TO_MID[qid],
                "대분류": MID_TO_MAJOR[QUESTION_TO_MID[qid]],
                **r,
            }
        )
    return pd.DataFrame(rows)


def top3_mid(obj_df: pd.DataFrame, year: str, org: str, by: str = "긍정", ascending: bool = False):
    df = all_mid_ratios(obj_df, year, org)
    return df.sort_values(by, ascending=ascending).head(3).reset_index(drop=True)


def top3_open_text(text_df: pd.DataFrame, year: str, org: str, qid: str, k: int = 3):
    sub = text_df[(text_df["year"] == year) & (text_df["org"] == org) & (text_df["question_id"] == qid)]
    if sub.empty:
        return []
    counts = sub["text"].value_counts()
    return list(counts.head(k).index)


def three_year_trend(obj_df: pd.DataFrame, org: str, level: str = "mid", key: str | None = None):
    rows = []
    for year in YEARS:
        if level == "overall":
            r = org_overall_ratio(obj_df, year, org)
        elif level == "mid":
            r = mid_ratio(obj_df, year, org, key)
        elif level == "major":
            r = major_ratio(obj_df, year, org, key)
        else:
            raise ValueError(level)
        rows.append({"year": year, **r})
    return pd.DataFrame(rows)
