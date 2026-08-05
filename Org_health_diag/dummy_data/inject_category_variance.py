# -*- coding: utf-8 -*-
"""더미 데이터에 조직×중분류별 편차를 주입한다.

원본 더미데이터는 조직 하나가 "건강한/변화기/개선신호" 중 하나의 단일 성향으로
생성되어 있어, 같은 조직 안에서는 어느 중분류를 봐도 긍정 비중이 서로 비슷하다.
그 결과 부서 내부 비교 코멘트가 거의 항상 "대분류 내 다른 영역 평균 대비
비슷한 수준입니다"로 나와 시연 시 단조롭다는 피드백을 받았다.

이 스크립트는 조직·중분류 조합마다 고정된 목표 편차(%p)를 부여하고, 그 편차만큼
긍정 비중이 실제로 이동하도록 응답값 일부를 다른 라벨로 바꿔치기한다. 같은
조직·중분류의 편차는 2024~2026 전 연도에 동일하게 적용해 "그 팀의 특성"처럼
보이게 하고(3개년 추이 자체는 원본의 연도별 변화 폭을 그대로 유지), 조직마다
편차 배정을 다르게 섞어 조직마다 강점·약점 영역이 달라 보이도록 한다.

실행: python inject_category_variance.py
대상: organization_health_survey_2024_2026_extended.xlsx (제자리 수정)
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))
from catalog import QUESTION_TO_MID, MID_TO_MAJOR, MID_CATEGORY_ORDER  # noqa: E402

PATH = os.path.join(
    os.path.dirname(__file__), "organization_health_survey_2024_2026_extended.xlsx"
)
YEARS = ["2024", "2025", "2026"]

POS_STRONG = "전적으로 동의(공감)함"
POS_WEAK = "동의(공감)함"
NEUTRAL = "어느 쪽도 아님"
NEG_WEAK = "동의(공감)하지 않음"
NEG_STRONG = "전혀 동의(공감)하지 않음"
POSITIVE_LABELS = {POS_STRONG, POS_WEAK}

MAJORS = ["직원 몰입 수준", "회사 지원 수준"]
MID_BY_MAJOR = {
    major: [m for m in MID_CATEGORY_ORDER if MID_TO_MAJOR[m] == major] for major in MAJORS
}
SPREAD_BY_MAJOR = {"직원 몰입 수준": 13.0, "회사 지원 수준": 17.0}

RNG_SEED = 20260805


def bucket(v: str) -> str:
    if v in POSITIVE_LABELS:
        return "pos"
    if v == NEUTRAL:
        return "neu"
    return "neg"


def build_org_deltas(orgs: list[tuple[str, str]]) -> dict[tuple[str, str, str], float]:
    """(회사, 조직, 중분류) -> 목표 편차(%p). 조직마다 순서를 다르게 섞어 배정한다."""
    deltas: dict[tuple[str, str, str], float] = {}
    for oi, (company, org) in enumerate(orgs):
        rng = np.random.default_rng(RNG_SEED + oi * 101)
        for major in MAJORS:
            mids = MID_BY_MAJOR[major]
            spread = SPREAD_BY_MAJOR[major]
            values = np.linspace(-spread, spread, len(mids))
            rng.shuffle(values)
            for mid, v in zip(mids, values):
                deltas[(company, org, mid)] = round(float(v), 1)
    return deltas


def apply_delta(vals: list[str], delta: float, rng: np.random.Generator) -> list[str]:
    n = len(vals)
    if n == 0 or abs(delta) < 0.05:
        return vals
    if delta > 0:
        pool = [i for i, v in enumerate(vals) if bucket(v) != "pos"]
        k = min(len(pool), round(n * delta / 100))
        if k <= 0:
            return vals
        chosen = rng.choice(pool, size=k, replace=False)
        for i in chosen:
            vals[i] = rng.choice([POS_WEAK, POS_STRONG], p=[0.65, 0.35])
    else:
        pool = [i for i, v in enumerate(vals) if bucket(v) == "pos"]
        k = min(len(pool), round(n * abs(delta) / 100))
        if k <= 0:
            return vals
        chosen = rng.choice(pool, size=k, replace=False)
        for i in chosen:
            vals[i] = rng.choice([NEUTRAL, NEG_WEAK, NEG_STRONG], p=[0.4, 0.4, 0.2])
    return vals


def apply_to_sheet(body: pd.DataFrame, deltas: dict, rng: np.random.Generator) -> pd.DataFrame:
    body = body.copy()
    orgs = body[["회사명", "조직명"]].drop_duplicates().itertuples(index=False, name=None)
    for company, org in orgs:
        row_mask = (body["회사명"] == company) & (body["조직명"] == org)
        row_idx = body.index[row_mask]
        for mid in MID_CATEGORY_ORDER:
            delta = deltas.get((company, org, mid))
            if not delta:
                continue
            cols = [q for q, m in QUESTION_TO_MID.items() if m == mid]
            cols = [c for c in cols if c in body.columns]
            if not cols:
                continue
            # 조직×중분류의 모든 문항·모든 응답자를 하나의 풀로 모아 편차를 적용한다
            flat_positions = [(r, c) for r in row_idx for c in cols]
            flat_values = [body.at[r, c] for r, c in flat_positions]
            new_values = apply_delta(flat_values, delta, rng)
            for (r, c), v in zip(flat_positions, new_values):
                body.at[r, c] = v
    return body


def main():
    with pd.ExcelFile(PATH) as xls:
        raw_sheets = {y: pd.read_excel(xls, sheet_name=y, header=None) for y in YEARS}

    sample_header = raw_sheets[YEARS[0]].iloc[0, :].tolist()
    body0 = raw_sheets[YEARS[0]].iloc[2:, :].copy()
    body0.columns = sample_header
    orgs = list(body0[["회사명", "조직명"]].drop_duplicates().itertuples(index=False, name=None))
    deltas = build_org_deltas(orgs)

    rng = np.random.default_rng(RNG_SEED)
    out_sheets = {}
    for year in YEARS:
        raw = raw_sheets[year]
        header_rows = raw.iloc[:2, :]
        body = raw.iloc[2:, :].copy()
        body.columns = raw.iloc[0, :].tolist()
        body = body.reset_index(drop=True)

        body = apply_to_sheet(body, deltas, rng)

        body.columns = header_rows.columns
        out_sheets[year] = pd.concat([header_rows, body], ignore_index=True)

    with pd.ExcelWriter(PATH, engine="openpyxl") as writer:
        for year in YEARS:
            out_sheets[year].to_excel(writer, sheet_name=year, header=False, index=False)

    print(f"편차 주입 완료: {PATH}")
    print(f"조직 {len(orgs)}개 × 중분류 {len(MID_CATEGORY_ORDER)}개 편차표:")
    for (company, org, mid), d in sorted(deltas.items()):
        print(f"  {company}/{org} · {mid}: {d:+.1f}%p")


if __name__ == "__main__":
    main()
