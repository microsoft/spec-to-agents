# Copyright (c) Microsoft. All rights reserved.
from contextlib import asynccontextmanager
from typing import AsyncIterator

from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential


async def ad_token_provider() -> str:
    """
    Get Azure AD token for Azure OpenAI.

    Returns
    -------
    str
        Azure AD access token for authentication.

def create_agent_client() -> AzureAIAgentClient:
    Notes
    -----
    This function creates a new credential instance for each call.
    For long-running applications, prefer using create_agent_client()
    which manages credential lifecycle properly.
    """
    credential = ChainedTokenCredential(
        ManagedIdentityCredential(),
        AzureCliCredential(),
    )
    try:
        token = await credential.get_token(DEFAULT_AZURE_TOKEN_ENDPOINT)
        return token.token
    finally:
        await credential.close()


def create_agent_client_for_devui() -> AzureAIAgentClient:
    """
    Create an AzureAIAgentClient for DevUI lazy loading (non-context-managed).

    Returns
    -------
    AzureAIAgentClient
        A client instance for DevUI. DevUI handles cleanup via FastAPI lifespan hooks.

    Warnings
    --------
    This function creates a client WITHOUT automatic cleanup. Only use this for
    DevUI lazy loading where FastAPI's lifespan management handles cleanup.
    For all other use cases, use create_agent_client() as an async context manager.

    Notes
    -----
    The credential's HTTP session will remain open until explicitly closed by
    the application's shutdown hooks. This is intentional for DevUI integration.
    """
    credential = ChainedTokenCredential(
        ManagedIdentityCredential(),
        AzureCliCredential(),
    )
    return AzureAIAgentClient(async_credential=credential)


@asynccontextmanager
async def create_agent_client() -> AsyncIterator[AzureAIAgentClient]:
    """
    Create a new AzureAIAgentClient with proper resource cleanup.

    Yields
    ------
    AzureAIAgentClient
        A client instance for creating and managing Azure AI agents.
        The client and its underlying credential are automatically cleaned up
        when the context exits.

    Notes
    -----
    This async context manager ensures proper cleanup of both the agent client
    and the Azure credential's HTTP session. Always use as a context manager:

        async with create_agent_client() as client:
            agent = client.create_agent(...)
            # Agent and credential automatically cleaned up on exit

    The credential's aiohttp session will be properly closed, preventing
    "Unclosed client session" warnings.

    Examples
    --------
    >>> async with create_agent_client() as client:
    ...     agent = client.create_agent(
    ...         name="MyAgent",
    ...         instructions="...",
    ...         tools=[...],
    ...     )
    ...     result = agent.run("Hello")
    """
    credential = ChainedTokenCredential(
        ManagedIdentityCredential(),
        AzureCliCredential(),
    )
    client = AzureAIAgentClient(async_credential=credential)

    try:
        async with client:
            yield client
    finally:
        # Ensure credential's HTTP session is closed
        await credential.close()
