# -*- coding: utf-8 -*-
"""원본 더미데이터(3개 조직)를 포스코/포스코이앤씨 각 3개 부서(총 6개)로 확장한다.

원본에 이미 있는 3가지 조직 유형(건강한 조직 / 변화기 조직 / 개선신호 조직)을
두 회사에 각각 배정한다. 각 회사마다 원본에 없는 1개 유형은 다른 회사의 응답
패턴을 약한 jitter(±1단계, 15% 확률)를 적용해 복제 생성한다 — 완전히 동일한
수치가 두 조직에 중복 노출되는 것을 피하기 위함이며, 실제 원인 데이터가 아닌
시연용 합성 데이터임을 명시한다.

매핑:
- 포스코   · 철강사업실   = 건강한 조직 (원본 People Growth 본부, 그대로 이름만 변경)
- 포스코   · 기술기획실   = 변화기 조직 (원본 Product Strategy 실, 그대로 이름만 변경)
- 포스코   · 경영혁신실   = 개선신호 조직 (원본 Operations Innovation 센터의 jitter 복제본)
- 포스코이앤씨 · 건설전략실 = 개선신호 조직 (원본 Operations Innovation 센터, 그대로 이름만 변경)
- 포스코이앤씨 · 철강설계실 = 건강한 조직 (원본 People Growth 본부의 jitter 복제본)
- 포스코이앤씨 · 플랜트설계실 = 변화기 조직 (원본 Product Strategy 실의 jitter 복제본)
"""

import os

import numpy as np
import pandas as pd

SRC_PATH = os.path.join(os.path.dirname(__file__), "organization_health_survey_2024_2026.xlsx")
DST_PATH = os.path.join(os.path.dirname(__file__), "organization_health_survey_2024_2026_extended.xlsx")

YEARS = ["2024", "2025", "2026"]

SCALE = [
    "전혀 동의(공감)하지 않음",
    "동의(공감)하지 않음",
    "어느 쪽도 아님",
    "동의(공감)함",
    "전적으로 동의(공감)함",
]
SCALE_INDEX = {v: i for i, v in enumerate(SCALE)}

JITTER_PROB = 0.15
RNG = np.random.default_rng(42)

# (원본 회사명, 원본 조직명) -> [(새 회사명, 새 조직명, 법인코드, jitter 여부), ...]
SOURCE_TO_TARGETS = {
    ("A회사", "People Growth 본부"): [
        ("포스코", "철강사업실", 1001, False),
        ("포스코이앤씨", "철강설계실", 2001, True),
    ],
    ("A회사", "Product Strategy 실"): [
        ("포스코", "기술기획실", 1001, False),
        ("포스코이앤씨", "플랜트설계실", 2001, True),
    ],
    ("B회사", "Operations Innovation 센터"): [
        ("포스코이앤씨", "건설전략실", 2001, False),
        ("포스코", "경영혁신실", 1001, True),
    ],
}

OBJ_COLS = [
    "OS02", "OM12", "OM11", "OM01", "CQ01", "SD04", "SD05", "CQ02",
    "SP45", "ER01", "RC01", "CP11", "CQ03", "SP12", "AV09", "JS05",
    "WE08", "JS02", "WE12", "DM02", "CQ04", "TW02", "TW04", "ST01",
    "TR01", "RE01", "PE09", "DI17", "DI12", "ER03", "DI32", "DI20",
]


def jitter_block(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in OBJ_COLS:
        values = df[col].tolist()
        new_values = []
        for v in values:
            idx = SCALE_INDEX.get(v)
            if idx is None or RNG.random() >= JITTER_PROB:
                new_values.append(v)
                continue
            step = RNG.choice([-1, 1])
            new_idx = min(max(idx + step, 0), len(SCALE) - 1)
            new_values.append(SCALE[new_idx])
        df[col] = new_values
    return df


def build_sheet(raw: pd.DataFrame) -> pd.DataFrame:
    header_rows = raw.iloc[:2, :]
    body = raw.iloc[2:, :].copy()
    body.columns = raw.iloc[0, :].tolist()
    body = body.reset_index(drop=True)

    blocks = []
    for (src_company, src_org), targets in SOURCE_TO_TARGETS.items():
        src_block = body[(body["회사명"] == src_company) & (body["조직명"] == src_org)]
        for new_company, new_org, corp_code, do_jitter in targets:
            block = jitter_block(src_block) if do_jitter else src_block.copy()
            block["회사명"] = new_company
            block["조직명"] = new_org
            block["법인코드"] = corp_code
            blocks.append(block)

    new_body = pd.concat(blocks, ignore_index=True)
    new_body.columns = header_rows.columns
    combined = pd.concat([header_rows, new_body], ignore_index=True)
    return combined


def main():
    xls = pd.ExcelFile(SRC_PATH)
    with pd.ExcelWriter(DST_PATH, engine="openpyxl") as writer:
        for year in YEARS:
            raw = pd.read_excel(xls, sheet_name=year, header=None)
            out = build_sheet(raw)
            out.to_excel(writer, sheet_name=year, header=False, index=False)
    print(f"written: {DST_PATH}")


if __name__ == "__main__":
    main()
