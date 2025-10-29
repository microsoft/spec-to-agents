# Copyright (c) Microsoft. All rights reserved.

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts.catering_coordinator import SYSTEM_PROMPT

agent = get_chat_client().create_agent(
    name="CateringCoordinatorAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={"allow_multiple_tool_calls": False},
)
