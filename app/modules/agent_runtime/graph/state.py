"""LangGraph agent state definition."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


@dataclass
class PIIMatch:
    category: str
    severity: Literal["low", "critical"]
    span: tuple[int, int]
    replacement: str


@dataclass
class GuardrailResult:
    status: Literal["clean", "masked", "rejected"]
    processed_content: str | None = None
    violations: list[PIIMatch] = field(default_factory=list)
    rejection_reason: str | None = None


@dataclass
class TokenUsage:
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class AgentState:
    """TypedDict-compatible state for the agent graph.

    Using Annotated[list[BaseMessage], add_messages] so LangGraph
    automatically merges message lists instead of replacing them.
    """

    thread_id: uuid.UUID
    tenant_id: uuid.UUID

    raw_user_messages: list[str]
    processed_input: str
    guardrail_result: GuardrailResult | None

    messages: Annotated[list[BaseMessage], add_messages]

    tool_calls_log: list[dict[str, Any]]
    usage: TokenUsage | None
    response_time_ms: int
    final_content: str


# TypedDict variant used by StateGraph (LangGraph requires TypedDict, not dataclass)
from typing import TypedDict  # noqa: E402


class AgentGraphState(TypedDict, total=False):
    thread_id: uuid.UUID
    tenant_id: uuid.UUID

    raw_user_messages: list[str]
    processed_input: str
    guardrail_result: dict[str, Any] | None

    messages: Annotated[list[BaseMessage], add_messages]

    tool_calls_log: list[dict[str, Any]]
    usage: dict[str, Any] | None
    response_time_ms: int
    final_content: str
    start_time: float
