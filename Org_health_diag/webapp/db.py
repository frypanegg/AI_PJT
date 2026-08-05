# -*- coding: utf-8 -*-
"""SQLite 스키마 정의 및 접근 계층.

Streamlit 데모에서는 엑셀을 매 요청마다 읽었지만, 웹앱에서는 설문 응답을
SQLite에 적재해 두고 SQL로 집계한다.

테이블
- orgs        : 회사/부서/조직장/인증코드/대상인원 (기존 ORG_REGISTRY 대체)
- admins      : 관리자 계정
- responses   : 객관식 응답 (long format, 1행 = 1인 1문항)
- open_texts  : 주관식 응답
- access_logs   : 로그인·챗봇·다운로드 접근 이력
- chat_messages : 챗봇 대화 원문 (세션별) — 다운로드 리포트에서 요약해 사용

chat_messages를 세션 쿠키가 아니라 DB에 두는 이유: Starlette의 기본
SessionMiddleware는 세션 전체를 서명된 쿠키에 담아 브라우저에 보낸다. 쿠키는
브라우저가 4KB 근처에서 자르거나 거부하는데, AI 답변 몇 개만 쌓여도 그 한도를
넘어서 이후 갱신이 조용히 사라지는 문제가 있었다. 대화 내용만 DB로 옮기고
쿠키에는 짧은 세션 토큰만 남긴다.
"""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "org_health.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS orgs (
    org_key          TEXT PRIMARY KEY,
    company          TEXT NOT NULL,
    org              TEXT NOT NULL UNIQUE,
    manager_name     TEXT NOT NULL,
    birth_code       TEXT NOT NULL,
    target_headcount INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    admin_id      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS responses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    year        TEXT NOT NULL,
    company     TEXT NOT NULL,
    org         TEXT NOT NULL,
    respondent  INTEGER NOT NULL,   -- 시트 내 응답자 순번 (개인 식별 불가)
    question_id TEXT NOT NULL,
    mid         TEXT NOT NULL,
    major       TEXT NOT NULL,
    bucket      TEXT NOT NULL       -- 긍정 / 중립 / 부정
);
CREATE INDEX IF NOT EXISTS idx_resp_year_org ON responses(year, org);
CREATE INDEX IF NOT EXISTS idx_resp_year_org_q ON responses(year, org, question_id);
CREATE INDEX IF NOT EXISTS idx_resp_year_org_mid ON responses(year, org, mid);

CREATE TABLE IF NOT EXISTS open_texts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    year        TEXT NOT NULL,
    company     TEXT NOT NULL,
    org         TEXT NOT NULL,
    question_id TEXT NOT NULL,
    text        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_text_year_org ON open_texts(year, org, question_id);

CREATE TABLE IF NOT EXISTS access_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    org_key   TEXT,
    org       TEXT,
    event     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_log_org_event ON access_logs(org_key, event);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    org_key    TEXT,
    seq        INTEGER NOT NULL,
    role       TEXT NOT NULL,   -- user / assistant
    text       TEXT NOT NULL,
    ts         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, seq);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema():
    with session() as conn:
        conn.executescript(SCHEMA)


def db_exists() -> bool:
    if not os.path.exists(DB_PATH):
        return False
    with session() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='responses'"
        ).fetchone()
        if not row:
            return False
        count = conn.execute("SELECT COUNT(*) AS c FROM responses").fetchone()["c"]
    return count > 0
