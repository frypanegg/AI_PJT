import pytest
from fastapi.testclient import TestClient

from home_core.api import create_app


@pytest.fixture
def app_client(core):
    app = create_app(core, poll_interval=0)
    with TestClient(app) as tc:
        yield tc


def test_health(app_client, core):
    body = app_client.get("/health").json()
    assert body["devices"] == len(core.registry.devices)
    assert body["rooms"] == 7


def test_devices_expose_readability(app_client):
    devices = {d["id"]: d for d in app_client.get("/devices").json()}
    assert devices["living_room_light"]["capabilities"]["on_off"]["readable"] is False
    assert devices["living_room_stand"]["capabilities"]["brightness"]["readable"] is True


def test_command_roundtrip(app_client):
    r = app_client.post("/devices/kitchen_light/command", json={"capability": "on_off", "value": False})
    assert r.status_code == 200
    assert r.json()["entity_id"] == "switch.jubang_ggeugi"


def test_command_on_unknown_device_is_404(app_client):
    r = app_client.post("/devices/nope/command", json={"capability": "on_off", "value": True})
    assert r.status_code == 404


def test_command_on_read_only_capability_is_400(app_client):
    r = app_client.post("/devices/washer/command", json={"capability": "status", "value": "x"})
    assert r.status_code == 400


def test_history_endpoint(app_client):
    app_client.post("/refresh")
    rows = app_client.get("/history", params={"device_id": "washer"}).json()
    assert any(r["capability"] == "status" for r in rows)
