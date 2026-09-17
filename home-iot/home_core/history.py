"""상태 이력 저장소.

값은 타입별 컬럼으로 나눠 담는다 (불리언/숫자/문자열). 한 컬럼에 섞어
넣으면 나중에 집계할 때 매번 캐스팅해야 하고, "0"과 false 가 구분되지 않는다.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ValueType

SCHEMA = """
CREATE TABLE IF NOT EXISTS state_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,
    device_id   TEXT    NOT NULL,
    capability  TEXT    NOT NULL,
    value_bool  INTEGER,
    value_num   REAL,
    value_text  TEXT
);
CREATE INDEX IF NOT EXISTS ix_history_device_ts ON state_history (device_id, ts);
"""


class History:
    def __init__(self, path: str | Path = "home_core.db") -> None:
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def record(self, device_id: str, capability: str, value: Any, value_type: ValueType) -> None:
        if value is None:
            return
        row: dict[str, Any] = {"value_bool": None, "value_num": None, "value_text": None}
        if value_type is ValueType.BOOL:
            row["value_bool"] = int(bool(value))
        elif value_type is ValueType.NUMBER:
            row["value_num"] = float(value)
        else:
            row["value_text"] = str(value)
        self._conn.execute(
            "INSERT INTO state_history (ts, device_id, capability, value_bool, value_num, value_text)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                device_id,
                capability,
                row["value_bool"],
                row["value_num"],
                row["value_text"],
            ),
        )
        self._conn.commit()

    def recent(self, device_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        sql = "SELECT * FROM state_history"
        args: tuple[Any, ...] = ()
        if device_id:
            sql += " WHERE device_id = ?"
            args = (device_id,)
        sql += " ORDER BY id DESC LIMIT ?"
        args += (limit,)
        rows = self._conn.execute(sql, args).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()
