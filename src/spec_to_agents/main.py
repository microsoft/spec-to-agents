# Copyright (c) Microsoft. All rights reserved.

import os

from agent_framework.observability import setup_observability
from dotenv import load_dotenv

# Load environment variables at module import
load_dotenv()

# Enable observability
setup_observability()


def main() -> None:
    """Launch the branching workflow in DevUI with DI container."""
    import asyncio
    import logging

    from agent_framework.devui import serve

    from spec_to_agents.agents import export_agents
    from spec_to_agents.container import AppContainer
    from spec_to_agents.workflow import export_workflow

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    # Initialize DI container and wire modules for dependency injection
    container = AppContainer()
    container.wire(modules=[__name__])

    # Override global_tools with empty dict since MCP tools cannot be used in DevUI mode
    # (async context manager lifecycle incompatible with FastAPI's event loop)
    container.global_tools.override({})  # type: ignore

    # Get port from environment (for container deployments) or use default
    port = int(os.getenv("PORT", "8080"))
    # Disable auto_open in container environments
    auto_open = os.getenv("ENVIRONMENT") != "production"

    logger.info("Starting Agent Workflow DevUI...")
    logger.info(f"Available at: http://localhost:{port}")

    # Initialize resources asynchronously before loading entities
    async def load_entities():
        workflows = await export_workflow()
        agents = export_agents()
        return workflows + agents

    # Load entities synchronously for serve()
    entities = asyncio.run(load_entities())

    # DevUI's serve() handles cleanup via FastAPI lifespan hooks
    # Use localhost for security; override with --host 0.0.0.0 if needed for external access
    # Dependencies (client, global_tools) are injected automatically into workflow/agent builders
    serve(entities=entities, port=port, host="localhost", auto_open=auto_open)


if __name__ == "__main__":
    main()
