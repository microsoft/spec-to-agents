# Copyright (c) Microsoft. All rights reserved.

from agent_framework import ChatAgent, HostedCodeInterpreterTool
from agent_framework.azure import AzureAIAgentClient

from spec_to_agents.prompts import budget_analyst
from spec_to_agents.workflow.messages import SpecialistOutput


def create_agent(
    client: AzureAIAgentClient,
    code_interpreter: HostedCodeInterpreterTool,
) -> ChatAgent:
    """
    Create Budget Analyst agent for event planning workflow.

    Parameters
    ----------
    client : AzureAIAgentClient
        AI client for agent creation
    code_interpreter : HostedCodeInterpreterTool
        Python code execution tool for financial calculations

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
    return client.create_agent(
        name="BudgetAnalyst",
        instructions=budget_analyst.SYSTEM_PROMPT,
        tools=[code_interpreter],
        response_format=SpecialistOutput,
        store=True,
    )
