# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from spec_to_agents.workflow.messages import SpecialistOutput, SummarizedContext


def test_specialist_output_with_next_agent():
    """Test SpecialistOutput with routing to next agent."""
    output = SpecialistOutput(summary="Venue options researched", next_agent="budget", user_input_needed=False)
    assert output.next_agent == "budget"
    assert output.user_input_needed is False
    assert output.user_prompt is None


def test_specialist_output_with_user_input():
    """Test SpecialistOutput requesting user input."""
    output = SpecialistOutput(
        summary="Found 3 venue options",
        next_agent=None,
        user_input_needed=True,
        user_prompt="Which venue do you prefer?",
    )
    assert output.user_input_needed is True
    assert output.user_prompt == "Which venue do you prefer?"
    assert output.next_agent is None


def test_specialist_output_requires_summary():
    """Test SpecialistOutput validation."""
    with pytest.raises(ValidationError):
        SpecialistOutput(next_agent="budget")


def test_summarized_context():
    """Test SummarizedContext model."""
    context = SummarizedContext(condensed_summary="User wants 50 people party, $5000 budget")
    assert len(context.condensed_summary) > 0
