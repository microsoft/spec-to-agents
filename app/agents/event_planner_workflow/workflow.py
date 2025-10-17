# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from agent_framework import AgentExecutorResponse, WorkflowBuilder
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential,
)
from pydantic import BaseModel


# Define structured output for review results
class ReviewResult(BaseModel):
    """Review evaluation with scores and feedback."""

    score: int  # Overall quality score (0-100)
    feedback: str  # Concise, actionable feedback
    clarity: int  # Clarity score (0-100)
    completeness: int  # Completeness score (0-100)
    accuracy: int  # Accuracy score (0-100)
    structure: int  # Structure score (0-100)


# Condition function: route to editor if score < 80
def needs_editing(message: Any) -> bool:
    """Check if content needs editing based on review score."""
    if not isinstance(message, AgentExecutorResponse):
        return False
    try:
        review = ReviewResult.model_validate_json(message.agent_run_response.text)
        return review.score < 80
    except Exception:
        return False


# Condition function: content is approved (score >= 80)
def is_approved(message: Any) -> bool:
    """Check if content is approved (high quality)."""
    if not isinstance(message, AgentExecutorResponse):
        return True
    try:
        review = ReviewResult.model_validate_json(message.agent_run_response.text)
        return review.score >= 80
    except Exception:
        return True


credential = ChainedTokenCredential(AzureCliCredential(), ManagedIdentityCredential())

chat_client = AzureOpenAIResponsesClient(env_file_path=".env", credential=credential)

# Create Writer agent - generates content
writer = chat_client.create_agent(
    name="Writer",
    instructions=(
        "You are an excellent content writer. "
        "Create clear, engaging content based on the user's request. "
        "Focus on clarity, accuracy, and proper structure."
    ),
)

# Create Reviewer agent - evaluates and provides structured feedback
reviewer = chat_client.create_agent(
    name="Reviewer",
    instructions=(
        "You are an expert content reviewer. "
        "Evaluate the writer's content based on:\n"
        "1. Clarity - Is it easy to understand?\n"
        "2. Completeness - Does it fully address the topic?\n"
        "3. Accuracy - Is the information correct?\n"
        "4. Structure - Is it well-organized?\n\n"
        "Return a JSON object with:\n"
        "- score: overall quality (0-100)\n"
        "- feedback: concise, actionable feedback\n"
        "- clarity, completeness, accuracy, structure: individual scores (0-100)"
    ),
    response_format=ReviewResult,
)

# Create Editor agent - improves content based on feedback
editor = chat_client.create_agent(
    name="Editor",
    instructions=(
        "You are a skilled editor. "
        "You will receive content along with review feedback. "
        "Improve the content by addressing all the issues mentioned in the feedback. "
        "Maintain the original intent while enhancing clarity, completeness, accuracy, and structure."
    ),
)

# Create Publisher agent - formats content for publication
publisher = chat_client.create_agent(
    name="Publisher",
    instructions=(
        "You are a publishing agent. "
        "You receive either approved content or edited content. "
        "Format it for publication with proper headings and structure."
    ),
)

# Create Summarizer agent - creates final publication report
summarizer = chat_client.create_agent(
    name="Summarizer",
    instructions=(
        "You are a summarizer agent. "
        "Create a final publication report that includes:\n"
        "1. A brief summary of the published content\n"
        "2. The workflow path taken (direct approval or edited)\n"
        "3. Key highlights and takeaways\n"
        "Keep it concise and professional."
    ),
)

# Build workflow with branching and convergence:
# Writer → Reviewer → [branches]:
#   - If score >= 80: → Publisher → Summarizer (direct approval path)
#   - If score < 80: → Editor → Publisher → Summarizer (improvement path)
# Both paths converge at Summarizer for final report
workflow = (
    WorkflowBuilder(
        name="Content Review Workflow",
        description=(
            "Multi-agent content creation workflow with quality-based routing (Writer → Reviewer → Editor/Publisher)"
        ),
    )
    .set_start_executor(writer)
    .add_edge(writer, reviewer)
    # Branch 1: High quality (>= 80) goes directly to publisher
    .add_edge(reviewer, publisher, condition=is_approved)
    # Branch 2: Low quality (< 80) goes to editor first, then publisher
    .add_edge(reviewer, editor, condition=needs_editing)
    .add_edge(editor, publisher)
    # Both paths converge: Publisher → Summarizer
    .add_edge(publisher, summarizer)
    .build()
)
