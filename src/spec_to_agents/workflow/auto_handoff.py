# Copyright (c) Microsoft. All rights reserved.

"""AutoHandoffBuilder - HandoffBuilder with automatic coordinator creation."""

from typing import Any

from agent_framework import BaseChatClient, Workflow
from agent_framework._workflows._handoff import HandoffBuilder


class AutoHandoffBuilder(HandoffBuilder):
    """
    Extended HandoffBuilder that automatically creates a coordinator agent if not explicitly set.

    This builder extends HandoffBuilder to eliminate boilerplate coordinator setup by:
    1. Accepting a `client` parameter for creating the coordinator agent
    2. Auto-generating a coordinator from participant descriptions if `.set_coordinator()` not called
    3. Maintaining HandoffBuilder's fluent API and conventions

    Key Differences from HandoffBuilder:
    - Accepts `client` parameter in __init__ for auto-coordinator creation
    - If `.set_coordinator()` is NOT called before `.build()`, automatically creates coordinator
    - Auto-created coordinator is NOT included in participants list
    - Coordinator gets handoff tools for all participants
    - Coordinator instructions generated from participant descriptions

    Usage Patterns:

    **Auto-Coordinator (Recommended):**

    >>> workflow = AutoHandoffBuilder(
    ...     name="Event Planning",
    ...     participants=[venue, budget, catering, logistics],  # No coordinator!
    ...     client=client,  # Required for auto-creation
    ... ).build()  # Coordinator created automatically as "Event Planning Coordinator"

    **Manual Coordinator (Same as HandoffBuilder):**

    >>> coordinator = client.create_agent(name="coordinator", ...)
    >>> workflow = (
    ...     AutoHandoffBuilder(
    ...         participants=[coordinator, venue, budget, catering],
    ...         # No client needed when using explicit coordinator
    ...     )
    ...     .set_coordinator("coordinator")
    ...     .build()
    ... )  # Explicit coordinator

    **With Custom Coordinator Name:**

    >>> workflow = AutoHandoffBuilder(
    ...     name="Support",
    ...     participants=[tier1, tier2, escalation],
    ...     client=client,
    ...     coordinator_name="Support Triage Agent",  # Custom name
    ... ).build()

    Parameters
    ----------
    client : BaseChatClient, optional
        Chat client for creating coordinator agent. Required ONLY if you want auto-coordinator
        feature (i.e., not calling .set_coordinator()). If you call .set_coordinator()
        manually, client is not needed. Defaults to None.
    coordinator_name : str, optional
        Name for auto-created coordinator. Defaults to "{name} Coordinator".
        Only used if .set_coordinator() not called.
    coordinator_instructions_template : str, optional
        Custom prompt template for coordinator. Must include {coordinator_name} and
        {participants_description} placeholders. If not provided, uses default template.
    **kwargs : Any
        All other HandoffBuilder parameters (name, participants, description)

    Raises
    ------
    ValueError
        If .set_coordinator() not called AND client not provided in __init__
    """

    def __init__(
        self,
        *,
        client: BaseChatClient | None = None,
        coordinator_name: str | None = None,
        coordinator_instructions_template: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize AutoHandoffBuilder with optional client for auto-coordinator."""
        super().__init__(**kwargs)
        self._client = client
        self._coordinator_name_override = coordinator_name
        self._coordinator_instructions_template = coordinator_instructions_template

    def build(self) -> Workflow:
        """
        Build workflow, auto-creating coordinator if not explicitly set.

        Returns
        -------
        Workflow
            Configured workflow ready for execution

        Raises
        ------
        ValueError
            If coordinator not set AND client not provided
        """
        # Check if coordinator was explicitly set
        if self._starting_agent_id is None:
            # No coordinator set - create automatically
            if self._client is None:
                raise ValueError(
                    "AutoHandoffBuilder requires 'client' parameter in __init__ to auto-create coordinator. "
                    "Either provide client=... or call .set_coordinator() manually."
                )

            # Auto-create coordinator from participants
            self._auto_create_coordinator()

        # Call parent build() method
        return super().build()

    def _auto_create_coordinator(self) -> None:
        """Create coordinator agent from participant descriptions and configure builder."""
        if not self._executors:
            raise ValueError(
                "Cannot auto-create coordinator with no participants. Call .participants([...]) before .build()."
            )

        # Extract participant descriptions for coordinator instructions
        participant_descriptions = []
        for exec_id, executor in self._executors.items():
            # Get agent from executor
            agent = getattr(executor, "_agent", None)
            if agent:
                name = getattr(agent, "name", exec_id)
                description = getattr(agent, "description", None)
                if description is None:
                    # Fallback: use first line of instructions
                    chat_options = getattr(agent, "chat_options", None)
                    instructions = getattr(chat_options, "instructions", None) if chat_options else None
                    description = instructions.split("\n")[0] if instructions else f"Agent responsible for {exec_id}"
                participant_descriptions.append(f"- **{exec_id}** ({name}): {description}")
            else:
                # Executor without agent - use exec_id
                participant_descriptions.append(f"- **{exec_id}**: {exec_id}")

        participants_description = "Available participants:\n\n" + "\n".join(participant_descriptions)

        # Determine coordinator name
        coordinator_name = self._coordinator_name_override
        if coordinator_name is None:
            coordinator_name = f"{self._name} Coordinator" if self._name else "Coordinator"

        # Build coordinator instructions
        if self._coordinator_instructions_template:
            instructions = self._coordinator_instructions_template.format(
                coordinator_name=coordinator_name,
                participants_description=participants_description,
            )
        else:
            # Use default template
            from spec_to_agents.prompts.coordinator import COORDINATOR_SYSTEM_PROMPT_TEMPLATE

            instructions = COORDINATOR_SYSTEM_PROMPT_TEMPLATE.format(
                coordinator_name=coordinator_name,
                participants_description=participants_description,
            )

        # Create coordinator agent
        coordinator = self._client.create_agent(  # type: ignore[union-attr]
            name=coordinator_name.lower().replace(" ", "_"),
            description=coordinator_name,
            instructions=instructions,
            store=True,  # Use service-managed threads
        )

        # Register coordinator and set as starting agent
        # Note: coordinator is NOT in original participants list
        current_participants = list(self._executors.values())
        all_participants = [coordinator, *current_participants]
        self.participants(all_participants)
        self.set_coordinator(coordinator)
        self.add_handoff(coordinator, current_participants)
        # Each specialist can ONLY hand back to coordinator
        for specialist in current_participants:
            self.add_handoff(specialist, coordinator)


__all__ = ["AutoHandoffBuilder"]
