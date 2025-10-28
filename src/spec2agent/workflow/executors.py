# Copyright (c) Microsoft. All rights reserved.

"""Custom executors for human-in-the-loop workflow interactions."""

import json

from agent_framework import (
    AgentExecutorResponse,
    Executor,
    FunctionCallContent,
    RequestResponse,
    WorkflowContext,
    handler,
)

from spec2agent.workflow.messages import UserElicitationRequest


class HumanInLoopAgentExecutor(Executor):
    """
    Wraps AgentExecutor to enable human-in-the-loop via request_user_input tool.

    When an agent calls the request_user_input tool, this executor:
    1. Intercepts the tool call from FunctionCallContent in AgentExecutorResponse
    2. Emits UserElicitationRequest to RequestInfoExecutor
    3. Workflow pauses until user provides response via DevUI
    4. Receives RequestResponse and continues workflow with agent's output

    Parameters
    ----------
    agent_id : str
        ID of the wrapped agent (for naming this executor)
    request_info_id : str
        ID of the RequestInfoExecutor to send user requests to

    Notes
    -----
    This executor must be placed between AgentExecutor and the next workflow step:
    AgentExecutor → HumanInLoopAgentExecutor → Next AgentExecutor

    It requires bidirectional edges to RequestInfoExecutor:
    HumanInLoopAgentExecutor ←→ RequestInfoExecutor
    """

    def __init__(self, agent_id: str, request_info_id: str):
        super().__init__(id=f"{agent_id}_hitl")
        self._agent_id = agent_id
        self._request_info_id = request_info_id
        self._current_response: AgentExecutorResponse | None = None

    @handler
    async def on_agent_response(self, response: AgentExecutorResponse, ctx: WorkflowContext) -> None:
        """
        Handle agent response and check for request_user_input tool calls.

        If tool call found, emit UserElicitationRequest to RequestInfoExecutor.
        Otherwise, continue workflow by forwarding agent response.
        """
        self._current_response = response

        # Check for request_user_input tool call
        user_request = self._extract_user_request(response)

        if user_request:
            # Agent needs user input - emit request to RequestInfoExecutor
            await ctx.send_message(
                UserElicitationRequest(
                    prompt=user_request["prompt"],
                    context=user_request["context"],
                    request_type=user_request["request_type"],
                ),
                target_id=self._request_info_id,
            )
            # Workflow pauses here until user responds via DevUI
        else:
            # No user input needed - continue to next agent
            await ctx.send_message(response)

    @handler
    async def on_user_response(self, response: RequestResponse, ctx: WorkflowContext) -> None:
        """
        Handle user response and continue workflow.

        User provided input via DevUI, which was routed back as RequestResponse.
        Forward the original agent response to continue workflow.
        """
        # User provided input - forward the agent response to continue workflow
        # The user's response is incorporated in the conversation context
        if self._current_response:
            await ctx.send_message(self._current_response)

    def _extract_user_request(self, response: AgentExecutorResponse) -> dict | None:
        """
        Extract request_user_input tool call arguments from agent response.

        Iterates through agent response messages looking for FunctionCallContent
        with name="request_user_input" and parses JSON arguments.

        Parameters
        ----------
        response : AgentExecutorResponse
            Agent's response to check for tool calls

        Returns
        -------
        dict | None
            Parsed tool arguments if found, None otherwise
        """
        for message in response.agent_run_response.messages:
            for content in message.contents:
                if isinstance(content, FunctionCallContent) and content.name == "request_user_input":
                    try:
                        return json.loads(content.arguments)
                    except json.JSONDecodeError:
                        # Arguments not valid JSON, skip
                        continue
        return None


__all__ = ["HumanInLoopAgentExecutor"]
