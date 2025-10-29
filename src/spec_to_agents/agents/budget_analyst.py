# Copyright (c) Microsoft. All rights reserved.

from spec_to_agents.clients import get_chat_client
from spec_to_agents.prompts.budget_analyst import SYSTEM_PROMPT

agent = get_chat_client().create_agent(
    name="BudgetAnalystAgent",
    instructions=SYSTEM_PROMPT,
    store=True,
    additional_chat_options={"allow_multiple_tool_calls": False},
)
