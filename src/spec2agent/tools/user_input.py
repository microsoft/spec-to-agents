"""User input request tool for human-in-the-loop workflows."""

from typing import Any, Literal


def request_user_input(
    prompt: str,
    context: dict[str, Any],
    request_type: Literal["clarification", "selection", "approval"],
) -> str:
    """
    Request input from the user during workflow execution.

    Use this tool when you need:
    - Clarification on ambiguous requirements
    - User selection between multiple options
    - User approval of recommendations or budgets

    Parameters
    ----------
    prompt : str
        Clear question to ask the user (e.g., "Which venue do you prefer?")
    context : dict[str, Any]
        Supporting information such as venue options, budget breakdown, etc.
    request_type : Literal["clarification", "selection", "approval"]
        Category of the request:
        - "clarification": Missing or ambiguous information
        - "selection": User must choose from options
        - "approval": User must approve/reject a proposal

    Returns
    -------
    str
        Placeholder return value - actual user response is handled by workflow

    Notes
    -----
    This tool is intercepted by HumanInLoopAgentExecutor which emits
    UserElicitationRequest to RequestInfoExecutor for DevUI handling.
    """
    return "User input will be requested"


__all__ = ["request_user_input"]
