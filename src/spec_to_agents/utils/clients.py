# Copyright (c) Microsoft. All rights reserved.
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential

_credential: ChainedTokenCredential | None = None


def get_credential() -> ChainedTokenCredential:
    """Get or create the shared Azure credential."""
    global _credential
    if _credential is None:
        _credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            AzureCliCredential(),
        )
    return _credential


def create_agent_client() -> AzureAIAgentClient:
    """
    Create a new AzureAIAgentClient for agent lifecycle management.

    Returns
    -------
    AzureAIAgentClient
        A client instance for creating and managing Azure AI agents.
        Must be used within an async context manager for automatic cleanup.

    Notes
    -----
    The returned client should be used as an async context manager to ensure
    proper cleanup of created agents when the program terminates:

        async with create_agent_client() as client:
            agent = client.create_agent(...)
            # Agent automatically deleted on context exit

    This follows the Agent Framework best practice for resource management
    documented in the Azure AI Foundry integration guide.
    """
    return AzureAIAgentClient(async_credential=get_credential())
