# -*- coding: utf-8 -*-
"""데모용 인증 및 접근 로그.

실제 운영 환경에서는 사내 SSO + 권한 매핑 테이블을 사용해야 한다 (06_guardrails.md).
이 데모에서는 조직당 6자리 생년월일 코드를 부서장 인증 수단으로 대체 사용한다.
데모 인증코드는 화면에 노출하지 않고, 시연 진행자가 DEMO_GUIDE.md를 통해
개인별 안내 메일에 포함하는 것으로 가정한다.
"""

import csv
import datetime as dt
import os

# key(URL 파라미터용 짧은 코드) -> 조직 정보 + 데모 인증코드(생년월일 6자리)
ORG_REGISTRY = {
    "ss": {
        "company": "포스코",
        "org": "철강사업실",
        "birth_code": "850315",
        "target_headcount": 80,
    },
    "tp": {
        "company": "포스코",
        "org": "기술기획실",
        "birth_code": "880622",
        "target_headcount": 75,
    },
    "mi": {
        "company": "포스코",
        "org": "경영혁신실",
        "birth_code": "911104",
        "target_headcount": 68,
    },
    "sd": {
        "company": "포스코이앤씨",
        "org": "철강설계실",
        "birth_code": "870709",
        "target_headcount": 80,
    },
    "pd": {
        "company": "포스코이앤씨",
        "org": "플랜트설계실",
        "birth_code": "900418",
        "target_headcount": 75,
    },
    "cs": {
        "company": "포스코이앤씨",
        "org": "건설전략실",
        "birth_code": "930227",
        "target_headcount": 68,
    },
}

MIN_RESPONDENTS = 10  # 소수 응답 조직 결과 숨김 기준 (06_guardrails.md)

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "access_log.csv")


def org_options():
    """LOV용 (key, 표시라벨) 목록."""
    return [(k, f"{v['company']} · {v['org']}") for k, v in ORG_REGISTRY.items()]


def verify(org_key: str, birth_input: str) -> bool:
    entry = ORG_REGISTRY.get(org_key)
    if not entry:
        return False
    return birth_input.strip() == entry["birth_code"]


def log_access(org_key: str, event: str):
    """접근/다운로드 이력을 로컬 CSV에 남긴다 (06_guardrails.md 접근 로그 원칙 데모)."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    is_new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "org_key", "org", "event"])
        org_name = ORG_REGISTRY.get(org_key, {}).get("org", org_key)
        writer.writerow([dt.datetime.now().isoformat(timespec="seconds"), org_key, org_name, event])
