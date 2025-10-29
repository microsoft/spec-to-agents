# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for weather tool."""

from unittest.mock import AsyncMock, patch

import pytest

from spec2agent.tools.weather import get_weather_forecast


@pytest.mark.asyncio
async def test_get_weather_forecast_success():
    """Test successful weather forecast retrieval with city name."""
    mock_geocode_response = {
        "results": [{"name": "Seattle", "country": "United States", "latitude": 47.6062, "longitude": -122.3321}]
    }

    mock_weather_response = {
        "daily": {
            "time": ["2025-10-30"],
            "temperature_2m_max": [18.5],
            "temperature_2m_min": [12.3],
            "weathercode": [2],
            "precipitation_probability_max": [30],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock geocoding response
        geocode_mock = AsyncMock()
        geocode_mock.json = AsyncMock(return_value=mock_geocode_response)
        geocode_mock.raise_for_status = AsyncMock()

        # Mock weather response
        weather_mock = AsyncMock()
        weather_mock.json = AsyncMock(return_value=mock_weather_response)
        weather_mock.raise_for_status = AsyncMock()

        mock_client.get = AsyncMock(side_effect=[geocode_mock, weather_mock])

        result = await get_weather_forecast(location="Seattle", days=1)

    assert "Seattle, United States" in result
    assert "partly cloudy" in result
    assert "12.3°C to 18.5°C" in result
    assert "30% chance of precipitation" in result


@pytest.mark.asyncio
async def test_get_weather_forecast_coordinates():
    """Test weather forecast with coordinates."""
    mock_weather_response = {
        "daily": {
            "time": ["2025-10-30"],
            "temperature_2m_max": [20.0],
            "temperature_2m_min": [15.0],
            "weathercode": [0],
            "precipitation_probability_max": [10],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        weather_mock = AsyncMock()
        weather_mock.json = AsyncMock(return_value=mock_weather_response)
        weather_mock.raise_for_status = AsyncMock()

        mock_client.get = AsyncMock(return_value=weather_mock)

        result = await get_weather_forecast(location="47.6062,-122.3321", days=1)

    assert "47.6062°, -122.3321°" in result
    assert "clear sky" in result
    assert "15.0°C to 20.0°C" in result


@pytest.mark.asyncio
async def test_get_weather_forecast_location_not_found():
    """Test error handling when location is not found."""
    mock_geocode_response = {"results": []}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        geocode_mock = AsyncMock()
        geocode_mock.json = AsyncMock(return_value=mock_geocode_response)
        geocode_mock.raise_for_status = AsyncMock()

        mock_client.get = AsyncMock(return_value=geocode_mock)

        result = await get_weather_forecast(location="InvalidCity123", days=1)

    assert "Location 'InvalidCity123' not found" in result


@pytest.mark.asyncio
async def test_get_weather_forecast_invalid_coordinates():
    """Test error handling for invalid coordinate format."""
    result = await get_weather_forecast(location="invalid,coordinates", days=1)

    assert "Error: Invalid coordinates format" in result


@pytest.mark.asyncio
async def test_get_weather_forecast_multiple_days():
    """Test weather forecast for multiple days."""
    mock_geocode_response = {
        "results": [{"name": "London", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278}]
    }

    mock_weather_response = {
        "daily": {
            "time": ["2025-10-30", "2025-10-31", "2025-11-01"],
            "temperature_2m_max": [15.0, 16.0, 14.5],
            "temperature_2m_min": [10.0, 11.0, 9.5],
            "weathercode": [61, 63, 3],
            "precipitation_probability_max": [70, 80, 40],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        geocode_mock = AsyncMock()
        geocode_mock.json = AsyncMock(return_value=mock_geocode_response)
        geocode_mock.raise_for_status = AsyncMock()

        weather_mock = AsyncMock()
        weather_mock.json = AsyncMock(return_value=mock_weather_response)
        weather_mock.raise_for_status = AsyncMock()

        mock_client.get = AsyncMock(side_effect=[geocode_mock, weather_mock])

        result = await get_weather_forecast(location="London", days=3)

    assert "London, United Kingdom" in result
    assert "slight rain" in result
    assert "moderate rain" in result
    assert "overcast" in result
    assert "2025-10-30" in result
    assert "2025-10-31" in result
    assert "2025-11-01" in result
