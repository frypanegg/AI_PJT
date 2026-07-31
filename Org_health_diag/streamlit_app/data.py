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

EXCEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "dummy_data", "organization_health_survey_2024_2026_extended.xlsx"
)

YEARS = ["2024", "2025", "2026"]


def _bucket(value: str) -> str:
    if value in POSITIVE_LABELS:
        return "긍정"
    if value in NEUTRAL_LABELS:
        return "중립"
    if value in NEGATIVE_LABELS:
        return "부정"
    return "무응답"


@st.cache_data(show_spinner=False)
def load_data():
    """엑셀을 읽어 (객관식 long-format df, 주관식 long-format df, 응답인원 df)를 반환."""
    xls = pd.ExcelFile(EXCEL_PATH)

    obj_rows = []
    text_rows = []
    count_rows = []

    for year in YEARS:
        raw = pd.read_excel(xls, sheet_name=year, header=None)
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


def company_wide_ratio(obj_df: pd.DataFrame, year: str, mid: str | None = None) -> dict:
    """전사(모든 조직 통합) 평균 비중 — 특정 조직 순위 비교가 아닌 참고용 기준선."""
    sub = obj_df[obj_df["year"] == year]
    if mid:
        sub = sub[sub["mid"] == mid]
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
