"""LangChain service: LLM streaming with cancellation support.

.. deprecated::
    This module is superseded by ``app.modules.agent_runtime.service.AgentRuntimeService``
    which provides LangGraph-based processing with guardrails, memory management,
    cost tracking, and message queue support. This module is kept for backward
    compatibility and will be removed in a future release.
"""
import asyncio
import logging
import os
import uuid
import warnings
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.secrets.base import SecretsManager
from app.modules.threads.models import Message, MessageRole

logger = logging.getLogger(__name__)

# In-memory map: thread_id -> asyncio.Task for cancellation on new user message
_active_tasks: dict[uuid.UUID, asyncio.Task] = {}
_tasks_lock = asyncio.Lock()

# Заготовленные настройки LLM (платформа)
LLM_CONFIG = {
    "model": "gpt-4o-mini",
    "system_prompt": "You are a helpful assistant.",
    "temperature": 0.7,
}


class LangChainService:
    """Service for streaming LLM responses with per-thread cancellation.

    .. deprecated::
        Use ``AgentRuntimeService`` from ``app.modules.agent_runtime`` instead.
    """

    def __init__(
        self,
        session: AsyncSession,
        secrets: SecretsManager,
    ) -> None:
        warnings.warn(
            "LangChainService is deprecated, use AgentRuntimeService",
            DeprecationWarning,
            stacklevel=2,
        )
        self._session = session
        self._secrets = secrets

    def _build_messages(
        self,
        history: list[Message],
        user_content: str,
    ) -> list[BaseMessage]:
        """Build LangChain message list from history and new user message."""
        messages: list[BaseMessage] = []

        if LLM_CONFIG["system_prompt"]:
            messages.append(SystemMessage(content=LLM_CONFIG["system_prompt"]))

        for msg in history:
            if msg.role == MessageRole.user:
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=user_content))
        return messages

    async def _get_openai_api_key(self, tenant_id: uuid.UUID) -> str | None:
        """Get OpenAI API key from Vault (tenant or platform) or env fallback."""
        for tid in (str(tenant_id), "platform"):
            try:
                creds = await self._secrets.get(tenant_id=tid, integration="openai")
                if api_key := creds.get("api_key"):
                    return api_key
            except Exception as e:
                logger.debug("OpenAI key not found in Vault for %s: %s", tid, e)
        return os.getenv("OPENAI_API_KEY")

    def _create_llm(self, api_key: str | None) -> ChatOpenAI:
        """Create ChatOpenAI instance from platform config."""
        kwargs = {
            "model": LLM_CONFIG["model"],
            "streaming": True,
            "temperature": LLM_CONFIG["temperature"],
        }
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    async def stream_response(
        self,
        thread_id: uuid.UUID,
        tenant_id: uuid.UUID,
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
            api_key = await self._get_openai_api_key(tenant_id)
            messages = self._build_messages(history, user_content)
            llm = self._create_llm(api_key)

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
