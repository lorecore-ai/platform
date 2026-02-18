"""Per-thread message queue with accumulation and merge support.

When the LLM is busy processing a response, incoming user messages are
queued. Once the current response completes, all queued messages are
drained and merged into a single request for the next LLM invocation.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class QueuedMessage:
    message_id: uuid.UUID
    content: str


@dataclass
class _ThreadState:
    queue: asyncio.Queue[QueuedMessage] = field(default_factory=asyncio.Queue)
    processing: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    subscribers: list[asyncio.Queue[dict[str, Any]]] = field(default_factory=list)


ProcessCallback = Callable[
    [uuid.UUID, list[str]],
    Coroutine[Any, Any, None],
]


class MessageQueueManager:
    """Manages per-thread message queues with LLM processing coordination.

    Usage:
        manager = MessageQueueManager()

        # On incoming message:
        status = await manager.enqueue(thread_id, msg)
        # status is "processing" or "queued"

        # Subscribe to SSE events for a thread:
        async for event in manager.subscribe(thread_id):
            yield event
    """

    def __init__(self) -> None:
        self._threads: dict[uuid.UUID, _ThreadState] = {}
        self._lock = asyncio.Lock()

    async def _get_thread_state(self, thread_id: uuid.UUID) -> _ThreadState:
        async with self._lock:
            if thread_id not in self._threads:
                self._threads[thread_id] = _ThreadState()
            return self._threads[thread_id]

    async def enqueue(
        self,
        thread_id: uuid.UUID,
        message: QueuedMessage,
    ) -> str:
        """Add a message to the thread's queue.

        Returns "processing" if LLM starts immediately, "queued" if LLM is busy.
        """
        state = await self._get_thread_state(thread_id)
        await state.queue.put(message)

        async with state.lock:
            if state.processing:
                logger.info(
                    "Message queued for thread %s (LLM busy)", thread_id
                )
                return "queued"
            else:
                state.processing = True
                return "processing"

    async def drain_and_merge(self, thread_id: uuid.UUID) -> list[str]:
        """Drain all queued messages for a thread and return their contents.

        Called by the processing loop after the previous LLM invocation completes.
        """
        state = await self._get_thread_state(thread_id)
        messages: list[str] = []

        while not state.queue.empty():
            try:
                msg = state.queue.get_nowait()
                messages.append(msg.content)
            except asyncio.QueueEmpty:
                break

        return messages

    async def mark_done(self, thread_id: uuid.UUID) -> bool:
        """Mark the current processing as done.

        Returns True if there are more messages to process (queue not empty).
        """
        state = await self._get_thread_state(thread_id)
        async with state.lock:
            if not state.queue.empty():
                return True
            state.processing = False
            return False

    async def broadcast(
        self, thread_id: uuid.UUID, event: dict[str, Any]
    ) -> None:
        """Send an event to all SSE subscribers of this thread."""
        state = await self._get_thread_state(thread_id)
        for sub in state.subscribers:
            await sub.put(event)

    async def subscribe(
        self, thread_id: uuid.UUID
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to SSE events for a thread. Yields events as they arrive."""
        state = await self._get_thread_state(thread_id)
        sub_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        state.subscribers.append(sub_queue)

        try:
            while True:
                event = await sub_queue.get()
                yield event
                if event.get("type") == "stream_end":
                    break
        finally:
            state.subscribers.remove(sub_queue)

    async def cleanup_thread(self, thread_id: uuid.UUID) -> None:
        """Remove thread state when no longer needed."""
        async with self._lock:
            self._threads.pop(thread_id, None)


# Singleton instance, initialized at module level
queue_manager = MessageQueueManager()
