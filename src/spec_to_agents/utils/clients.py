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


def create_agent_client() -> AzureAIAgentClient:
    """
    Create a new AzureAIAgentClient for agent lifecycle management.

    Returns
    -------
    AzureAIAgentClient
        A client instance for creating and managing Azure AI agents.

    Notes
    -----
    **Best Practice:** Use as an async context manager for automatic cleanup:

        async with create_agent_client() as client:
            agent = client.create_agent(...)
            # Agent automatically deleted on context exit

    **DevUI Exception:** When using DevUI (agent_framework.devui.serve),
    cleanup is handled automatically via FastAPI lifespan hooks. DevUI calls
    close() on each agent's chat_client during server shutdown, so context
    manager usage is not required in DevUI export functions.

    See: agent_framework_devui/_server.py::_cleanup_entities()
    """
    return AzureAIAgentClient(async_credential=get_credential())
