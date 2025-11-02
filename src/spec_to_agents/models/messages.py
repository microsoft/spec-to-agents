# Copyright (c) Microsoft. All rights reserved.

"""Custom message types for workflow human-in-the-loop interactions."""

from dataclasses import dataclass, field
from typing import Any

from agent_framework import ChatMessage
from pydantic import BaseModel, Field


@dataclass
class HumanFeedbackRequest:
    """
    Request for human input during event planning workflow.

    This dataclass is used with ctx.request_info() to pause the workflow
    and request clarification, selection, or approval from the user.

    Attributes
    ----------
    prompt : str
        Clear question or instruction for the user
    context : dict[str, Any]
        Supporting information such as options, data, constraints
    request_type : str
        Category of request (e.g., "clarification", "selection", "approval")
    requesting_agent : str
        ID of the specialist agent that requested this input
    conversation : list[ChatMessage]
        Full conversation history up to this point, used to restore context
        when routing back to the requesting agent after human feedback

    Examples
    --------
    >>> HumanFeedbackRequest(
    ...     prompt="Which venue do you prefer?",
    ...     context={"venues": [{"name": "Venue A", "capacity": 50}]},
    ...     request_type="selection",
    ...     requesting_agent="venue",
    ...     conversation=[ChatMessage(Role.USER, text="Plan a party")],
    ... )
    """

    prompt: str
    context: dict[str, Any]
    request_type: str
    requesting_agent: str
    conversation: list[ChatMessage] = field(default_factory=list)  # type: ignore


class SupervisorDecision(BaseModel):
    """
    Structured output from supervisor agent for routing decisions.

    The supervisor evaluates conversation history and decides which
    participant to route to next, whether to request user input,
    or whether the workflow is complete.

    Workflow completion occurs when next_agent=None AND user_input_needed=False.

    Examples
    --------
    Route to participant:
    >>> SupervisorDecision(next_agent="venue", user_input_needed=False)

    Request user input:
    >>> SupervisorDecision(
    ...     next_agent=None,
    ...     user_input_needed=True,
    ...     user_prompt="Which venue do you prefer?",
    ... )

    Workflow complete:
    >>> SupervisorDecision(next_agent=None, user_input_needed=False)
    """

    next_agent: str | None = Field(
        description=("ID of next participant to route to or None if workflow is complete and ready for final synthesis")
    )
    user_input_needed: bool = Field(default=False, description="Whether user input is required before continuing")
    user_prompt: str | None = Field(default=None, description="Question to ask user if user_input_needed=True")


__all__ = ["HumanFeedbackRequest", "SupervisorDecision"]
