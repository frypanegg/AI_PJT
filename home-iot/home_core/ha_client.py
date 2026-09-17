"""Home Assistant 접근 계층.

REST 만 쓴다 (states 조회 + service 호출). 테스트는 FakeHaClient 로 한다.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx


class HaClient(Protocol):
    async def states(self) -> dict[str, dict[str, Any]]: ...

    async def call_service(self, domain: str, service: str, data: dict[str, Any]) -> None: ...


class HttpHaClient:
    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    async def states(self) -> dict[str, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            r = await c.get(f"{self._base}/api/states", headers=self._headers)
            r.raise_for_status()
            return {row["entity_id"]: row for row in r.json()}

    async def call_service(self, domain: str, service: str, data: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            r = await c.post(
                f"{self._base}/api/services/{domain}/{service}",
                headers=self._headers,
                json=data,
            )
            r.raise_for_status()


class FakeHaClient:
    """테스트/오프라인 개발용. 서비스 호출을 그대로 기록한다."""

    def __init__(self, states: dict[str, dict[str, Any]] | None = None) -> None:
        self._states = states or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def states(self) -> dict[str, dict[str, Any]]:
        return dict(self._states)

    async def call_service(self, domain: str, service: str, data: dict[str, Any]) -> None:
        self.calls.append((domain, service, data))
        entity = data.get("entity_id")
        if not entity:
            return
        row = self._states.setdefault(entity, {"entity_id": entity, "state": "off", "attributes": {}})
        if service == "turn_on":
            row["state"] = "on"
        elif service == "turn_off":
            row["state"] = "off"
        elif service == "toggle":
            row["state"] = "off" if row["state"] == "on" else "on"
        for key in ("brightness", "color_temp_kelvin", "temperature"):
            if key in data:
                row.setdefault("attributes", {})[key] = data[key]

    def set_state(self, entity_id: str, state: Any, **attributes: Any) -> None:
        self._states[entity_id] = {
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes,
        }
