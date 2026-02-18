"""Build the agent processing graph."""
from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.modules.agent_runtime.graph.nodes.cost_tracker import cost_tracker_node
from app.modules.agent_runtime.graph.nodes.guardrails import input_guard_node
from app.modules.agent_runtime.graph.nodes.llm_node import make_llm_node, should_continue
from app.modules.agent_runtime.graph.nodes.memory import memory_loader_node
from app.modules.agent_runtime.graph.state import AgentGraphState

REJECT_SENTINEL = "__reject__"


def _guard_router(state: AgentGraphState) -> str:
    gr = state.get("guardrail_result")
    if gr and gr.get("status") == "rejected":
        return REJECT_SENTINEL
    return "memory_loader"


def _reject_node(state: AgentGraphState) -> dict[str, Any]:
    """Terminal node for rejected messages."""
    reason = ""
    if gr := state.get("guardrail_result"):
        reason = gr.get("rejection_reason", "")
    return {
        "final_content": (
            f"Message rejected: {reason}" if reason
            else "Message contains sensitive data and cannot be processed."
        ),
    }


def build_agent_graph(
    llm: ChatOpenAI,
    tools: list | None = None,
) -> StateGraph:
    """Construct and compile the agent StateGraph.

    Nodes: input_guard -> memory_loader -> llm_agent <-> tool_node -> cost_tracker -> END
    Conditional edge from input_guard: rejected -> reject -> END.
    """
    tools = tools or []
    graph = StateGraph(AgentGraphState)

    graph.add_node("input_guard", input_guard_node)
    graph.add_node("memory_loader", memory_loader_node)
    graph.add_node("llm_agent", make_llm_node(llm, tools))
    graph.add_node("cost_tracker", cost_tracker_node)
    graph.add_node("reject", _reject_node)

    if tools:
        graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("input_guard")

    graph.add_conditional_edges(
        "input_guard",
        _guard_router,
        {REJECT_SENTINEL: "reject", "memory_loader": "memory_loader"},
    )

    graph.add_edge("memory_loader", "llm_agent")

    graph.add_conditional_edges(
        "llm_agent",
        should_continue,
        {"tools": "tools", "cost_tracker": "cost_tracker"} if tools else {"cost_tracker": "cost_tracker"},
    )

    if tools:
        graph.add_edge("tools", "llm_agent")

    graph.add_edge("cost_tracker", END)
    graph.add_edge("reject", END)

    return graph
