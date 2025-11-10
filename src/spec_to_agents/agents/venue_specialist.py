# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from agent_framework import BaseChatClient, ChatAgent, ToolProtocol
from dependency_injector.wiring import Provide, inject

from spec_to_agents.models.messages import SpecialistOutput
from spec_to_agents.prompts import venue_specialist
from spec_to_agents.tools import web_search


@inject
def create_agent(
    client: BaseChatClient = Provide["client"],
    global_tools: dict[str, ToolProtocol] = Provide["global_tools"],
    model_config: dict[str, Any] = Provide["model_config"],
) -> ChatAgent:
    """
    Create Venue Specialist agent for event planning workflow.

    IMPORTANT: This function uses dependency injection. ALL parameters are
    automatically injected via the DI container. DO NOT pass any arguments
    when calling this function.

    Usage
    -----
    After container is wired:
        agent = venue_specialist.create_agent()  # No arguments - DI handles it!

    Parameters
    ----------
    client : BaseChatClient
        Automatically injected via Provide["client"]
    global_tools : dict[str, ToolProtocol]
        Automatically injected via Provide["global_tools"]

    Returns
    -------
    ChatAgent
        Configured venue specialist agent with web search capabilities

    Notes
    -----
    Uses custom web_search @ai_function instead of HostedWebSearchTool for
    better control over response formatting for language models.
    """
    # TODO: Exercise 1 - Create Venue Specialist agent with web search capability
    pass
