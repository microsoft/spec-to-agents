# Copyright (c) Microsoft. All rights reserved.

from spec2agent.workflow.messages import UserElicitationRequest


def test_user_elicitation_request_creation():
    """Test UserElicitationRequest can be created with required fields."""
    msg = UserElicitationRequest(
        prompt="Test prompt",
        context={"venues": ["A", "B", "C"]},
        request_type="selection"
    )
    assert msg.prompt == "Test prompt"
    assert msg.context == {"venues": ["A", "B", "C"]}
    assert msg.request_type == "selection"


def test_user_elicitation_request_is_request_info_message():
    """Test UserElicitationRequest inherits from RequestInfoMessage."""
    from agent_framework import RequestInfoMessage

    msg = UserElicitationRequest(
        prompt="Test",
        context={},
        request_type="clarification"
    )
    assert isinstance(msg, RequestInfoMessage)
