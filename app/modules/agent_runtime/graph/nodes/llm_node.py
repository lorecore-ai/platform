"""LLM agent node: ReAct-style LLM invocation with optional tool calling."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.modules.agent_runtime.graph.state import AgentGraphState

logger = logging.getLogger(__name__)


def make_llm_node(
    llm: ChatOpenAI,
    tools: list | None = None,
) -> Callable[[AgentGraphState], dict[str, Any]]:
    """Factory that returns an async LLM node bound to the given model and tools.

    If tools are provided, the LLM is bound with them so it can issue tool_calls.
    The node returns either a tool_call (routed to ToolNode) or a final answer.
    """
    bound_llm = llm.bind_tools(tools) if tools else llm

    async def llm_agent_node(state: AgentGraphState) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {"final_content": ""}

        response: AIMessage = await bound_llm.ainvoke(messages)

        tool_calls_log = list(state.get("tool_calls_log", []))
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_calls_log.append({
                    "name": tc["name"],
                    "args": tc["args"],
                    "start_ms": int(time.monotonic() * 1000),
                    "status": "pending",
                })

        usage = _extract_usage(response, llm.model_name)

        return {
            "messages": [response],
            "tool_calls_log": tool_calls_log,
            "usage": usage,
            "final_content": str(response.content) if not response.tool_calls else "",
        }

    return llm_agent_node


def should_continue(state: AgentGraphState) -> str:
    """Conditional edge: route to tools if last message has tool_calls, else to cost_tracker."""
    messages = state.get("messages", [])
    if not messages:
        return "cost_tracker"

    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "cost_tracker"


def _extract_usage(response: AIMessage, model_name: str) -> dict[str, Any]:
    """Extract token usage from the AIMessage response metadata."""
    usage: dict[str, Any] = {"model": model_name}
    meta = getattr(response, "usage_metadata", None)
    if meta:
        usage["input_tokens"] = meta.get("input_tokens", 0)
        usage["output_tokens"] = meta.get("output_tokens", 0)
        usage["total_tokens"] = meta.get("total_tokens", 0)
    response_meta = getattr(response, "response_metadata", {})
    if token_usage := response_meta.get("token_usage"):
        usage.setdefault("input_tokens", token_usage.get("prompt_tokens", 0))
        usage.setdefault("output_tokens", token_usage.get("completion_tokens", 0))
        usage.setdefault("total_tokens", token_usage.get("total_tokens", 0))
    return usage
