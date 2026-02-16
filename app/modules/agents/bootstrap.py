"""Bootstrap: ensure platform LLM agent exists on startup."""

import logging

from app.core.database import session_context
from app.modules.agents.service import AgentService

logger = logging.getLogger(__name__)


async def init_agents() -> None:
    """Create platform LLM agent if not exists."""
    logger.info("Initializing agents...")

    async with session_context() as db:
        service = AgentService(db)
        await service.ensure_platform_llm_agent()

    logger.info("Agents initialized")
