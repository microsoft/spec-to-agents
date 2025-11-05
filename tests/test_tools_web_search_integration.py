# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for web search tool using ChatClient."""

import os

import pytest

from spec_to_agents.tools.bing_search import web_search
from spec_to_agents.utils.clients import create_agent_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_general_query() -> None:
    """Test web search integration with agent using general query."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool
        agent = client.create_agent(
            name="search_test_agent",
            description="Test agent for web search",
            instructions="You are a helpful assistant that can search the web for information.",
            tools=[web_search],
        )

        # Test with a general search query
        response = await agent.run("Search the web for information about Microsoft Agent Framework")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain information about the framework or indicate search was performed
        assert any(
            keyword in result_text
            for keyword in [
                "microsoft",
                "agent",
                "framework",
                "search",
                "found",
                "results",
                "information",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_specific_query() -> None:
    """Test web search integration with agent using specific query."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool
        agent = client.create_agent(
            name="search_specific_agent",
            description="Test agent for specific web searches",
            instructions="You are a helpful assistant that can search the web for information.",
            tools=[web_search],
        )

        # Test with a specific query
        response = await agent.run("Search for the latest Azure AI updates")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain azure-related information or search results
        assert any(keyword in result_text for keyword in ["azure", "ai", "search", "found", "results"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_venue_query() -> None:
    """Test web search integration for venue-related queries."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool (simulating venue specialist)
        agent = client.create_agent(
            name="venue_search_agent",
            description="Test agent for venue searches",
            instructions=(
                "You are a venue specialist that searches for event venues. Help find appropriate venues for events."
            ),
            tools=[web_search],
        )

        # Test with a venue search query
        response = await agent.run("Find conference venues in Seattle that can accommodate 100 people")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain venue or Seattle-related information
        assert any(
            keyword in result_text for keyword in ["seattle", "venue", "conference", "space", "location", "accommodate"]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_catering_query() -> None:
    """Test web search integration for catering-related queries."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool (simulating catering coordinator)
        agent = client.create_agent(
            name="catering_search_agent",
            description="Test agent for catering searches",
            instructions=(
                "You are a catering coordinator that searches for catering services. "
                "Help find appropriate catering options for events."
            ),
            tools=[web_search],
        )

        # Test with a catering search query
        response = await agent.run("Find catering services in San Francisco for a corporate event with 50 people")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain catering or food-related information
        assert any(
            keyword in result_text
            for keyword in [
                "catering",
                "food",
                "service",
                "san francisco",
                "corporate",
                "event",
                "menu",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_obscure_query() -> None:
    """Test web search integration with agent handling obscure query."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool
        agent = client.create_agent(
            name="search_obscure_agent",
            description="Test agent for handling obscure queries",
            instructions="You are a helpful assistant that can search the web for information.",
            tools=[web_search],
        )

        # Test with an obscure query
        response = await agent.run("Search for xyzabc123nonexistentterm456 qwertyuiop asdfghjkl zxcvbnm impossible")

        # Verify response handles the query (agent should respond in some way)
        assert response is not None
        assert response.text is not None
        # Agent should provide some response, even if it's explaining lack of results
        assert len(response.text) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_multiple_queries() -> None:
    """Test web search integration with multiple sequential queries."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool
        agent = client.create_agent(
            name="search_multiple_agent",
            description="Test agent for multiple searches",
            instructions="You are a helpful assistant that can search the web for information.",
            tools=[web_search],
        )

        # First query
        response1 = await agent.run("Search for Python programming language")
        assert response1 is not None
        assert response1.text is not None
        assert "python" in response1.text.lower()

        # Second query
        response2 = await agent.run("Now search for JavaScript frameworks")
        assert response2 is not None
        assert response2.text is not None
        assert "javascript" in response2.text.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_search_with_agent_complex_query() -> None:
    """Test web search integration with complex multi-part query."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with web search tool
        agent = client.create_agent(
            name="search_complex_agent",
            description="Test agent for complex searches",
            instructions="You are a helpful assistant that can search the web for information.",
            tools=[web_search],
        )

        # Test with a complex query
        response = await agent.run(
            "Search for best practices for organizing corporate events in 2025, "
            "including venue selection and catering options"
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain information about events, venues, or catering
        assert any(
            keyword in result_text
            for keyword in [
                "event",
                "venue",
                "catering",
                "corporate",
                "best practices",
                "organize",
            ]
        )
