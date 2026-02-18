"""Threads API router: CRUD, message queue, and SSE streaming."""
import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.modules.agents.deps import get_agent_service
from app.modules.agents.service import AgentService
from app.modules.agent_runtime.message_queue import QueuedMessage, queue_manager
from app.modules.agent_runtime.service import AgentRuntimeService
from app.modules.threads.deps import (
    get_agent_runtime_service,
    get_message_service,
    get_thread_service,
)
from app.modules.threads.models import MessageRole
from app.modules.threads.schemas import (
    MessageAccepted,
    MessageCreate,
    MessageRead,
    ThreadCreate,
    ThreadRead,
)
from app.modules.threads.service import MessageService, ThreadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threads", tags=["threads"])


def _thread_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Thread not found",
    )


# ---------- Thread CRUD (unchanged) ----------

@router.post(
    "/",
    response_model=ThreadRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    data: ThreadCreate,
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadRead:
    """Create thread. Agents added when they send messages."""
    thread = await thread_service.create(data.tenant_id, data)
    return ThreadRead(
        id=thread.id,
        tenant_id=thread.tenant_id,
        agent_ids=[],
        title=thread.title,
        metadata_=thread.metadata_,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.get("/tenant/{tenant_id}", response_model=list[ThreadRead])
async def list_threads(
    tenant_id: uuid.UUID,
    thread_service: ThreadService = Depends(get_thread_service),
) -> list[ThreadRead]:
    threads = await thread_service.get_by_tenant(tenant_id)
    return [ThreadRead.from_thread(t) for t in threads]


@router.get("/{thread_id}", response_model=ThreadRead)
async def get_thread(
    thread_id: uuid.UUID,
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadRead:
    thread = await thread_service.get(thread_id)
    if not thread:
        raise _thread_not_found()
    return ThreadRead.from_thread(thread)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: uuid.UUID,
    thread_service: ThreadService = Depends(get_thread_service),
) -> None:
    thread = await thread_service.get(thread_id)
    if not thread:
        raise _thread_not_found()
    await thread_service.delete(thread)


@router.get("/{thread_id}/messages", response_model=list[MessageRead])
async def get_thread_messages(
    thread_id: uuid.UUID,
    thread_service: ThreadService = Depends(get_thread_service),
    message_service: MessageService = Depends(get_message_service),
) -> list[MessageRead]:
    thread = await thread_service.get(thread_id)
    if not thread:
        raise _thread_not_found()
    messages = await message_service.get_history(thread_id)
    return [MessageRead.from_message(m) for m in messages]


# ---------- New message send (queue-based, non-blocking) ----------

@router.post(
    "/{thread_id}/messages",
    response_model=MessageAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_message(
    thread_id: uuid.UUID,
    data: MessageCreate,
    thread_service: ThreadService = Depends(get_thread_service),
    message_service: MessageService = Depends(get_message_service),
    agent_service: AgentService = Depends(get_agent_service),
    runtime_service: AgentRuntimeService = Depends(get_agent_runtime_service),
) -> JSONResponse:
    """Accept a user message. Returns 202 immediately.

    If the LLM is idle, processing starts right away (status="processing").
    If the LLM is busy with a previous message, the message is queued
    and will be merged into the next LLM invocation (status="queued").

    Subscribe to GET /{thread_id}/stream for SSE delivery of the response.
    """
    thread = await thread_service.get(thread_id)
    if not thread:
        raise _thread_not_found()

    author_agent = await agent_service.get_by_id(data.agent_id)
    if not author_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    is_tenant_agent = author_agent.tenant_id == thread.tenant_id
    is_platform = author_agent.tenant_id is None
    if not (is_tenant_agent or is_platform):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent does not belong to thread's tenant",
        )

    system_agent = await agent_service.get_system_agent_for_tenant(thread.tenant_id)
    if not system_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant has no system agent to respond",
        )

    await thread_service.ensure_agent_in_thread(thread_id, data.agent_id)

    user_message = await message_service.create(
        thread_id, data.agent_id, MessageRole.user, data.content
    )

    queued = QueuedMessage(message_id=user_message.id, content=data.content)
    queue_status = await queue_manager.enqueue(thread_id, queued)

    if queue_status == "processing":
        asyncio.create_task(
            _process_loop(
                thread_id=thread_id,
                tenant_id=thread.tenant_id,
                system_agent_id=system_agent.id,
                runtime_service=runtime_service,
                thread_service=thread_service,
                message_service=message_service,
            )
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message_id": str(user_message.id),
            "status": queue_status,
        },
    )


async def _process_loop(
    thread_id: uuid.UUID,
    tenant_id: uuid.UUID,
    system_agent_id: uuid.UUID,
    runtime_service: AgentRuntimeService,
    thread_service: ThreadService,
    message_service: MessageService,
) -> None:
    """Background processing loop: drain queue, merge messages, run graph, repeat."""
    try:
        while True:
            user_messages = await queue_manager.drain_and_merge(thread_id)
            if not user_messages:
                break

            collected_content = ""
            metadata: dict | None = None

            async for event in runtime_service.stream_response(
                thread_id=thread_id,
                tenant_id=tenant_id,
                user_messages=user_messages,
            ):
                await queue_manager.broadcast(thread_id, event)

                if event.get("type") == "chunk":
                    collected_content += event.get("content", "")
                elif event.get("type") == "guardrail_reject":
                    collected_content = event.get("reason", "Message rejected")
                elif event.get("type") == "done":
                    metadata = event.get("metadata")

            await thread_service.ensure_agent_in_thread(thread_id, system_agent_id)
            await message_service.create(
                thread_id,
                system_agent_id,
                MessageRole.assistant,
                collected_content or "(no response)",
                metadata=metadata,
            )

            has_more = await queue_manager.mark_done(thread_id)
            if not has_more:
                break

    except Exception:
        logger.exception("Error in processing loop for thread %s", thread_id)
    finally:
        await queue_manager.broadcast(
            thread_id, {"type": "stream_end"}
        )


# ---------- SSE stream endpoint ----------

@router.get("/{thread_id}/stream")
async def stream_thread_events(
    thread_id: uuid.UUID,
    thread_service: ThreadService = Depends(get_thread_service),
) -> StreamingResponse:
    """SSE endpoint: subscribe to real-time events for a thread.

    Event types:
    - data: {"type": "chunk", "content": "..."}
    - data: {"type": "guardrail_reject", "reason": "..."}
    - data: {"type": "done", "metadata": {...}}
    - data: {"type": "stream_end"}
    """
    thread = await thread_service.get(thread_id)
    if not thread:
        raise _thread_not_found()

    async def event_generator():
        async for event in queue_manager.subscribe(thread_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
