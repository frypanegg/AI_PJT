import pytest

from home_core import adapter
from home_core.adapter import CommandError


@pytest.mark.asyncio
async def test_on_off_true_calls_on_scene(core, client):
    event = await core.command("living_room_light", "on_off", True)
    assert event["entity_id"] == "switch.geosil_kyeogi"
    assert client.calls[-1][:2] == ("switch", "turn_on")


@pytest.mark.asyncio
async def test_off_is_idempotent(core, client):
    for _ in range(3):
        await core.command("living_room_light", "on_off", False)
    targets = {call[2]["entity_id"] for call in client.calls}
    services = {call[1] for call in client.calls}
    # 세 번 모두 "끄기 씬"만 실행 — 토글처럼 뒤집히지 않는다.
    assert targets == {"switch.geosil_ggeugi"}
    assert services == {"turn_on"}


@pytest.mark.asyncio
async def test_brightness_scales_to_ha_range(core, client):
    await core.command("living_room_stand", "brightness", 60)
    domain, service, data = client.calls[-1]
    assert (domain, service) == ("light", "turn_on")
    assert data["brightness"] == 153  # 60% of 255


def test_brightness_scales_back_to_domain(registry, client):
    cap = registry.get("living_room_stand").capability("brightness")
    raw = {"state": "on", "attributes": {"brightness": 128}}
    assert adapter.to_domain(cap, raw) == pytest.approx(50.2, abs=0.2)


def test_scene_capability_never_reports_state(registry):
    cap = registry.get("balcony_light").capability("on_off")
    assert adapter.to_domain(cap, {"state": "off", "attributes": {}}) is None


def test_unknown_values_become_none(registry):
    cap = registry.get("living_room_power").capability("power")
    assert adapter.to_domain(cap, {"state": "unavailable", "attributes": {}}) is None


def test_out_of_range_is_rejected(registry):
    cap = registry.get("living_room_ac").capability("target_temperature")
    with pytest.raises(CommandError):
        adapter.to_ha_number(cap, 40)


@pytest.mark.asyncio
async def test_read_only_capability_cannot_be_commanded(core):
    with pytest.raises(CommandError):
        await core.command("washer", "status", "idle")


@pytest.mark.asyncio
async def test_climate_uses_its_own_service(core, client):
    await core.command("living_room_ac", "target_temperature", 24)
    assert client.calls[-1][:2] == ("climate", "set_temperature")
    assert client.calls[-1][2]["temperature"] == 24
