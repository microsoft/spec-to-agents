# Copyright (c) Microsoft. All rights reserved.

from dotenv import load_dotenv

# Load environment variables at module import
load_dotenv()


def main() -> None:
    """Launch the branching workflow in DevUI."""
    import logging
    import os

    from agent_framework.devui import serve

    from spec_to_agents.workflow import export_workflow

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    # Get port from environment (for container deployments) or use default
    port = int(os.getenv("PORT", "8080"))
    # Disable auto_open in container environments
    auto_open = os.getenv("ENVIRONMENT") != "production"

    logger.info("Starting Agent Workflow DevUI...")
    logger.info(f"Available at: http://localhost:{port}")

    # DevUI's serve() handles cleanup via FastAPI lifespan hooks
    # Use localhost for security; override with --host 0.0.0.0 if needed for external access
    serve(entities=export_workflow(), port=port, host="localhost", auto_open=auto_open)


if __name__ == "__main__":
    main()
