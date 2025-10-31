# Copyright (c) Microsoft. All rights reserved.

"""Tests for Bing Search tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_web_search_agent():
    """Reset the module-level agent cache before each test."""
    import spec_to_agents.tools.bing_search as bing_search_module

    bing_search_module._web_search_agent = None
    bing_search_module._agent_client = None
    yield
    # Cleanup after test
    bing_search_module._web_search_agent = None
    bing_search_module._agent_client = None


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_success():
    """Test successful web search with results."""
    from spec_to_agents.tools.bing_search import web_search

    # Mock the agent's response
    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        # Setup async context manager
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = 'Found 2 results for "Microsoft Agent Framework"\n\n1. Microsoft Agent Framework\n   Build intelligent multi-agent systems.\n   URL: https://github.com/microsoft/agent-framework'  # noqa: E501

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("Microsoft Agent Framework")

    assert 'Found 2 results for "Microsoft Agent Framework"' in result
    assert "Microsoft Agent Framework" in result
    assert "github.com/microsoft/agent-framework" in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_no_results():
    """Test web search with no results."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = "No results found for query: xyzabc123nonexistent"

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("xyzabc123nonexistent")

    assert "No results found" in result or "xyzabc123nonexistent" in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_with_custom_count():
    """Test web search creates agent with web search tool."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = "Found 2 results"

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("test query")

    assert "Found 2 results" in result
    # Verify agent was created with proper configuration
    mock_client.create_agent.assert_called_once()


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_api_error():
    """Test web search handles API errors gracefully."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        # Make agent.run() raise an exception
        mock_agent.run = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        mock_client.create_agent.return_value = mock_agent
        mock_client_factory.return_value = mock_client

        result = await web_search("test query")

    assert "Error performing web search" in result
    assert "Exception" in result
    assert "API rate limit exceeded" in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_formatting():
    """Test that results are properly formatted for LM consumption."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = (
            'Found 1 results for "test"\n\n'
            "1. Test Result\n"
            "   This is a test snippet.\n"
            "   URL: https://example.com/test\n"
            "   Source: example.com/test"
        )

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("test")

    # Check formatting structure
    assert 'Found 1 results for "test"' in result
    assert "1. Test Result" in result
    assert "This is a test snippet." in result
    assert "https://example.com/test" in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_empty_results_list():
    """Test web search when results list is empty."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = "No results found for query: empty query"

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("empty query")

    assert "No results found" in result or "empty query" in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_result_numbering():
    """Test that results are properly numbered starting from 1."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.text = (
            'Found 2 results for "test"\n\n'
            "1. Result One\n"
            "   First result snippet.\n\n"
            "2. Result Two\n"
            "   Second result snippet."
        )

        mock_agent.run = AsyncMock(return_value=mock_response)
        mock_client.create_agent.return_value = mock_agent
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("test")

    assert "1. " in result
    assert "2. " in result
    # Should not have 0. or 3. since we have 2 results
    assert "0. " not in result
    assert "3. " not in result


@pytest.mark.asyncio
@patch.dict(
    "os.environ",
    {
        "BING_SUBSCRIPTION_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test_key",
    },
    clear=False,
)
async def test_web_search_agent_reuse():
    """Test that agent is created once and reused across multiple calls."""
    # Explicitly disable the fixture for this test to verify caching
    import spec_to_agents.tools.bing_search as bing_search_module

    bing_search_module._web_search_agent = None
    bing_search_module._agent_client = None

    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()

        # Create different responses for each call
        response1 = Mock()
        response1.text = "First search result"
        response2 = Mock()
        response2.text = "Second search result"

        mock_agent.run = AsyncMock(side_effect=[response1, response2])
        mock_client.create_agent.return_value = mock_agent
        mock_client_factory.return_value = mock_client

        # First call - should create agent
        result1 = await web_search("query 1")
        assert result1 == "First search result"
        assert mock_client.create_agent.call_count == 1

        # Second call - should reuse agent (no new creation)
        result2 = await web_search("query 2")
        assert result2 == "Second search result"
        # Agent should still only be created once
        assert mock_client.create_agent.call_count == 1
        # But agent.run should be called twice
        assert mock_agent.run.call_count == 2
