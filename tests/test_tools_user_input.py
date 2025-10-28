# Copyright (c) Microsoft. All rights reserved.

from spec2agent.tools.user_input import request_user_input


def test_request_user_input_returns_placeholder():
    """Test that request_user_input returns placeholder message."""
    result = request_user_input(prompt="Test prompt", context={"key": "value"}, request_type="clarification")
    assert isinstance(result, str)
    assert len(result) > 0


def test_request_user_input_accepts_all_request_types():
    """Test that all request types are accepted."""
    for req_type in ["clarification", "selection", "approval"]:
        result = request_user_input(prompt="Test", context={}, request_type=req_type)
        assert isinstance(result, str)
