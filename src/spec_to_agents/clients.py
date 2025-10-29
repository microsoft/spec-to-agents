# Copyright (c) Microsoft. All rights reserved.
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential

_credential: ChainedTokenCredential | None = None
_chat_client: AzureAIAgentClient | None = None


def get_credential() -> ChainedTokenCredential:
    """Get or create the shared Azure credential."""
    global _credential
    if _credential is None:
        _credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            AzureCliCredential(),
        )
    return _credential


def get_chat_client() -> AzureAIAgentClient:
    """Get or create the shared agent client."""
    global _chat_client
    if _chat_client is None:
        _chat_client = AzureAIAgentClient(async_credential=get_credential())
    return _chat_client
