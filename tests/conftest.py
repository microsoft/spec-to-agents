# Copyright (c) Microsoft. All rights reserved.

"""Shared pytest fixtures for test suite."""

from contextlib import suppress
from unittest.mock import Mock

import pytest

from spec_to_agents.container import AppContainer


@pytest.fixture(autouse=True)
def setup_di_container():
    """
    Set up and wire DI container for all tests.

    This fixture automatically runs before each test to ensure the DI container
    is properly configured. It mocks out the client and global_tools providers
    to avoid making real API calls during tests.

    The fixture is autouse=True, so it runs automatically for all tests without
    needing to be explicitly requested.
    """
    # Create container
    container = AppContainer()

    # Override providers with mocks for testing
    container.client.override(Mock())
    container.global_tools.override({})
    container.model_config.override({})

    # Wire the container to enable @inject decorators
    container.wire(
        packages=[
            "spec_to_agents.agents",
            "spec_to_agents.workflow",
        ]
    )

    # Yield control to the test
    yield container

    # Cleanup: unwire after test
    with suppress(Exception):
        # Ignore unwiring errors during cleanup
        container.unwire()
