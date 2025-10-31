# Copyright (c) Microsoft. All rights reserved.

"""Bing Web Search tool using Azure Cognitive Services."""

import os
from typing import Annotated

from agent_framework import ai_function
from azure.cognitiveservices.search.websearch import WebSearchClient
from msrest.authentication import CognitiveServicesCredentials
from pydantic import Field

# Get API key from environment
_API_KEY = os.getenv("BING_SEARCH_API_KEY")
if not _API_KEY:
    raise ValueError(
        "BING_SEARCH_API_KEY environment variable not set. "
        "Obtain an API key from Azure Portal (Bing Search v7 resource) and add to .env file."
    )

# Initialize client
_client = WebSearchClient(
    endpoint="https://api.bing.microsoft.com",
    credentials=CognitiveServicesCredentials(_API_KEY),
)


@ai_function
async def web_search(
    query: Annotated[str, Field(description="Search query to find information on the web")],
    count: Annotated[int, Field(description="Number of search results to return (1-50)", ge=1, le=50)] = 10,
) -> str:
    """
    Search the web using Bing Search API and return formatted results.

    Parameters
    ----------
    query : str
        The search query string
    count : int, optional
        Number of results to return (1-50), default is 10

    Returns
    -------
    str
        Formatted search results with titles, snippets, and URLs, or error message

    Notes
    -----
    Results are formatted for language model consumption with clear structure:
    - Result count at top
    - Numbered results
    - Title, snippet, URL, and source for each result
    """
    try:
        # Execute search
        response = _client.web.search(query=query, count=count)

        # Check if we have results
        if not response.web_pages or not response.web_pages.value:
            return f"No results found for query: {query}"

        # Format results for LM consumption
        results = []
        for i, result in enumerate(response.web_pages.value, start=1):
            result_text = f"{i}. {result.name}\n"
            result_text += f"   {result.snippet}\n"
            result_text += f"   URL: {result.url}\n"
            result_text += f"   Source: {result.display_url}"
            results.append(result_text)

        # Build final response
        formatted_response = f'Found {len(results)} results for "{query}":\n\n'
        formatted_response += "\n\n".join(results)

        return formatted_response

    except Exception as e:
        # Handle API errors gracefully
        error_type = type(e).__name__
        return f"Error performing web search: {error_type} - {e!s}"


__all__ = ["web_search"]
