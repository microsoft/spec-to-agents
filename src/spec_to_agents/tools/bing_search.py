# Copyright (c) Microsoft. All rights reserved.

"""Bing Web Search tool using Azure Cognitive Services."""

import os
from typing import Annotated

from agent_framework import HostedWebSearchTool, ToolMode, ai_function
from pydantic import Field

from spec_to_agents.utils.clients import create_agent_client


@ai_function  # type: ignore[arg-type]
async def web_search(
    query: Annotated[str, Field(description="Search query to find information on the web")],
) -> str:
    """
    Search the web using Bing Search API and return formatted results.

    Parameters
    ----------
    query : str
        The search query string

    Returns
    -------
    str
        Formatted search results with titles, snippets, and URLs, or error message

    Notes
    -----
    Results are formatted for language model consumption with clear structure:
    - Result count at top
    - Numbered results
    - Title, snippet, URL, and display URL for each result

    Uses a temporary agent with auto-cleanup via async context manager.
    """
    # TODO: Exercise 2 - Implement web search tool using HostedWebSearchTool
    pass


__all__ = ["web_search"]
