import pytest
from pydantic import ValidationError

from home_core.models import Registry, SourceRef


def test_registry_loads(registry):
    assert len(registry.devices) >= 20
    assert "거실" in registry.rooms and "세탁실" in registry.rooms


def test_scene_lights_are_not_readable(registry):
    for dev_id in ("living_room_light", "kitchen_light", "bathroom_light", "balcony_light", "all_lights"):
        cap = registry.get(dev_id).capability("on_off")
        assert cap.source.readable is False, f"{dev_id} 는 상태를 보고하면 안 됩니다"
        assert set(cap.source.command_targets) == {"true", "false"}


def test_no_doorlock_in_registry(registry):
    assert not [d for d in registry.devices if "lock" in d.kind or "lock" in d.id]


def test_source_ref_needs_a_target():
    with pytest.raises(ValidationError):
        SourceRef()


def test_duplicate_device_ids_rejected():
    dev = {"id": "x", "name": "x", "room": "r", "kind": "light", "capabilities": {}}
    with pytest.raises(ValidationError):
        Registry(devices=[dev, dict(dev)])
