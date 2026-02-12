"""LangChain service: LLM streaming with cancellation support."""
import asyncio
import logging
import uuid
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.models import Agent
from app.modules.threads.models import Message, MessageRole

logger = logging.getLogger(__name__)

# In-memory map: thread_id -> asyncio.Task for cancellation on new user message
_active_tasks: dict[uuid.UUID, asyncio.Task] = {}
_tasks_lock = asyncio.Lock()


class LangChainService:
    """Service for streaming LLM responses with per-thread cancellation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _build_messages(
        self,
        agent: Agent,
        history: list[Message],
        user_content: str,
    ) -> list[BaseMessage]:
        """Build LangChain message list from history and new user message."""
        messages: list[BaseMessage] = []

        if agent.system_prompt:
            messages.append(SystemMessage(content=agent.system_prompt))

        for msg in history:
            if msg.role == MessageRole.user:
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=user_content))
        return messages

    def _create_llm(self, agent: Agent) -> ChatOpenAI:
        """Create ChatOpenAI instance from agent config."""
        return ChatOpenAI(
            model=agent.model,
            streaming=True,
            temperature=0.7,
        )

    async def stream_response(
        self,
        thread_id: uuid.UUID,
        agent: Agent,
        history: list[Message],
        user_content: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response. Cancels previous task for this thread if exists.
        Yields text chunks. Raises asyncio.CancelledError when cancelled.
        """
        async with _tasks_lock:
            if prev_task := _active_tasks.get(thread_id):
                prev_task.cancel()
                try:
                    await prev_task
                except asyncio.CancelledError:
                    pass
                del _active_tasks[thread_id]

            task = asyncio.current_task()
            if task:
                _active_tasks[thread_id] = task

        try:
            messages = self._build_messages(agent, history, user_content)
            llm = self._create_llm(agent)

            full_content = ""
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_content += chunk.content
                    yield chunk.content

        except asyncio.CancelledError:
            logger.info("LLM stream cancelled for thread %s", thread_id)
            raise
        finally:
            async with _tasks_lock:
                _active_tasks.pop(thread_id, None)
