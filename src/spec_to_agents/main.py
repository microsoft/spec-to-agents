# Copyright (c) Microsoft. All rights reserved.

from dotenv import load_dotenv

# Load environment variables at module import
load_dotenv()


def main() -> None:
    """Launch the event planning workflow and agents in DevUI."""
    import logging
    import os

    from agent_framework.devui import serve

    from spec_to_agents.agents import export_agents
    from spec_to_agents.workflow import export_workflows

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    # Get port from environment (for container deployments) or use default
    port = int(os.getenv("PORT", "8080"))
    # Disable auto_open in container environments
    auto_open = os.getenv("ENVIRONMENT") != "production"

    logger.info("Starting Agent Workflow DevUI...")
    logger.info(f"Available at: http://0.0.0.0:{port}")

    # Combine workflows and individual agents for DevUI
    # DevUI's serve() handles cleanup via FastAPI lifespan hooks
    entities = export_workflows() + export_agents()
    serve(entities=entities, port=port, host="0.0.0.0", auto_open=auto_open)


if __name__ == "__main__":
    main()
