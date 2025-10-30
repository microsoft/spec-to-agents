# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

from agent_framework import ChatAgent, HostedCodeInterpreterTool, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts import budget_analyst
from spec_to_agents.prompts.budget_analyst import SYSTEM_PROMPT
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    code_interpreter: HostedCodeInterpreterTool,
    mcp_tool: MCPStdioTool,
    request_user_input: Callable[..., str],
) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    code_interpreter : HostedCodeInterpreterTool
        Python code execution tool for financial calculations
    mcp_tool : MCPStdioTool
        Sequential thinking tool for complex reasoning
    request_user_input : Callable[..., str]
        Tool for requesting user input/clarification

    Returns
    -------
    ChatAgent
        Configured budget analyst agent with code interpreter capabilities
    """
    return client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[code_interpreter, mcp_tool, request_user_input],
        response_format=SpecialistOutput,
        store=True,
    )


agent = get_chat_client().create_agent(
    name="BudgetAnalystAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={
        "allow_multiple_tool_calls": True,
        "reasoning": {"effort": "minimal", "summary": "concise"},
    },
)

__all__ = ["agent", "create_agent"]
