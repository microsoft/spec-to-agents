# Copyright (c) Microsoft. All rights reserved.

from spec2agent.clients import get_chat_client
from spec2agent.prompts.logistics_manager import SYSTEM_PROMPT

agent = get_chat_client().create_agent(
    name="LogisticsManagerAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
)
