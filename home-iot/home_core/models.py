"""home-core 도메인 모델.

HA 엔티티는 기기 단위가 아니라 "능력 단위"로 흩어져 있다. 한 논리 기기가
여러 엔티티에 걸치는 경우(대표적으로 Aqara 씬 쌍: 켜기 씬 / 끄기 씬)를
표현하기 위해 SourceRef 에 members / command_targets 자리를 둔다.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ValueType(str, Enum):
    BOOL = "bool"
    NUMBER = "number"
    STRING = "string"
    TIMESTAMP = "timestamp"


class SourceRef(BaseModel):
    """능력 하나가 HA 쪽 어디에 붙어 있는지."""

    # 상태를 읽을 엔티티. 씬 방식처럼 읽을 곳이 없으면 None.
    entity_id: str | None = None
    # 한 논리 기기가 여러 엔티티로 흩어질 때의 역할 -> 엔티티 맵.
    # 예: {"on": "switch.geosil_kyeogi", "off": "switch.geosil_ggeugi"}
    members: dict[str, str] = Field(default_factory=dict)
    # 명령 값 -> 실행할 엔티티. 씬 쌍이 여기 쓰인다.
    # 예: {"true": "switch.geosil_kyeogi", "false": "switch.geosil_ggeugi"}
    command_targets: dict[str, str] = Field(default_factory=dict)
    # HA attribute 에서 값을 꺼내야 할 때 (예: light 의 brightness).
    attribute: str | None = None

    @property
    def readable(self) -> bool:
        """상태를 읽을 수 있는가.

        씬 스위치는 실행 후 항상 off 로 돌아간다. 그 off 를 "조명 꺼짐"으로
        내보내면 대시보드와 LLM이 틀린 정보를 믿게 되므로, 읽을 엔티티가
        없는 능력은 상태를 아예 보고하지 않는다.
        """
        return self.entity_id is not None

    @model_validator(mode="after")
    def _needs_a_target(self) -> "SourceRef":
        if self.entity_id is None and not self.command_targets and not self.members:
            raise ValueError("SourceRef 에 entity_id / command_targets / members 중 하나는 있어야 합니다")
        return self


class Capability(BaseModel):
    name: str
    type: ValueType
    source: SourceRef
    unit: str | None = None
    writable: bool = False
    # 도메인 단위 범위 (예: brightness 0~100).
    min: float | None = None
    max: float | None = None
    # HA 쪽 원본 범위 (예: light.brightness 0~255). 있으면 선형 변환한다.
    ha_min: float | None = None
    ha_max: float | None = None
    # 기본 서비스(turn_on/turn_off) 대신 쓸 HA 서비스. 예: "climate.set_temperature"
    service: str | None = None
    note: str | None = None

    @property
    def scaled(self) -> bool:
        return None not in (self.min, self.max, self.ha_min, self.ha_max)


class Device(BaseModel):
    id: str
    name: str
    room: str
    kind: str
    capabilities: dict[str, Capability] = Field(default_factory=dict)
    note: str | None = None

    def capability(self, name: str) -> Capability:
        try:
            return self.capabilities[name]
        except KeyError:
            raise KeyError(f"{self.id} 에 '{name}' 능력이 없습니다") from None


class Registry(BaseModel):
    devices: list[Device]

    @property
    def rooms(self) -> list[str]:
        return sorted({d.room for d in self.devices})

    def get(self, device_id: str) -> Device:
        for d in self.devices:
            if d.id == device_id:
                return d
        raise KeyError(f"알 수 없는 기기: {device_id}")

    @model_validator(mode="after")
    def _unique_ids(self) -> "Registry":
        seen: set[str] = set()
        for d in self.devices:
            if d.id in seen:
                raise ValueError(f"기기 id 중복: {d.id}")
            seen.add(d.id)
        return self


class StateValue(BaseModel):
    device_id: str
    capability: str
    value: Any
    type: ValueType
