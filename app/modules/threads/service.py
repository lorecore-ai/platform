"""Thread and Message services: DB operations and business logic."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.agents.models import Agent
from app.modules.threads.models import Message, MessageRole, Thread
from app.modules.threads.schemas import ThreadCreate


class ThreadService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        data: ThreadCreate,
    ) -> Thread:
        thread = Thread(
            tenant_id=tenant_id,
            title=data.title,
            metadata_=data.metadata_,
        )
        self._session.add(thread)
        await self._session.flush()
        await self._session.refresh(thread)
        return thread

    async def ensure_agent_in_thread(self, thread_id: uuid.UUID, agent_id: uuid.UUID) -> None:
        """Add agent to thread participants if not already present."""
        thread = await self.get(thread_id)
        if not thread:
            return
        existing_ids = {a.id for a in thread.agents}
        if agent_id in existing_ids:
            return
        agent = await self._session.get(Agent, agent_id)
        if agent:
            thread.agents.append(agent)
            await self._session.flush()

    async def get(self, thread_id: uuid.UUID) -> Thread | None:
        result = await self._session.execute(
            select(Thread)
            .where(Thread.id == thread_id)
            .options(selectinload(Thread.agents))
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Thread]:
        result = await self._session.execute(
            select(Thread)
            .where(Thread.tenant_id == tenant_id)
            .options(selectinload(Thread.agents))
            .order_by(Thread.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, thread: Thread) -> None:
        await self._session.delete(thread)
        await self._session.flush()


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        thread_id: uuid.UUID,
        agent_id: uuid.UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        message = Message(
            thread_id=thread_id,
            agent_id=agent_id,
            role=role,
            content=content,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def get_history(self, thread_id: uuid.UUID) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
