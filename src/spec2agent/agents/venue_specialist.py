# Copyright (c) Microsoft. All rights reserved.

from spec2agent.clients import get_chat_client
from spec2agent.prompts.venue_specialist import SYSTEM_PROMPT

agent = get_chat_client().create_agent(
    name="VenueSpecialistAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={"allow_multiple_tool_calls": False},
)
