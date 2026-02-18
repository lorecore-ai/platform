"""MemoryLoader node: build conversation history with summarization."""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_openai import ChatOpenAI

from app.modules.agent_runtime.graph.state import AgentGraphState

logger = logging.getLogger(__name__)

MAX_CONTEXT_TOKENS = 4000
SUMMARY_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "You are a helpful assistant."

SUMMARIZE_INSTRUCTION = (
    "Distill the above chat messages into a single concise summary message. "
    "Include key facts and any decisions that were made. Be concise."
)


def _history_to_langchain(history_dicts: list[dict[str, Any]]) -> list[BaseMessage]:
    """Convert serialized history dicts to LangChain messages."""
    msgs: list[BaseMessage] = []
    for h in history_dicts:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role == "assistant":
            msgs.append(AIMessage(content=content))
        else:
            msgs.append(HumanMessage(content=content))
    return msgs


async def _summarize(messages: list[BaseMessage], api_key: str | None = None) -> str:
    """Summarize a list of messages using a cheap model."""
    kwargs: dict[str, Any] = {"model": SUMMARY_MODEL, "temperature": 0}
    if api_key:
        kwargs["api_key"] = api_key
    llm = ChatOpenAI(**kwargs)

    summary_prompt = messages + [
        HumanMessage(content=SUMMARIZE_INSTRUCTION),
    ]
    resp = await llm.ainvoke(summary_prompt)
    return str(resp.content)


async def memory_loader_node(state: AgentGraphState) -> dict[str, Any]:
    """Load conversation history and prepare messages for the LLM.

    Steps:
    1. Build system message
    2. Convert raw history into LangChain messages
    3. Trim to MAX_CONTEXT_TOKENS; if trimmed, summarize the dropped portion
    4. Append the processed user input
    """
    processed_input = state.get("processed_input", "")
    existing_messages = list(state.get("messages", []))

    base_messages: list[BaseMessage] = []

    if SYSTEM_PROMPT:
        base_messages.append(SystemMessage(content=SYSTEM_PROMPT))

    if existing_messages:
        non_system = [m for m in existing_messages if not isinstance(m, SystemMessage)]

        trimmed = trim_messages(
            non_system,
            max_tokens=MAX_CONTEXT_TOKENS,
            token_counter=len,  # approximate: 1 msg ≈ 1 token-unit for trimming heuristic
            strategy="last",
            allow_partial=False,
            start_on="human",
        )

        dropped_count = len(non_system) - len(trimmed)
        if dropped_count > 0:
            dropped = non_system[:dropped_count]
            logger.info(
                "Summarizing %d old messages for thread %s",
                dropped_count,
                state.get("thread_id"),
            )
            try:
                summary_text = await _summarize(dropped)
                base_messages.append(
                    SystemMessage(content=f"Summary of earlier conversation:\n{summary_text}")
                )
            except Exception:
                logger.exception("Summarization failed, using trimmed history only")

        base_messages.extend(trimmed)

    base_messages.append(HumanMessage(content=processed_input))

    return {"messages": base_messages}
