# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, HostedCodeInterpreterTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.agents.factory import create_budget_analyst_agent


def create_agent(
    client: AzureAIAgentClient, code_interpreter: HostedCodeInterpreterTool, mcp_tool: MCPStdioTool | None
) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Deprecated: Use create_budget_analyst_agent from agents.factory instead.
    This function is maintained for backward compatibility.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    code_interpreter : HostedCodeInterpreterTool
        Python code execution tool for financial calculations
    mcp_tool : MCPStdioTool | None, optional
        Sequential thinking tool for complex reasoning.
        If None, coordinator operates without MCP tool assistance.

    Returns
    -------
    ChatAgent
        Configured budget analyst agent with code interpreter capabilities

    Notes
    -----
    MCP sequential-thinking tool was removed because it interferes with
    structured output generation (SpecialistOutput). The agent would complete
    its thinking process but fail to return a final structured response,
    causing ValueError in the workflow.

    User input is handled through SpecialistOutput.user_input_needed field,
    not through a separate tool.
    """
    return create_budget_analyst_agent(client, code_interpreter, mcp_tool)
