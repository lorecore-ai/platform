"""Thread and Message services: DB operations and business logic."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.threads.models import Message, MessageRole, Thread
from app.modules.threads.schemas import MessageCreate, ThreadCreate


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
            agent_id=data.agent_id,
            title=data.title,
        )
        self._session.add(thread)
        await self._session.flush()
        await self._session.refresh(thread)
        return thread

    async def get(self, thread_id: uuid.UUID) -> Thread | None:
        result = await self._session.execute(
            select(Thread).where(Thread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Thread]:
        result = await self._session.execute(
            select(Thread)
            .where(Thread.tenant_id == tenant_id)
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
        role: MessageRole,
        content: str,
    ) -> Message:
        message = Message(
            thread_id=thread_id,
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
