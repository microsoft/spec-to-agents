# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, HostedCodeInterpreterTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import budget_analyst


def create_agent(client: AzureAIAgentClient, mcp_tool: MCPStdioTool | None) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured budget analyst agent with code interpreter capabilities

    Notes
    -----
    Budget analyst returns natural text responses with budget calculations
    and explanations. The coordinator parses these responses to make routing
    decisions.
    """
    # Create hosted tools
    code_interpreter = HostedCodeInterpreterTool(
        description=(
            "Execute Python code for complex financial calculations, budget analysis, "
            "cost projections, and data visualization. Creates a scratchpad for "
            "intermediate calculations and maintains calculation history."
        ),
    )

    tools = [code_interpreter]
    if mcp_tool is not None:
        tools.append(mcp_tool)  # type: ignore

    return client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=tools,
        store=True,
    )
