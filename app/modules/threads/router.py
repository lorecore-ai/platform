"""Threads API router: CRUD and streaming."""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.modules.agents.deps import get_agent_service
from app.modules.agents.service import AgentService
from app.modules.threads.deps import (
    get_langchain_service,
    get_message_service,
    get_thread_service,
)
from app.modules.threads.models import MessageRole
from app.modules.threads.schemas import MessageCreate, MessageRead, ThreadCreate, ThreadRead
from app.modules.threads.service import MessageService, ThreadService
from app.modules.threads.langchain_service import LangChainService

router = APIRouter(prefix="/threads", tags=["threads"])


def _thread_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Thread not found",
    )


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
        agent_ids=[],  # no agents on create
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


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: uuid.UUID,
    data: MessageCreate,
    thread_service: ThreadService = Depends(get_thread_service),
    message_service: MessageService = Depends(get_message_service),
    agent_service: AgentService = Depends(get_agent_service),
    langchain_service: LangChainService = Depends(get_langchain_service),
) -> StreamingResponse:
    """Send message from agent_id. LLM response is from system agent."""
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

    history = await message_service.get_history(thread_id)
    await message_service.create(
        thread_id, data.agent_id, MessageRole.user, data.content
    )

    async def event_stream():
        collected = []
        try:
            async for chunk in langchain_service.stream_response(
                thread_id=thread_id,
                history=history,
                user_content=data.content,
            ):
                collected.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        await thread_service.ensure_agent_in_thread(thread_id, system_agent.id)
        full_content = "".join(collected)
        await message_service.create(
            thread_id, system_agent.id, MessageRole.assistant, full_content
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
