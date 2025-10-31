# Copyright (c) Microsoft. All rights reserved.

"""Tests for Bing Search tool."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_search_response():
    """Create a mock Bing Search response."""
    response = MagicMock()
    response.web_pages = MagicMock()
    response.web_pages.value = [
        MagicMock(
            name="Microsoft Agent Framework",
            snippet="Build intelligent multi-agent systems with Microsoft Agent Framework.",
            url="https://github.com/microsoft/agent-framework",
            display_url="github.com/microsoft/agent-framework",
        ),
        MagicMock(
            name="Agent Framework Documentation",
            snippet="Complete documentation for Agent Framework including tutorials and API reference.",
            url="https://docs.microsoft.com/agent-framework",
            display_url="docs.microsoft.com/agent-framework",
        ),
    ]
    return response


@pytest.fixture
def mock_empty_response():
    """Create a mock empty Bing Search response."""
    response = MagicMock()
    response.web_pages = None
    return response


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_success(mock_search_response):
    """Test successful web search with results."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    with patch.object(_get_client().web, "search", return_value=mock_search_response):
        result = await web_search("Microsoft Agent Framework")

    assert 'Found 2 results for "Microsoft Agent Framework"' in result
    assert "Microsoft Agent Framework" in result
    assert "Build intelligent multi-agent systems" in result
    assert "github.com/microsoft/agent-framework" in result
    assert "Agent Framework Documentation" in result
    assert "docs.microsoft.com/agent-framework" in result
    assert "1." in result
    assert "2." in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_no_results(mock_empty_response):
    """Test web search with no results."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    with patch.object(_get_client().web, "search", return_value=mock_empty_response):
        result = await web_search("xyzabc123nonexistent")

    assert "No results found for query: xyzabc123nonexistent" in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_with_custom_count(mock_search_response):
    """Test web search with custom result count."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    with patch.object(_get_client().web, "search", return_value=mock_search_response) as mock_search:
        result = await web_search("test query", count=5)

    # Verify count parameter was passed
    mock_search.assert_called_once_with(query="test query", count=5)
    assert "Found 2 results" in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_api_error():
    """Test web search handles API errors gracefully."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    with patch.object(_get_client().web, "search", side_effect=Exception("API rate limit exceeded")):
        result = await web_search("test query")

    assert "Error performing web search" in result
    assert "Exception" in result
    assert "API rate limit exceeded" in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_formatting():
    """Test that results are properly formatted for LM consumption."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    result_obj = MagicMock()
    result_obj.name = "Test Result"
    result_obj.snippet = "This is a test snippet."
    result_obj.url = "https://example.com/test"
    result_obj.display_url = "example.com/test"

    response = MagicMock()
    response.web_pages = MagicMock()
    response.web_pages.value = [result_obj]

    with patch.object(_get_client().web, "search", return_value=response):
        result = await web_search("test")

    # Check formatting structure
    lines = result.split("\n")
    assert 'Found 1 results for "test"' in lines[0]
    assert "1. Test Result" in result
    assert "   This is a test snippet." in result
    assert "   URL: https://example.com/test" in result
    assert "   Source: example.com/test" in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_empty_results_list():
    """Test web search when results list is empty."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    response = MagicMock()
    response.web_pages = MagicMock()
    response.web_pages.value = []

    with patch.object(_get_client().web, "search", return_value=response):
        result = await web_search("empty query")

    assert "No results found for query: empty query" in result


@pytest.mark.asyncio
@patch.dict("os.environ", {"BING_SEARCH_API_KEY": "test_api_key"})
async def test_web_search_result_numbering(mock_search_response):
    """Test that results are properly numbered starting from 1."""
    from spec_to_agents.tools.bing_search import _get_client, web_search

    with patch.object(_get_client().web, "search", return_value=mock_search_response):
        result = await web_search("test")

    assert "\n1. " in result
    assert "\n\n2. " in result
    # Should not have 0. or 3. since we have 2 results
    assert "\n0. " not in result
    assert "\n\n3. " not in result
