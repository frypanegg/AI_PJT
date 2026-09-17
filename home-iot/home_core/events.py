"""SSE 브로커 — 상태 변화를 구독자에게 뿌린다."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator


class EventBroker:
    def __init__(self, queue_size: int = 200) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._queue_size = queue_size

    def publish(self, event: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            if q.full():  # 느린 구독자 때문에 전체가 막히지 않게 한다
                continue
            q.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        q: asyncio.Queue = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subscribers.discard(q)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
