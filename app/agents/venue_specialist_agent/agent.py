# Copyright (c) Microsoft. All rights reserved.
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential,
)

from .prompts import SYSTEM_PROMPT

credential = ChainedTokenCredential(AzureCliCredential(), ManagedIdentityCredential())

chat_client = AzureOpenAIResponsesClient(env_file_path=".env", credential=credential)

venue_specialist_agent = ChatAgent(chat_client=chat_client, name="venue_specialist", instructions=SYSTEM_PROMPT)
