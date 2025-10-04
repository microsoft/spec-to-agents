"""
Main entry point for the backend API server.
This module starts the FastAPI server for API-only serving.
The frontend is served separately via Vite dev server or static hosting.
"""

import logging
from typing import Never
from agent_framework import (
    WorkflowAgent,
    Workflow,
    WorkflowBuilder,
    executor,
    WorkflowContext,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from spec2agent.api._server import DevServer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    load_dotenv()

    def get_weather(location: str) -> str:
        """Get weather for a location."""
        return f"Weather in {location}: 72°F and sunny"

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )

    client = AzureOpenAIResponsesClient(
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        base_url=os.environ["AZURE_OPENAI_API_BASE_URL"],
        ad_token_provider=token_provider,
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )

    writer = client.create_agent(
        name="Writer",
        instructions=(
            "You are an excellent content writer. You create new content and edit contents based on the feedback."
        ),
    )

    # Create a Reviewer agent that provides feedback
    reviewer = client.create_agent(
        name="Reviewer",
        instructions=(
            "You are an excellent content reviewer. "
            "Provide actionable feedback to the writer about the provided content. "
            "Provide the feedback in the most concise manner possible."
        ),
    )

    agent = (
        WorkflowBuilder()
        .add_edge(writer, reviewer)
        .set_start_executor(writer)
        .build()
        .as_agent()
    )

    """Start the backend API server."""
    # Create and configure the server
    server = DevServer(
        entities_dir=None,  # Will use default discovery
        port=8080,
        host="127.0.0.1",
        cors_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative frontend port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        ui_enabled=False,  # UI is served separately
    )
    entities = [agent]
    server._pending_entities = entities

    # Get the FastAPI app
    app = server.get_app()

    # Start the server using uvicorn
    import uvicorn

    logger.info("Starting backend API server on http://127.0.0.1:8080")
    logger.info("Frontend should be served separately (e.g., via Vite dev server)")
    logger.info("API endpoints available at: http://127.0.0.1:8080/v1/*")

    uvicorn.run(
        app,
        host=server.host,
        port=server.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
