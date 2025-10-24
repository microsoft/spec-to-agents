# Copyright (c) Microsoft. All rights reserved.


def main():
    """Launch the branching workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    from spec2agent.agents import export_entities

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Agent Workflow DevUI...")
    logger.info("Available at: http://localhost:8080")

    # DevUI's serve() handles cleanup via FastAPI lifespan hooks
    serve(entities=export_entities(), port=8080, auto_open=True)


if __name__ == "__main__":
    main()
