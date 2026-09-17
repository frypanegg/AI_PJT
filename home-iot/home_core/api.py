"""FastAPI 앱 — 조회 / 제어 / SSE / 이력."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .adapter import CommandError
from .config import Settings
from .events import EventBroker
from .ha_client import HttpHaClient
from .history import History
from .registry import load_registry
from .service import HomeCore


class CommandBody(BaseModel):
    capability: str
    value: Any


def build_core(settings: Settings | None = None) -> HomeCore:
    settings = settings or Settings.from_env()
    return HomeCore(
        registry=load_registry(settings.registry_path),
        client=HttpHaClient(settings.ha_url, settings.ha_token),
        history=History(settings.db_path),
        broker=EventBroker(),
    )


def create_app(core: HomeCore | None = None, poll_interval: float | None = None) -> FastAPI:
    interval = poll_interval if poll_interval is not None else Settings.from_env().poll_interval

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = None
        if interval > 0:
            async def poll() -> None:
                while True:
                    try:
                        await app.state.core.refresh()
                    except Exception:  # 폴링 실패로 앱이 죽지 않게 한다
                        pass
                    await asyncio.sleep(interval)

            task = asyncio.create_task(poll())
        yield
        if task:
            task.cancel()

    app = FastAPI(title="home-core", lifespan=lifespan)
    app.state.core = core or build_core()

    def get_core() -> HomeCore:
        return app.state.core

    @app.get("/health")
    async def health() -> dict[str, Any]:
        c = get_core()
        return {"ok": True, "devices": len(c.registry.devices), "rooms": len(c.registry.rooms)}

    @app.get("/devices")
    async def devices(c: HomeCore = Depends(get_core)) -> list[dict[str, Any]]:
        return [
            {
                "id": d.id,
                "name": d.name,
                "room": d.room,
                "kind": d.kind,
                "capabilities": {
                    name: {
                        "type": cap.type.value,
                        "unit": cap.unit,
                        "writable": cap.writable,
                        "readable": cap.source.readable,
                    }
                    for name, cap in d.capabilities.items()
                },
                "state": c.device_state(d.id),
                "note": d.note,
            }
            for d in c.registry.devices
        ]

    @app.get("/state")
    async def state(c: HomeCore = Depends(get_core)) -> dict[str, Any]:
        return c.snapshot()

    @app.post("/refresh")
    async def refresh(c: HomeCore = Depends(get_core)) -> dict[str, Any]:
        return await c.refresh()

    @app.post("/devices/{device_id}/command")
    async def command(device_id: str, body: CommandBody, c: HomeCore = Depends(get_core)) -> dict[str, Any]:
        try:
            return await c.command(device_id, body.capability, body.value)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CommandError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/history")
    async def history(device_id: str | None = None, limit: int = 100, c: HomeCore = Depends(get_core)) -> list[dict[str, Any]]:
        return c.history.recent(device_id, limit)

    @app.get("/events")
    async def events(c: HomeCore = Depends(get_core)) -> StreamingResponse:
        async def stream():
            async for event in c.broker.subscribe():
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app
