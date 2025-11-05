# Copyright (c) Microsoft. All rights reserved.

"""AutoHandoffBuilder - HandoffBuilder with automatic coordinator creation."""

from typing import Sequence, override

from agent_framework import AgentProtocol, BaseChatClient, Executor
from agent_framework._workflows._handoff import HandoffBuilder


class AutoHandoffBuilder(HandoffBuilder):
    """Extended HandoffBuilder that automatically creates a coordinator agent if not explicitly set."""

    @override
    def set_coordinator(self, agent: str | BaseChatClient | AgentProtocol | Executor) -> "HandoffBuilder":
        if isinstance(agent, BaseChatClient):
            """Create coordinator agent from participant descriptions and configure builder."""
            if not self._executors:
                raise ValueError(
                    "Cannot auto-create coordinator with no participants. Call .participants([...]) before .build()."
                )

            # Extract participant descriptions for coordinator instructions
            participant_descriptions: list[str] = []
            for exec_id, executor in self._executors.items():
                # Get agent from executor
                specialist_agent = getattr(executor, "_agent", None)
                description = (
                    getattr(specialist_agent, "description", None) if agent else f"Handoff to the {exec_id} agent."
                )

                participant_descriptions.append(f"- Name: **{exec_id}**, Description: {description}")

            participants_description = "Available participants:\n\n" + "\n".join(participant_descriptions)

            # Use default template
            from spec_to_agents.prompts.coordinator import COORDINATOR_SYSTEM_PROMPT_TEMPLATE

            instructions = COORDINATOR_SYSTEM_PROMPT_TEMPLATE.format(
                coordinator_name=self._name,
                participants_description=participants_description,
            )

            # Create coordinator agent using the provided client
            coordinator = agent.create_agent(name=self._name, description=self._description, instructions=instructions)

            # Register coordinator and set as starting agent
            # Note: coordinator is NOT in original participants list
            current_participants = list(self._executors.values())
            all_participants: Sequence[AgentProtocol | Executor] = [coordinator, *current_participants]
            self.participants(all_participants)
            self.set_coordinator(coordinator)

            return self

        return super().set_coordinator(agent)


__all__ = ["AutoHandoffBuilder"]
