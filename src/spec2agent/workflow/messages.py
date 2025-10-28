# Copyright (c) Microsoft. All rights reserved.

"""
Custom RequestInfoMessage types for event planning workflow user handoff.

These message types enable agents to request user clarification, approval,
or selection during workflow execution. DevUI automatically handles these
requests by prompting the user and routing responses back to the workflow.
"""

from dataclasses import dataclass
from typing import Any

from agent_framework import RequestInfoMessage


@dataclass
class UserElicitationRequest(RequestInfoMessage):
    """General-purpose request for user input during event planning.

    This message type allows any specialist agent to request clarification,
    approval, or selection from the user during workflow execution.

    Parameters
    ----------
    prompt : str
        Question or instruction for the user
    context : dict[str, Any]
        Contextual information such as options, data, or recommendations
    request_type : str
        Category of request: "venue_selection", "budget_approval",
        "catering_approval", "logistics_confirmation", or "general_clarification"
    """

    prompt: str
    context: dict[str, Any]
    request_type: str


@dataclass
class VenueSelectionRequest(RequestInfoMessage):
    """Request user to select preferred venue from options.

    Used when the Venue Specialist identifies multiple viable venues
    and needs the user to make a selection based on their preferences.

    Parameters
    ----------
    prompt : str
        Question asking user to select venue
    venue_options : list[dict[str, Any]]
        List of venue recommendations with details (name, capacity, location, cost, pros/cons)
    """

    prompt: str
    venue_options: list[dict[str, Any]]


@dataclass
class BudgetApprovalRequest(RequestInfoMessage):
    """Request user approval or modification of budget allocation.

    Used when the Budget Analyst creates a budget breakdown and needs
    user approval or wants to allow adjustments.

    Parameters
    ----------
    prompt : str
        Question asking for budget approval
    proposed_budget : dict[str, float]
        Budget breakdown by category (venue, catering, logistics, etc.)
    """

    prompt: str
    proposed_budget: dict[str, float]


@dataclass
class CateringApprovalRequest(RequestInfoMessage):
    """Request user approval of catering menu and dietary considerations.

    Used when the Catering Coordinator proposes menu options and needs
    user confirmation or preference selection.

    Parameters
    ----------
    prompt : str
        Question asking for catering approval or selection
    menu_options : list[dict[str, Any]]
        List of menu options with details (cuisine, style, dietary accommodations)
    dietary_considerations : list[str]
        Dietary requirements being addressed
    """

    prompt: str
    menu_options: list[dict[str, Any]]
    dietary_considerations: list[str]


__all__ = [
    "BudgetApprovalRequest",
    "CateringApprovalRequest",
    "UserElicitationRequest",
    "VenueSelectionRequest",
]
