import pytest

from home_core.events import EventBroker
from home_core.ha_client import FakeHaClient
from home_core.history import History
from home_core.registry import load_registry
from home_core.service import HomeCore


@pytest.fixture
def registry():
    return load_registry()


@pytest.fixture
def client():
    fake = FakeHaClient()
    fake.set_state("light.geosil_stand", "on", brightness=128, color_temp_kelvin=4000)
    fake.set_state("sensor.setakgi_status", "rinsing")
    fake.set_state("sensor.setakgi_finish_time", "2026-09-13T10:20:51+00:00")
    fake.set_state("sensor.geosil_power", "312.5")
    fake.set_state("binary_sensor.naengjangsil_door", "off")
    # 씬 스위치는 실행 뒤 off 로 돌아간다 — 상태로 읽히면 안 된다.
    fake.set_state("switch.geosil_kyeogi", "off")
    fake.set_state("switch.geosil_ggeugi", "off")
    return fake


@pytest.fixture
def core(registry, client, tmp_path):
    return HomeCore(registry, client, History(tmp_path / "t.db"), EventBroker())
