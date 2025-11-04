# Copyright (c) Microsoft. All rights reserved.

"""Custom message types for workflow human-in-the-loop interactions."""

from dataclasses import dataclass, field
from typing import Any

from agent_framework import ChatMessage


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


__all__ = ["HumanFeedbackRequest"]
