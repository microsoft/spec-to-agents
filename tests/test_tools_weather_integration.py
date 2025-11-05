# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for weather tool using ChatClient."""

import os

import pytest

from spec_to_agents.tools.weather import get_weather_forecast
from spec_to_agents.utils.clients import create_agent_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_tool_with_agent_real_city() -> None:
    """Test weather tool integration with agent using real city lookup."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with the weather tool
        agent = client.create_agent(
            name="weather_test_agent",
            description="Test agent for weather tool",
            instructions="You are a helpful assistant that provides weather information.",
            tools=[get_weather_forecast],
        )

        # Test with a real city
        response = await agent.run("What's the weather forecast for Seattle for the next 3 days?")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should mention Seattle or location
        assert any(keyword in result_text for keyword in ["seattle", "weather", "forecast"])

        # Should contain temperature or weather-related terms
        assert any(
            keyword in result_text
            for keyword in [
                "temperature",
                "°c",
                "celsius",
                "cloudy",
                "sunny",
                "rain",
                "clear",
                "precipitation",
                "degrees",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_tool_with_agent_coordinates() -> None:
    """Test weather tool integration with agent using coordinates."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with the weather tool
        agent = client.create_agent(
            name="weather_test_agent_coords",
            description="Test agent for weather tool with coordinates",
            instructions="You are a helpful assistant that provides weather information.",
            tools=[get_weather_forecast],
        )

        # Test with coordinates (San Francisco)
        response = await agent.run("What's the weather at coordinates 37.7749,-122.4194?")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain weather-related information
        assert any(
            keyword in result_text
            for keyword in [
                "weather",
                "temperature",
                "°c",
                "celsius",
                "forecast",
                "cloudy",
                "sunny",
                "rain",
                "clear",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_tool_with_agent_obscure_location() -> None:
    """Test weather tool integration with agent handling obscure location request."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with the weather tool
        agent = client.create_agent(
            name="weather_test_agent_obscure",
            description="Test agent for weather tool with obscure locations",
            instructions="You are a helpful assistant that provides weather information.",
            tools=[get_weather_forecast],
        )

        # Test with obscure/invalid location
        response = await agent.run("What's the weather in XYZInvalidCity12345?")

        # Verify response handles request gracefully (agent should respond in some way)
        assert response is not None
        assert response.text is not None
        # Agent should provide some response, even if it's explaining it can't find the location
        assert len(response.text) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_tool_with_agent_multiple_days() -> None:
    """Test weather tool integration with agent for multi-day forecast."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with the weather tool
        agent = client.create_agent(
            name="weather_test_agent_multiday",
            description="Test agent for multi-day weather forecasts",
            instructions="You are a helpful assistant that provides weather information.",
            tools=[get_weather_forecast],
        )

        # Test with multi-day forecast request
        response = await agent.run("Give me a 5-day weather forecast for London")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should mention London or location
        assert any(keyword in result_text for keyword in ["london", "weather", "forecast"])

        # Should contain multiple days of information
        # At least some weather-related terms should appear
        assert any(
            keyword in result_text
            for keyword in [
                "temperature",
                "°c",
                "celsius",
                "cloudy",
                "sunny",
                "rain",
                "clear",
                "precipitation",
            ]
        )
