"""HA 원본 <-> home-core 도메인 값 변환, 그리고 명령 라우팅."""

from __future__ import annotations

from typing import Any

from .ha_client import HaClient
from .models import Capability, Device, ValueType

UNKNOWN = {"unknown", "unavailable", "none", "", None}
TRUTHY = {"on", "true", "open", "home", "playing", "cleaning"}
FALSY = {"off", "false", "closed", "not_home", "idle", "standby", "docked"}


class CommandError(RuntimeError):
    pass


def _scale(value: float, src: tuple[float, float], dst: tuple[float, float]) -> float:
    (s0, s1), (d0, d1) = src, dst
    if s1 == s0:
        return d0
    ratio = (value - s0) / (s1 - s0)
    return d0 + ratio * (d1 - d0)


def to_domain(cap: Capability, raw: dict[str, Any] | None) -> Any | None:
    """HA state row -> 도메인 값. 값이 없거나 읽을 수 없으면 None."""
    if raw is None or not cap.source.readable:
        return None

    if cap.source.attribute:
        value = (raw.get("attributes") or {}).get(cap.source.attribute)
    else:
        value = raw.get("state")

    if isinstance(value, str) and value.lower() in UNKNOWN:
        return None
    if value is None:
        return None

    if cap.type is ValueType.BOOL:
        if isinstance(value, bool):
            return value
        text = str(value).lower()
        if text in TRUTHY:
            return True
        if text in FALSY:
            return False
        return None

    if cap.type is ValueType.NUMBER:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if cap.scaled:
            number = _scale(number, (cap.ha_min, cap.ha_max), (cap.min, cap.max))
        return round(number, 2)

    # STRING / TIMESTAMP 는 원본 문자열 그대로 내보낸다.
    # (LG 가전의 "남은 시간"은 실제로는 ISO 종료 *시각*이다 — devices.yaml 주석 참고)
    return str(value)


def to_ha_number(cap: Capability, value: float) -> float:
    if cap.min is not None and cap.max is not None:
        if not (cap.min <= value <= cap.max):
            raise CommandError(f"{cap.name} 값은 {cap.min}~{cap.max} 범위여야 합니다 (받은 값: {value})")
    if cap.scaled:
        return round(_scale(value, (cap.min, cap.max), (cap.ha_min, cap.ha_max)))
    return value


def resolve_command_entity(cap: Capability, value: Any) -> str:
    """명령 값에 대응하는 실행 대상 엔티티.

    씬 쌍(켜기/끄기)이 여기서 풀린다. 토글 씬과 달리 명령이 멱등해진다:
    on_off=false 를 몇 번 실행해도 "끄기 씬"만 불린다.
    """
    targets = cap.source.command_targets
    if targets:
        key = str(value).lower() if isinstance(value, bool) else str(value)
        if key not in targets:
            raise CommandError(f"{cap.name} 에 '{key}' 에 대응하는 실행 대상이 없습니다")
        return targets[key]
    if cap.source.entity_id:
        return cap.source.entity_id
    raise CommandError(f"{cap.name} 은(는) 실행 대상이 없습니다")


def _service_for(cap: Capability, domain: str, default: str) -> tuple[str, str]:
    if cap.service:
        svc_domain, _, service = cap.service.partition(".")
        return svc_domain, service
    return domain, default


async def send_command(client: HaClient, device: Device, cap_name: str, value: Any) -> str:
    """기기에 명령을 보내고, 실제로 호출한 엔티티 id 를 돌려준다."""
    cap = device.capability(cap_name)
    if not cap.writable:
        raise CommandError(f"{device.id}.{cap_name} 은(는) 제어할 수 없습니다")

    entity_id = resolve_command_entity(cap, value)
    domain = entity_id.split(".", 1)[0]

    if cap.type is ValueType.BOOL:
        if not isinstance(value, bool):
            raise CommandError(f"{cap_name} 에는 true/false 가 필요합니다")
        if cap.source.command_targets:
            # 씬 쌍: 어느 쪽이든 해당 씬 스위치를 켜면 씬이 실행된다.
            await client.call_service(domain, "turn_on", {"entity_id": entity_id})
        else:
            await client.call_service(domain, "turn_on" if value else "turn_off", {"entity_id": entity_id})
        return entity_id

    if cap.type is ValueType.NUMBER:
        ha_value = to_ha_number(cap, float(value))
        attribute = cap.source.attribute or cap_name
        svc_domain, service = _service_for(cap, domain, "turn_on")
        await client.call_service(svc_domain, service, {"entity_id": entity_id, attribute: ha_value})
        return entity_id

    svc_domain, service = _service_for(cap, domain, "turn_on")
    await client.call_service(svc_domain, service, {"entity_id": entity_id, cap_name: value})
    return entity_id
