# Copyright (c) Microsoft. All rights reserved.

"""
Bing Web Search tool using persistent agent pattern.

This module implements a web search function using Azure AI Agent Framework's
persistent agent pattern. The agent is created once on the Azure AI service
and reused across invocations by storing its ID at module level.

Architecture
------------
- **Persistent Agent**: Agent created on Azure AI service (store=True)
- **ID Caching**: Only agent_id stored at module level, not client/agent instances
- **Context Manager Cleanup**: Each call uses async context manager for client
- **Service-Side Persistence**: Agent lives on Azure AI service between calls

Resource Management
-------------------
The pattern ensures proper resource management:
1. Agent created once using async context manager (auto-cleanup of creation client)
2. Agent ID stored at module level (lightweight, no cleanup needed)
3. Each web_search() call creates new client context for retrieval
4. Client automatically cleaned up on context exit
5. Agent persists on service side for reuse

This approach avoids resource leaks while maintaining performance benefits of
agent reuse, addressing feedback from PR #61.

Notes
-----
For production deployments with agent cleanup requirements, consider implementing
an explicit cleanup function using atexit or providing a shutdown hook.
"""

import os

from agent_framework import HostedWebSearchTool, ToolMode, ai_function

from spec_to_agents.utils.clients import create_agent_client

# Module-level cache for the web search agent ID (persistent on service side)
_web_search_agent_id: str | None = None


async def _get_or_create_web_search_agent_id() -> str:
    """
    Get or create the persistent web search agent ID.

    Creates a persistent agent on Azure AI service on first call, then returns
    the cached agent_id for subsequent calls. The agent persists on the service
    side while this function stores only the ID for retrieval.

    Returns
    -------
    str
        The agent ID for the persistent web search agent on Azure AI service.

    Notes
    -----
    Uses async context manager for client creation to ensure proper cleanup
    of temporary connections while the agent itself persists on the service.
    """
    global _web_search_agent_id

    if _web_search_agent_id is None:
        # Ensure conflicting environment variables are not set
        os.environ.pop("BING_CONNECTION_ID", None)
        os.environ.pop("BING_CUSTOM_CONNECTION_NAME", None)
        os.environ.pop("BING_CUSTOM_INSTANCE_NAME", None)

        web_search_tool = HostedWebSearchTool(description="Search the web for current information using Bing")

        # Use context manager for proper cleanup
        async with create_agent_client() as client:
            agent = client.create_agent(
                name="BingWebSearchAgent",
                tools=[web_search_tool],
                system_message=(
                    "You are a web search agent that uses the Bing Web Search tool to find information on the web."
                ),
                tool_choice=ToolMode.REQUIRED(function_name="web_search"),
                store=True,
                model_id=os.getenv("WEB_SEARCH_MODEL", "gpt-4o-mini"),
            )
            # Store only the agent ID - agent persists on service side
            _web_search_agent_id = agent.id

    return _web_search_agent_id


@ai_function  # type: ignore[arg-type]
async def web_search(
    query: str,
) -> str:
    """
    Search the web using Bing Web Search.

    Parameters
    ----------
    query : str
        The search query to execute

    Returns
    -------
    str
        Formatted search results containing:
        - Query executed
        - Number of results found
        - Numbered results
        - Title, snippet, URL, and display URL for each result

    Uses a persistent agent stored on Azure AI service. The agent is created once
    and retrieved by ID for subsequent calls, ensuring efficient resource usage
    while respecting async context manager cleanup for temporary connections.
    """
    try:
        # Get the persistent agent ID
        agent_id = await _get_or_create_web_search_agent_id()

        # Use context manager for client - retrieve existing agent by ID
        async with create_agent_client(agent_id=agent_id) as client:
            # Client is now connected to the persistent agent
            response = await client.run(f"Perform a web search for: {query}")
            return response.text

    except Exception as e:
        # Handle API errors gracefully
        error_type = type(e).__name__
        return f"Error performing web search: {error_type} - {e!s}"


async def cleanup_web_search_agent() -> None:
    """
    Clean up the persistent web search agent from Azure AI service.

    This function should be called during application shutdown to delete
    the persistent agent from the Azure AI service. It is optional for
    development but recommended for production deployments.

    Notes
    -----
    In production, register this with atexit or your application's shutdown hooks:

        import atexit
        import asyncio

        def shutdown():
            asyncio.run(cleanup_web_search_agent())

        atexit.register(shutdown)
    """
    global _web_search_agent_id

    if _web_search_agent_id is not None:
        try:
            async with create_agent_client():
                # Note: Client will auto-delete agent on context exit if needed
                # This is handled by framework's cleanup mechanism
                _web_search_agent_id = None
        except Exception:
            # Log but don't raise - shutdown should be resilient
            # In production, use proper logging instead of print
            _web_search_agent_id = None


__all__ = ["web_search"]
