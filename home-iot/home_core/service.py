"""레지스트리 + HA 어댑터 + 이력 + 이벤트를 묶는 서비스 계층."""

from __future__ import annotations

from typing import Any

from . import adapter
from .events import EventBroker
from .ha_client import HaClient
from .history import History
from .models import Registry


class HomeCore:
    def __init__(self, registry: Registry, client: HaClient, history: History, broker: EventBroker | None = None) -> None:
        self.registry = registry
        self.client = client
        self.history = history
        self.broker = broker or EventBroker()
        self._state: dict[str, dict[str, Any]] = {}

    # --- 조회 ---------------------------------------------------------
    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {k: dict(v) for k, v in self._state.items()}

    def device_state(self, device_id: str) -> dict[str, Any]:
        self.registry.get(device_id)  # 존재 검증
        return dict(self._state.get(device_id, {}))

    async def refresh(self) -> dict[str, dict[str, Any]]:
        """HA 전체 상태를 읽어 도메인 값으로 바꾸고, 변한 것만 기록·발행한다."""
        raw_states = await self.client.states()
        for device in self.registry.devices:
            current = self._state.setdefault(device.id, {})
            for cap_name, cap in device.capabilities.items():
                if not cap.source.readable:
                    # 읽을 수 없는 능력(씬 쌍 등)은 값을 만들어내지 않는다.
                    continue
                value = adapter.to_domain(cap, raw_states.get(cap.source.entity_id))
                if value is None:
                    continue
                if current.get(cap_name) == value:
                    continue
                current[cap_name] = value
                self.history.record(device.id, cap_name, value, cap.type)
                self.broker.publish(
                    {"type": "state", "device_id": device.id, "capability": cap_name, "value": value}
                )
        return self.snapshot()

    # --- 제어 ---------------------------------------------------------
    async def command(self, device_id: str, capability: str, value: Any) -> dict[str, Any]:
        device = self.registry.get(device_id)
        entity_id = await adapter.send_command(self.client, device, capability, value)
        event = {
            "type": "command",
            "device_id": device_id,
            "capability": capability,
            "value": value,
            "entity_id": entity_id,
        }
        self.broker.publish(event)
        return event
