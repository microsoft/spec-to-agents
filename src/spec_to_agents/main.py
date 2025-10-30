# Copyright (c) Microsoft. All rights reserved.


def main():
    """Launch the branching workflow in DevUI."""
    import logging
    import os

    from agent_framework.devui import serve

    from spec_to_agents.agents import export_entities

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    # Get port from environment (for container deployments) or use default
    port = int(os.getenv("PORT", "8080"))
    # Disable auto_open in container environments
    auto_open = os.getenv("ENVIRONMENT") != "production"

    logger.info("Starting Agent Workflow DevUI...")
    logger.info(f"Available at: http://0.0.0.0:{port}")

    # DevUI's serve() handles cleanup via FastAPI lifespan hooks
    serve(entities=export_entities(), port=port, host="0.0.0.0", auto_open=auto_open)


if __name__ == "__main__":
    main()
