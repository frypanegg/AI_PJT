import pytest


@pytest.mark.asyncio
async def test_refresh_fills_state_and_history(core):
    snapshot = await core.refresh()
    assert snapshot["washer"]["status"] == "rinsing"
    assert snapshot["living_room_power"]["power"] == 312.5
    assert core.history.recent(), "이력이 쌓여야 합니다"


@pytest.mark.asyncio
async def test_finish_time_stays_a_timestamp(core):
    snapshot = await core.refresh()
    # LG 는 "남은 시간"이 아니라 종료 *시각*을 준다 — 숫자로 뭉개면 안 된다.
    assert snapshot["washer"]["finish_at"] == "2026-09-13T10:20:51+00:00"


@pytest.mark.asyncio
async def test_scene_light_has_no_state_after_refresh(core):
    snapshot = await core.refresh()
    assert "on_off" not in snapshot.get("living_room_light", {})


@pytest.mark.asyncio
async def test_history_uses_typed_columns(core):
    await core.refresh()
    rows = {(r["device_id"], r["capability"]): r for r in core.history.recent(limit=200)}
    assert rows[("fridge_door", "open")]["value_bool"] == 0
    assert rows[("living_room_power", "power")]["value_num"] == 312.5
    assert rows[("washer", "status")]["value_text"] == "rinsing"


@pytest.mark.asyncio
async def test_refresh_is_quiet_when_nothing_changed(core):
    await core.refresh()
    before = len(core.history.recent(limit=500))
    await core.refresh()
    assert len(core.history.recent(limit=500)) == before


@pytest.mark.asyncio
async def test_unknown_device_raises(core):
    with pytest.raises(KeyError):
        await core.command("nope", "on_off", True)
