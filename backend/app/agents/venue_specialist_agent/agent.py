from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import (
    ChainedTokenCredential,
    AzureCliCredential,
    ManagedIdentityCredential,
    get_bearer_token_provider,
)

from .prompts import SYSTEM_PROMPT

credential = ChainedTokenCredential(AzureCliCredential(), ManagedIdentityCredential())

venue_specialist_agent = AzureOpenAIResponsesClient(
    env_file_path=".env", credential=credential
).create_agent(name="venue_specialist", instructions=SYSTEM_PROMPT)
