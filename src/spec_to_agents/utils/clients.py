# Copyright (c) Microsoft. All rights reserved.
from agent_framework.azure import AzureAIAgentClient
from agent_framework.azure._shared import DEFAULT_AZURE_TOKEN_ENDPOINT
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


async def ad_token_provider() -> str:
    """Get Azure AD token for Azure OpenAI."""
    credential = get_credential()
    token = await credential.get_token(DEFAULT_AZURE_TOKEN_ENDPOINT)
    return token.token


def create_agent_client(agent_id: str | None = None) -> AzureAIAgentClient:
    """
    Create a new AzureAIAgentClient for agent lifecycle management.

    Parameters
    ----------
    agent_id : str | None, optional
        The ID of an existing agent to retrieve. If provided, the client will
        connect to the existing persistent agent. If None, the client can be
        used to create new agents.

    Returns
    -------
    AzureAIAgentClient
        A client instance for creating and managing Azure AI agents.
        Must be used within an async context manager for automatic cleanup.

    Notes
    -----
    The returned client should be used as an async context manager to ensure
    proper cleanup of created agents when the program terminates:

        # Creating a new agent
        async with create_agent_client() as client:
            agent = client.create_agent(...)
            # Agent automatically deleted on context exit

        # Retrieving an existing agent
        async with create_agent_client(agent_id="existing_id") as client:
            response = await client.run("query")
            # Existing agent not deleted on context exit

    This follows the Agent Framework best practice for resource management
    documented in the Azure AI Foundry integration guide.
    """
    return AzureAIAgentClient(async_credential=get_credential(), agent_id=agent_id)
