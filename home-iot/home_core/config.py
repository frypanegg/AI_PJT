"""환경 설정."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ha_url: str
    ha_token: str
    registry_path: str | None
    db_path: str
    poll_interval: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ha_url=os.getenv("HA_URL", "http://homeassistant.local:8123"),
            ha_token=os.getenv("HA_TOKEN", ""),
            registry_path=os.getenv("REGISTRY_PATH") or None,
            # 도커 밖(맥에서 직접 실행)에서는 DB 경로를 로컬 파일로 덮어쓴다.
            db_path=os.getenv("DB_PATH", "home_core.db"),
            poll_interval=float(os.getenv("POLL_INTERVAL", "10")),
        )
