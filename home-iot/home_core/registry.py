"""config/devices.yaml 로더."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Registry

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "devices.yaml"


def load_registry(path: str | Path | None = None) -> Registry:
    p = Path(path) if path else DEFAULT_PATH
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    devices = []
    for dev_id, body in (raw.get("devices") or {}).items():
        body = dict(body)
        caps = {}
        for cap_name, cap_body in (body.pop("capabilities", None) or {}).items():
            cap_body = dict(cap_body)
            cap_body["name"] = cap_name
            caps[cap_name] = cap_body
        devices.append({"id": dev_id, "capabilities": caps, **body})
    return Registry(devices=devices)
