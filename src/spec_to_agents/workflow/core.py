# Copyright (c) Microsoft. All rights reserved.

"""
Workflow core module - re-exports for backward compatibility.

The workflow builder has been moved to src/spec_to_agents/agents/event_planning_workflow.py.
This module maintains backward compatibility by re-exporting the workflow builder
and lazy-loading the workflow instance.
"""

from agent_framework import Workflow

from spec_to_agents.workflow.event_planning_workflow import build_event_planning_workflow

# Declare lazy-loaded attribute for type checking
workflow: Workflow

__all__ = ["build_event_planning_workflow", "workflow"]

# Private cache for lazy initialization
_workflow_cache: Workflow | None = None


def __getattr__(name: str) -> Workflow:
    """
    Lazy initialization hook for the workflow module attribute.

    This enables lazy loading of the workflow instance to avoid asyncio.run()
    during module import, which causes issues with MCP tool lifecycle management.

    Parameters
    ----------
    name : str
        The attribute name being accessed

    Returns
    -------
    Workflow
        The workflow instance

    Raises
    ------
    AttributeError
        If the attribute name is not 'workflow'
    """
    if name == "workflow":
        global _workflow_cache
        if _workflow_cache is None:
            _workflow_cache = build_event_planning_workflow()
        return _workflow_cache
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
