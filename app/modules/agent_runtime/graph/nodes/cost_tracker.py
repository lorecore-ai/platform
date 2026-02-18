"""CostTracker node: collect token usage, calculate cost, measure timing."""
from __future__ import annotations

import time
from typing import Any

from app.modules.agent_runtime.graph.state import AgentGraphState

# Pricing per 1M tokens (USD) — update as models change
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}

DEFAULT_PRICING = {"input": 1.00, "output": 3.00}


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 8)


async def cost_tracker_node(state: AgentGraphState) -> dict[str, Any]:
    """Finalize cost and timing metadata for the response.

    Reads usage info set by the LLM node and computes:
    - Total cost in USD
    - Response time in milliseconds
    - Aggregated tool_calls log
    """
    usage = state.get("usage") or {}
    model = usage.get("model", "")
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    total_tokens = usage.get("total_tokens", 0) or (input_tokens + output_tokens)

    cost_usd = _calculate_cost(model, input_tokens, output_tokens)

    start_time = state.get("start_time", 0.0)
    elapsed_ms = int((time.monotonic() - start_time) * 1000) if start_time else 0

    guardrail_result = state.get("guardrail_result")
    guardrail_summary = None
    if guardrail_result:
        violations = guardrail_result.get("violations", [])
        guardrail_summary = {
            "status": guardrail_result.get("status", "clean"),
            "violations_count": len(violations),
        }

    return {
        "usage": {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
        },
        "response_time_ms": elapsed_ms,
    }


def build_message_metadata(state: AgentGraphState) -> dict[str, Any]:
    """Build the metadata dict to store on the assistant Message record."""
    usage = state.get("usage") or {}
    guardrail_result = state.get("guardrail_result")
    tool_calls_log = state.get("tool_calls_log", [])

    guardrail_info = None
    if guardrail_result:
        violations = guardrail_result.get("violations", [])
        guardrail_info = {
            "status": guardrail_result.get("status", "clean"),
            "violations_count": len(violations),
        }

    return {
        "model": usage.get("model", ""),
        "tokens": {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
            "total": usage.get("total_tokens", 0),
        },
        "cost_usd": usage.get("cost_usd", 0.0),
        "response_time_ms": state.get("response_time_ms", 0),
        "tool_calls": [
            {"name": tc.get("name", ""), "status": tc.get("status", "unknown")}
            for tc in tool_calls_log
        ],
        "guardrail": guardrail_info,
    }
