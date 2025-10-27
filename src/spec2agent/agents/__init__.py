# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent, Workflow

from spec2agent.agents.budget_analyst.workflow import agent as budget_analyst_agent
from spec2agent.agents.catering_coordinator.workflow import agent as catering_coordinator_agent
from spec2agent.agents.event_coordinator.workflow import agent as event_coordinator_agent
from spec2agent.agents.logistics_manager.workflow import agent as logistics_manager_agent
from spec2agent.agents.venue_specialist.workflow import agent as venue_specialist_agent


def export_entities() -> list[Workflow | ChatAgent]:
    """Export all agents/workflows for registration in DevUI."""
    return [
        budget_analyst_agent,
        catering_coordinator_agent,
        event_coordinator_agent,
        logistics_manager_agent,
        venue_specialist_agent,
    ]
