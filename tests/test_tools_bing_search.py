# Copyright (c) Microsoft. All rights reserved.

"""Tests for Bing Search tool."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

import spec_to_agents.tools.bing_search as bing_search_module


@pytest.fixture(autouse=True)
def reset_web_search_agent():
    """Reset the module-level agent ID cache before and after each test."""
    # Reset before test
    bing_search_module._web_search_agent_id = None
    yield
    # Reset after test to prevent state leakage
    bing_search_module._web_search_agent_id = None


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

    # Mock the client's response
    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        # Setup async context manager
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = 'Found 2 results for "Microsoft Agent Framework"\n\n1. Microsoft Agent Framework\n   Build intelligent multi-agent systems.\n   URL: https://github.com/microsoft/agent-framework'  # noqa: E501

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
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
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = "No results found for query: xyzabc123nonexistent"

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
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
    """Test web search retrieves agent and executes query."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = "Found 2 results"

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("test query")

    assert "Found 2 results" in result


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
    """Test web_search handles API errors gracefully."""
    from spec_to_agents.tools.bing_search import web_search

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        # Make client.run() raise an exception (not agent.run())
        mock_client.run = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        mock_client.create_agent.return_value = mock_agent
        # Mock context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_factory.return_value = mock_client

        result = await web_search("test query")

    assert "Error performing web search" in result
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
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = (
            'Found 1 results for "test"\n\n'
            "1. Test Result\n"
            "   This is a test snippet.\n"
            "   URL: https://example.com/test\n"
            "   Source: example.com/test"
        )

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
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
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = "No results found for query: empty query"

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
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
        mock_agent.id = "test-agent-id"
        mock_response = Mock()
        mock_response.text = (
            'Found 2 results for "test"\n\n'
            "1. Result One\n"
            "   First result snippet.\n\n"
            "2. Result Two\n"
            "   Second result snippet."
        )

        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(return_value=mock_response)
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
async def test_web_search_agent_persistence():
    """Test that agent ID is stored and agent is retrieved by ID on subsequent calls."""
    from spec_to_agents.tools.bing_search import web_search

    # Note: autouse fixture automatically resets _web_search_agent_id before this test

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        # Mock two different clients - one for creation, one for retrieval
        mock_create_client = Mock()
        mock_retrieve_client = Mock()
        mock_agent = Mock()

        # Set the agent ID that will be stored
        mock_agent.id = "test-agent-123"

        response1 = Mock()
        response1.text = "First search result"
        response2 = Mock()
        response2.text = "Second search result"

        # First client creates agent
        mock_create_client.create_agent.return_value = mock_agent
        mock_create_client.__aenter__ = AsyncMock(return_value=mock_create_client)
        mock_create_client.__aexit__ = AsyncMock(return_value=None)

        # Second client retrieves agent by ID and runs queries
        mock_retrieve_client.run = AsyncMock(side_effect=[response1, response2])
        mock_retrieve_client.__aenter__ = AsyncMock(return_value=mock_retrieve_client)
        mock_retrieve_client.__aexit__ = AsyncMock(return_value=None)

        # Track calls to verify correct parameters
        calls = []

        def mock_factory(agent_id=None):
            calls.append(agent_id)
            return mock_create_client if agent_id is None else mock_retrieve_client

        mock_client_factory.side_effect = mock_factory

        # First call - should create agent and store ID
        result1 = await web_search("query 1")
        assert result1 == "First search result"
        assert bing_search_module._web_search_agent_id == "test-agent-123"

        # Second call - should reuse agent ID (retrieve existing agent)
        result2 = await web_search("query 2")
        assert result2 == "Second search result"
        # Agent ID should still be the same
        assert bing_search_module._web_search_agent_id == "test-agent-123"

        # Verify create_agent_client was called with correct parameters
        assert len(calls) == 3  # One for creation, two for retrieval
        # First call creates (agent_id is None)
        assert calls[0] is None
        # Second call retrieves by ID
        assert calls[1] == "test-agent-123"
        # Third call retrieves by ID
        assert calls[2] == "test-agent-123"


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
async def test_web_search_full_lifecycle():
    """
    Integration test verifying complete agent lifecycle.

    Tests:
    - Agent created on first call with proper context manager cleanup
    - Agent ID stored at module level
    - Subsequent calls retrieve agent by ID with new context managers
    - Each context manager properly cleaned up (enters/exits balanced)
    """
    import spec_to_agents.tools.bing_search as bing_search_module
    from spec_to_agents.tools.bing_search import web_search

    # Verify starting with no agent ID
    assert bing_search_module._web_search_agent_id is None

    with (
        patch("spec_to_agents.tools.bing_search.create_agent_client") as mock_client_factory,
        patch("spec_to_agents.tools.bing_search.HostedWebSearchTool"),
    ):
        mock_client = Mock()
        mock_agent = Mock()

        # Track context manager calls to verify cleanup
        enter_count = 0
        exit_count = 0

        async def mock_enter(self):
            nonlocal enter_count
            enter_count += 1
            return mock_client

        async def mock_exit(self, *args):
            nonlocal exit_count
            exit_count += 1
            return

        mock_client.__aenter__ = mock_enter
        mock_client.__aexit__ = mock_exit

        # Mock agent with ID
        mock_agent.id = "persistent-agent-456"

        response1 = Mock()
        response1.text = "First result"
        response2 = Mock()
        response2.text = "Second result"
        response3 = Mock()
        response3.text = "Third result"

        mock_agent.run = AsyncMock(side_effect=[response1, response2, response3])
        mock_client.create_agent.return_value = mock_agent
        mock_client.run = AsyncMock(side_effect=[response1, response2, response3])
        mock_client_factory.return_value = mock_client

        # First call - creates agent
        result1 = await web_search("query 1")
        assert result1 == "First result"
        assert bing_search_module._web_search_agent_id == "persistent-agent-456"
        # One context manager used for creation, one for run
        assert enter_count == 2  # Once for creation, once for run
        assert exit_count == 2

        # Second call - retrieves by ID
        result2 = await web_search("query 2")
        assert result2 == "Second result"
        # Still same agent ID
        assert bing_search_module._web_search_agent_id == "persistent-agent-456"
        # Additional context manager for retrieval
        assert enter_count == 3  # One more for run
        assert exit_count == 3

        # Third call - retrieves by ID again
        result3 = await web_search("query 3")
        assert result3 == "Third result"
        assert bing_search_module._web_search_agent_id == "persistent-agent-456"
        # Another context manager for retrieval
        assert enter_count == 4
        assert exit_count == 4

        # Verify context managers are balanced (proper cleanup)
        assert enter_count == exit_count
