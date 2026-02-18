"""InputGuard node: PII detection, masking, and rejection."""
from __future__ import annotations

import logging
import time
from dataclasses import asdict
from typing import Any

from app.modules.agent_runtime.graph.state import AgentGraphState
from app.modules.agent_runtime.middleware.pii_detector import detect_pii

logger = logging.getLogger(__name__)


async def input_guard_node(state: AgentGraphState) -> dict[str, Any]:
    """Check user input for PII / sensitive data.

    - Low-severity matches (email, phone, card, IP) are masked and processing continues.
    - Critical matches (passport, SSN, API keys, JWTs) cause the message to be rejected.

    Sets `guardrail_result` and `processed_input` in state.
    Also initializes `start_time` for response timing.
    """
    raw_messages = state.get("raw_user_messages", [])
    combined_input = "\n".join(raw_messages) if raw_messages else ""

    result = detect_pii(combined_input)

    if result.has_critical:
        logger.warning(
            "Rejected message in thread %s: %s",
            state.get("thread_id"),
            result.rejection_reason,
        )
        return {
            "guardrail_result": {
                "status": "rejected",
                "processed_content": None,
                "violations": [asdict(m) for m in result.matches],
                "rejection_reason": result.rejection_reason,
            },
            "processed_input": "",
            "start_time": time.monotonic(),
        }

    if result.has_low:
        logger.info(
            "Masked %d PII items in thread %s",
            len(result.matches),
            state.get("thread_id"),
        )
        status = "masked"
    else:
        status = "clean"

    return {
        "guardrail_result": {
            "status": status,
            "processed_content": result.masked_text,
            "violations": [asdict(m) for m in result.matches],
            "rejection_reason": None,
        },
        "processed_input": result.masked_text,
        "start_time": time.monotonic(),
    }
