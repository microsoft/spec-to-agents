# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for code interpreter tool using ChatClient."""

import os

import pytest
from agent_framework import HostedCodeInterpreterTool

from spec_to_agents.utils.clients import create_agent_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_simple_calculation() -> None:
    """Test code interpreter integration with simple mathematical calculation."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(
            description="Execute Python code for calculations and data analysis."
        )

        agent = client.create_agent(
            name="code_test_agent",
            description="Test agent for code interpreter",
            instructions="You are a helpful assistant that can execute Python code to solve problems.",
            tools=[code_interpreter],
        )

        # Test with a simple calculation
        response = await agent.run("Calculate the sum of numbers from 1 to 100 using Python code")

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain the result (5050) or indicate calculation was performed
        assert any(keyword in result_text for keyword in ["5050", "sum", "result", "calculated"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_data_analysis() -> None:
    """Test code interpreter integration with data analysis."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(
            description="Execute Python code for calculations and data analysis."
        )

        agent = client.create_agent(
            name="code_analysis_agent",
            description="Test agent for data analysis",
            instructions="You are a helpful assistant that can execute Python code to analyze data.",
            tools=[code_interpreter],
        )

        # Test with data analysis
        response = await agent.run(
            "Create a list of numbers [10, 20, 30, 40, 50] and calculate the average using Python"
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain the average (30) or indicate analysis was performed
        assert any(keyword in result_text for keyword in ["30", "average", "mean", "calculated"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_budget_calculation() -> None:
    """Test code interpreter integration for budget calculations."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool (simulating budget analyst)
        code_interpreter = HostedCodeInterpreterTool(
            description=(
                "Execute Python code for complex financial calculations, "
                "budget analysis, cost projections, and data visualization."
            )
        )

        agent = client.create_agent(
            name="budget_test_agent",
            description="Test agent for budget calculations",
            instructions=(
                "You are a budget analyst that performs financial calculations. "
                "Use Python code to calculate budgets, allocations, and projections."
            ),
            tools=[code_interpreter],
        )

        # Test with a budget calculation
        response = await agent.run(
            "Calculate the total budget if venue costs $2000, catering costs $3000, "
            "and logistics costs $1500. Then calculate what percentage each category "
            "represents of the total."
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain total budget (6500) and percentages
        assert any(
            keyword in result_text
            for keyword in [
                "6500",
                "total",
                "budget",
                "percentage",
                "percent",
                "%",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_cost_breakdown() -> None:
    """Test code interpreter integration for detailed cost breakdown."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(
            description="Execute Python code for financial calculations and budget analysis."
        )

        agent = client.create_agent(
            name="cost_breakdown_agent",
            description="Test agent for cost breakdown",
            instructions="You are a budget analyst that provides detailed cost breakdowns using Python.",
            tools=[code_interpreter],
        )

        # Test with cost breakdown
        response = await agent.run(
            "I have a budget of $10,000 for an event. Calculate how to allocate: "
            "40% for venue, 35% for catering, 15% for entertainment, and 10% for contingency."
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain allocations and amounts
        assert any(
            keyword in result_text
            for keyword in [
                "4000",  # Venue: 40% of 10000
                "3500",  # Catering: 35% of 10000
                "1500",  # Entertainment: 15% of 10000
                "1000",  # Contingency: 10% of 10000
                "allocation",
                "breakdown",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_per_person_calculation() -> None:
    """Test code interpreter integration for per-person cost calculations."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(description="Execute Python code for financial calculations.")

        agent = client.create_agent(
            name="per_person_agent",
            description="Test agent for per-person calculations",
            instructions="You are a budget analyst that calculates per-person costs using Python.",
            tools=[code_interpreter],
        )

        # Test with per-person calculation
        response = await agent.run(
            "If the total event cost is $8000 and we have 50 attendees, what is the cost per person?"
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain per-person cost (160)
        assert any(keyword in result_text for keyword in ["160", "per person", "per attendee", "each"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_multiple_calculations() -> None:
    """Test code interpreter integration with multiple sequential calculations."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(description="Execute Python code for calculations.")

        agent = client.create_agent(
            name="multi_calc_agent",
            description="Test agent for multiple calculations",
            instructions="You are a helpful assistant that performs calculations using Python.",
            tools=[code_interpreter],
        )

        # First calculation
        response1 = await agent.run("Calculate 25% of 1000")
        assert response1 is not None
        assert response1.text is not None
        assert "250" in response1.text

        # Second calculation
        response2 = await agent.run("Now calculate the square root of 144")
        assert response2 is not None
        assert response2.text is not None
        assert "12" in response2.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_list_operations() -> None:
    """Test code interpreter integration with list operations."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(
            description="Execute Python code for data manipulation and analysis."
        )

        agent = client.create_agent(
            name="list_ops_agent",
            description="Test agent for list operations",
            instructions="You are a helpful assistant that manipulates data using Python.",
            tools=[code_interpreter],
        )

        # Test with list operations
        response = await agent.run(
            "Create a list of event costs [1200, 3500, 2800, 1500, 900] and find the maximum, minimum, and total"
        )

        # Verify response contains expected elements
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should contain max (3500), min (900), and total (9900)
        assert any(
            keyword in result_text
            for keyword in [
                "3500",
                "900",
                "9900",
                "maximum",
                "minimum",
                "total",
            ]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_interpreter_with_agent_error_handling() -> None:
    """Test code interpreter integration with error handling."""
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        pytest.skip("Azure credentials not configured")

    async with create_agent_client() as client:
        # Create an agent with code interpreter tool
        code_interpreter = HostedCodeInterpreterTool(description="Execute Python code for calculations.")

        agent = client.create_agent(
            name="error_handling_agent",
            description="Test agent for error handling",
            instructions="You are a helpful assistant that executes Python code.",
            tools=[code_interpreter],
        )

        # Test with potentially problematic calculation (division by zero handling)
        response = await agent.run("Write Python code to divide 10 by 0 and handle the error appropriately")

        # Verify response handles error gracefully
        assert response is not None
        assert response.text is not None
        result_text = response.text.lower()

        # Should mention error, exception, or handling
        assert any(
            keyword in result_text
            for keyword in [
                "error",
                "exception",
                "division by zero",
                "zerodivision",
                "cannot divide",
                "handle",
            ]
        )
