import asyncio

import pytest

from home_core.events import EventBroker


@pytest.mark.asyncio
async def test_broker_delivers_to_subscribers():
    broker = EventBroker()
    received = []

    async def consume():
        async for event in broker.subscribe():
            received.append(event)
            if len(received) == 2:
                break

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)
    broker.publish({"n": 1})
    broker.publish({"n": 2})
    await asyncio.wait_for(task, timeout=1)
    assert [e["n"] for e in received] == [1, 2]


@pytest.mark.asyncio
async def test_publish_without_subscribers_is_a_noop(core):
    core.broker.publish({"n": 0})
    assert core.broker.subscriber_count == 0


@pytest.mark.asyncio
async def test_commands_are_published(core):
    events = []

    async def consume():
        async for event in core.broker.subscribe():
            events.append(event)
            break

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)
    await core.command("balcony_light", "on_off", True)
    await asyncio.wait_for(task, timeout=1)
    assert events[0]["type"] == "command"
    assert events[0]["entity_id"] == "switch.beranda_kyeogi"
