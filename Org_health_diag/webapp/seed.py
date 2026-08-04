# -*- coding: utf-8 -*-
"""엑셀 설문 데이터를 SQLite로 적재한다.

`python seed.py` 로 단독 실행하거나, 앱 기동 시 DB가 비어 있으면 자동 호출된다.
관리자 화면에서 새 엑셀을 업로드할 때도 이 모듈의 load_workbook을 재사용한다.
"""

import hashlib
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit_app"))

from catalog import (  # noqa: E402
    MID_TO_MAJOR,
    NEGATIVE_LABELS,
    NEUTRAL_LABELS,
    OPEN_TEXT_QUESTIONS,
    POSITIVE_LABELS,
    QUESTION_ORDER,
    QUESTION_TO_MID,
)

import db  # noqa: E402

YEARS = ["2024", "2025", "2026"]

DEFAULT_EXCEL = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dummy_data",
    "organization_health_survey_2024_2026_extended.xlsx",
)

# 기존 Streamlit 데모와 동일한 조직/계정 정보
ORG_SEED = [
    ("ss", "포스코", "철강사업실", "김민준", "850315", 80),
    ("tp", "포스코", "기술기획실", "이서연", "880622", 75),
    ("mi", "포스코", "경영혁신실", "박지훈", "911104", 68),
    ("sd", "포스코이앤씨", "철강설계실", "최유진", "870709", 80),
    ("pd", "포스코이앤씨", "플랜트설계실", "정승우", "900418", 75),
    ("cs", "포스코이앤씨", "건설전략실", "한소희", "930227", 68),
]

ADMIN_SEED = [("sum", "sum1420")]


def hash_password(raw: str) -> str:
    """데모용 해시. 실서비스에서는 bcrypt/argon2 + per-user salt를 써야 한다."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def bucket_of(value) -> str | None:
    if value in POSITIVE_LABELS:
        return "긍정"
    if value in NEUTRAL_LABELS:
        return "중립"
    if value in NEGATIVE_LABELS:
        return "부정"
    return None


def read_workbook(path: str):
    """엑셀에서 (responses, open_texts) 행 목록을 만든다."""
    resp_rows, text_rows = [], []

    with pd.ExcelFile(path) as xls:
        sheets = {y: pd.read_excel(xls, sheet_name=y, header=None) for y in YEARS}

    for year in YEARS:
        raw = sheets[year]
        header = [str(c) for c in raw.iloc[0, :].tolist()]
        body = raw.iloc[2:, :].copy()
        body.columns = header
        body = body.reset_index(drop=True)

        for idx, row in body.iterrows():
            company, org = row.get("회사명"), row.get("조직명")
            if pd.isna(company) or pd.isna(org):
                continue
            for qid in QUESTION_ORDER:
                if qid not in body.columns:
                    continue
                bucket = bucket_of(row[qid])
                if bucket is None:
                    continue
                mid = QUESTION_TO_MID[qid]
                resp_rows.append(
                    (year, str(company), str(org), int(idx), qid, mid, MID_TO_MAJOR[mid], bucket)
                )
            for qid in OPEN_TEXT_QUESTIONS:
                if qid not in body.columns:
                    continue
                text = row[qid]
                if pd.isna(text):
                    continue
                text_rows.append((year, str(company), str(org), qid, str(text)))

    return resp_rows, text_rows


def load_workbook(path: str, replace: bool = True) -> dict:
    """엑셀을 읽어 responses/open_texts 테이블을 채운다. 반환: 적재 통계."""
    resp_rows, text_rows = read_workbook(path)
    if not resp_rows:
        raise ValueError("적재할 응답 데이터가 없습니다.")

    with db.session() as conn:
        if replace:
            conn.execute("DELETE FROM responses")
            conn.execute("DELETE FROM open_texts")
        conn.executemany(
            "INSERT INTO responses (year, company, org, respondent, question_id, mid, major, bucket)"
            " VALUES (?,?,?,?,?,?,?,?)",
            resp_rows,
        )
        conn.executemany(
            "INSERT INTO open_texts (year, company, org, question_id, text) VALUES (?,?,?,?,?)",
            text_rows,
        )
        orgs = conn.execute(
            "SELECT COUNT(DISTINCT org) AS c FROM responses WHERE year='2026'"
        ).fetchone()["c"]

    return {"responses": len(resp_rows), "open_texts": len(text_rows), "orgs_2026": orgs}


def seed_orgs_and_admins():
    with db.session() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO orgs"
            " (org_key, company, org, manager_name, birth_code, target_headcount)"
            " VALUES (?,?,?,?,?,?)",
            ORG_SEED,
        )
        conn.executemany(
            "INSERT OR REPLACE INTO admins (admin_id, password_hash) VALUES (?,?)",
            [(a, hash_password(p)) for a, p in ADMIN_SEED],
        )


def bootstrap(excel_path: str | None = None) -> dict:
    """스키마 생성 + 조직/관리자 시드 + 엑셀 적재."""
    db.init_schema()
    seed_orgs_and_admins()
    stats = load_workbook(excel_path or DEFAULT_EXCEL)
    return stats


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL
    stats = bootstrap(path)
    print(f"DB: {db.DB_PATH}")
    print(f"적재 완료 - 응답 {stats['responses']}건, 주관식 {stats['open_texts']}건, "
          f"2026 조직 {stats['orgs_2026']}개")
