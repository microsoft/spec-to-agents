# Copyright (c) Microsoft. All rights reserved.

"""Custom message types for workflow human-in-the-loop interactions."""

from dataclasses import dataclass, field
from typing import Any

from agent_framework import RequestInfoMessage


@dataclass(kw_only=True)
class UserElicitationRequest(RequestInfoMessage):
    """
    General-purpose request for user input during event planning.

    This message type allows any specialist agent to request clarification,
    approval, or selection from the user during workflow execution.

    Attributes
    ----------
    prompt : str
        Clear question or instruction for the user
    context : dict[str, Any]
        Contextual information such as options, data, constraints
    request_type : str
        Category of request: "clarification", "selection", or "approval"

    Examples
    --------
    >>> UserElicitationRequest(
    ...     prompt="Which venue do you prefer?",
    ...     context={"venues": [{"name": "Venue A", "capacity": 50}]},
    ...     request_type="selection"
    ... )
    """

    prompt: str
    context: dict[str, Any]
    request_type: str


__all__ = ["UserElicitationRequest"]
