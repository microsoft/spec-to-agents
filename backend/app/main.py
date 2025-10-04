"""
Main entry point for the backend API server.
This module starts the FastAPI server for API-only serving.
The frontend is served separately via Vite dev server or static hosting.
"""

import logging

from spec2agent.api._server import DevServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
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
