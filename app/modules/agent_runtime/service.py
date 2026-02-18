"""AgentRuntimeService: LangGraph-based agent execution engine."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_runtime.checkpointer import get_checkpointer
from app.modules.agent_runtime.graph.builder import build_agent_graph
from app.modules.agent_runtime.graph.nodes.cost_tracker import build_message_metadata
from app.modules.agent_runtime.graph.state import AgentGraphState
from app.modules.secrets.base import SecretsManager
from app.modules.threads.models import Message, MessageRole
from app.modules.threads.service import MessageService

logger = logging.getLogger(__name__)

LLM_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
}


class AgentRuntimeService:
    """Orchestrates LangGraph agent execution for a thread."""

    def __init__(
        self,
        session: AsyncSession,
        secrets: SecretsManager,
        message_service: MessageService,
    ) -> None:
        self._session = session
        self._secrets = secrets
        self._message_service = message_service

    async def _get_openai_api_key(self, tenant_id: uuid.UUID) -> str | None:
        for tid in (str(tenant_id), "platform"):
            try:
                creds = await self._secrets.get(tenant_id=tid, integration="openai")
                if api_key := creds.get("api_key"):
                    return api_key
            except Exception as e:
                logger.debug("OpenAI key not found in Vault for %s: %s", tid, e)
        return os.getenv("OPENAI_API_KEY")

    def _create_llm(self, api_key: str | None) -> ChatOpenAI:
        kwargs: dict[str, Any] = {
            "model": LLM_CONFIG["model"],
            "temperature": LLM_CONFIG["temperature"],
        }
        if api_key:
            kwargs["api_key"] = api_key
        return ChatOpenAI(**kwargs)

    async def _load_history_messages(
        self, thread_id: uuid.UUID
    ) -> list[BaseMessage]:
        """Load existing thread messages and convert to LangChain format."""
        history = await self._message_service.get_history(thread_id)
        msgs: list[BaseMessage] = []
        for m in history:
            if m.role == MessageRole.user:
                msgs.append(HumanMessage(content=m.content))
            else:
                msgs.append(AIMessage(content=m.content))
        return msgs

    async def process_messages(
        self,
        thread_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_messages: list[str],
    ) -> dict[str, Any]:
        """Run the agent graph for accumulated user messages.

        Returns the final graph state containing the response,
        usage metadata, and guardrail results.
        """
        api_key = await self._get_openai_api_key(tenant_id)
        llm = self._create_llm(api_key)

        graph = build_agent_graph(llm=llm, tools=[])
        checkpointer = await get_checkpointer()
        compiled = graph.compile(checkpointer=checkpointer)

        history = await self._load_history_messages(thread_id)

        initial_state: dict[str, Any] = {
            "thread_id": thread_id,
            "tenant_id": tenant_id,
            "raw_user_messages": user_messages,
            "processed_input": "",
            "guardrail_result": None,
            "messages": history,
            "tool_calls_log": [],
            "usage": None,
            "response_time_ms": 0,
            "final_content": "",
            "start_time": 0.0,
        }

        config = {"configurable": {"thread_id": str(thread_id)}}

        final_state = await compiled.ainvoke(initial_state, config=config)
        return final_state

    async def process_and_save(
        self,
        thread_id: uuid.UUID,
        tenant_id: uuid.UUID,
        system_agent_id: uuid.UUID,
        user_messages: list[str],
    ) -> Message:
        """Process messages through the graph and persist the assistant response.

        Returns the saved assistant Message with metadata.
        """
        final_state = await self.process_messages(
            thread_id=thread_id,
            tenant_id=tenant_id,
            user_messages=user_messages,
        )

        content = final_state.get("final_content", "")
        metadata = build_message_metadata(final_state)

        message = await self._message_service.create(
            thread_id=thread_id,
            agent_id=system_agent_id,
            role=MessageRole.assistant,
            content=content,
            metadata=metadata,
        )
        return message

    async def stream_response(
        self,
        thread_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_messages: list[str],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream graph execution events for SSE delivery.

        Yields dicts with event type and payload:
        - {"type": "chunk", "content": "..."}
        - {"type": "guardrail_reject", "reason": "..."}
        - {"type": "done", "metadata": {...}}
        """
        api_key = await self._get_openai_api_key(tenant_id)
        llm = self._create_llm(api_key)

        graph = build_agent_graph(llm=llm, tools=[])
        checkpointer = await get_checkpointer()
        compiled = graph.compile(checkpointer=checkpointer)

        history = await self._load_history_messages(thread_id)

        initial_state: dict[str, Any] = {
            "thread_id": thread_id,
            "tenant_id": tenant_id,
            "raw_user_messages": user_messages,
            "processed_input": "",
            "guardrail_result": None,
            "messages": history,
            "tool_calls_log": [],
            "usage": None,
            "response_time_ms": 0,
            "final_content": "",
            "start_time": 0.0,
        }

        config = {"configurable": {"thread_id": str(thread_id)}}

        final_state: dict[str, Any] = {}
        async for event in compiled.astream(initial_state, config=config):
            for node_name, node_output in event.items():
                if node_name == "reject":
                    yield {
                        "type": "guardrail_reject",
                        "reason": node_output.get("final_content", "Message rejected"),
                    }
                    return

                if node_name == "llm_agent":
                    content = node_output.get("final_content", "")
                    if content:
                        yield {"type": "chunk", "content": content}

                final_state.update(node_output)

        metadata = build_message_metadata(final_state)
        yield {"type": "done", "metadata": metadata}
