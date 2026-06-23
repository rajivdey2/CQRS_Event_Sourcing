from __future__ import annotations
import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable

from app.domain.events import DomainEvent

logger = logging.getLogger(__name__)

Handler = Callable[[DomainEvent], Awaitable[None]]


class InProcessEventBus:
    """
    Lightweight in-process pub/sub.
    Projectors register themselves at startup; command handlers publish after
    persisting events.

    Phase-2 migration path: swap this for a KafkaEventBus that implements the
    same publish() / subscribe() interface — no command handler changes needed.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed %s to %s", handler.__class__.__qualname__, event_type)

    async def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            handlers = self._handlers.get(event.event_type, [])
            if not handlers:
                continue
            await asyncio.gather(
                *[h(event) for h in handlers],
                return_exceptions=True,   # don't let a bad projector kill the command
            )


# Single shared instance — injected via FastAPI dependency
event_bus = InProcessEventBus()