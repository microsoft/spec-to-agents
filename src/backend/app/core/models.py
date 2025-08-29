"""
Pydantic models for the Microsoft Agent Framework Reference implementation.

This module contains all the data models used throughout the application,
including request/response models, learning progression models, and agent models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4


# Base Models
class BaseResponseModel(BaseModel):
    """Base response model with common fields."""
    
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        str_strip_whitespace=True
    )
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid4()))


# Enums
class LearningLevel(str, Enum):
    """Available learning levels in the framework."""
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"
    LEVEL_5 = "level_5"
    LEVEL_6 = "level_6"


class DifficultyLevel(str, Enum):
    """Difficulty levels for learning content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class AgentType(str, Enum):
    """Types of available agents."""
    EVENT_PLANNER = "event_planner"
    VENUE_RESEARCHER = "venue_researcher"
    BUDGET_ANALYST = "budget_analyst"
    CATERING_COORDINATOR = "catering_coordinator"
    LOGISTICS_MANAGER = "logistics_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    CUSTOMER_LIAISON = "customer_liaison"


class WorkflowType(str, Enum):
    """Types of workflows available."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    MAGENTIC = "magentic"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


class ToolType(str, Enum):
    """Types of tools available to agents."""
    NATIVE = "native"
    MCP = "mcp"
    HOSTED = "hosted"


# Learning Models
class LearningNote(BaseModel):
    """Educational note for learning content."""
    title: str = Field(..., description="Title of the learning note")
    content: str = Field(..., description="Educational content")
    level: LearningLevel = Field(..., description="Associated learning level")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    tags: List[str] = Field(default_factory=list)


class CodeExample(BaseModel):
    """Code example for educational purposes."""
    title: str = Field(..., description="Title of the code example")
    language: str = Field(default="python", description="Programming language")
    code: str = Field(..., description="Code content")
    explanation: str = Field(..., description="Explanation of the code")
    level: LearningLevel = Field(..., description="Associated learning level")


class LearningResponse(BaseResponseModel):
    """Response model for learning endpoints."""
    agent_response: str = Field(..., description="Response from the agent")
    explanation: str = Field(..., description="Educational explanation")
    learning_notes: List[LearningNote] = Field(default_factory=list)
    code_example: Optional[CodeExample] = None
    next_steps: List[str] = Field(default_factory=list)
    level: LearningLevel = Field(..., description="Current learning level")


# Agent Models
class AgentConfiguration(BaseModel):
    """Configuration for creating an agent."""
    name: str = Field(..., description="Name of the agent")
    type: AgentType = Field(..., description="Type of agent")
    instructions: str = Field(..., description="Agent instructions")
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    model: str = Field(default="gpt-4", description="Model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timeout: int = Field(default=60, ge=1, le=300, description="Timeout in seconds")


class AgentInteraction(BaseModel):
    """Model for agent interaction requests."""
    message: str = Field(..., description="Message to send to the agent", min_length=1)
    agent_type: AgentType = Field(default=AgentType.EVENT_PLANNER)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    include_explanation: bool = Field(default=True, description="Include educational explanation")


class SimpleAgentRequest(BaseModel):
    """Request model for simple agent interactions."""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    agent_type: AgentType = Field(default=AgentType.EVENT_PLANNER)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)


class AgentWithInstructionsRequest(BaseModel):
    """Request model for agent with custom instructions."""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    agent_type: AgentType = Field(default=AgentType.EVENT_PLANNER)
    custom_instructions: str = Field(..., description="Custom agent instructions", max_length=1000)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)


# Tool Models
class ToolConfiguration(BaseModel):
    """Configuration for agent tools."""
    name: str = Field(..., description="Tool name")
    type: ToolType = Field(..., description="Tool type")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class NativeToolRequest(BaseModel):
    """Request for using native Python function tools."""
    message: str = Field(..., description="User message")
    tools: List[str] = Field(..., description="List of tool names to enable")
    agent_type: AgentType = Field(default=AgentType.BUDGET_ANALYST)


class McpToolRequest(BaseModel):
    """Request for using MCP (Model Context Protocol) tools."""
    message: str = Field(..., description="User message")
    mcp_server: str = Field(..., description="MCP server endpoint")
    tools: List[str] = Field(default_factory=list, description="Specific tools to use")
    agent_type: AgentType = Field(default=AgentType.VENUE_RESEARCHER)


class HostedToolRequest(BaseModel):
    """Request for using hosted Code Interpreter tools."""
    message: str = Field(..., description="User message")
    enable_code_interpreter: bool = Field(default=True)
    enable_file_upload: bool = Field(default=False)
    agent_type: AgentType = Field(default=AgentType.BUDGET_ANALYST)


# Multi-Agent Models
class MultiAgentRequest(BaseModel):
    """Request for multi-agent interactions."""
    message: str = Field(..., description="Initial message or task")
    agent_types: List[AgentType] = Field(..., description="List of agent types to involve", min_length=2)
    collaboration_type: Literal["simple", "group_discussion", "task_delegation"] = Field(
        default="simple", description="Type of collaboration"
    )
    max_rounds: int = Field(default=3, ge=1, le=10, description="Maximum collaboration rounds")


class AgentMessage(BaseModel):
    """Message from an agent in multi-agent collaboration."""
    agent_name: str = Field(..., description="Name of the agent")
    agent_type: AgentType = Field(..., description="Type of the agent")
    message: str = Field(..., description="Agent's message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class MultiAgentResponse(BaseResponseModel):
    """Response from multi-agent collaboration."""
    conversation: List[AgentMessage] = Field(..., description="Conversation between agents")
    final_result: str = Field(..., description="Final collaborative result")
    collaboration_summary: str = Field(..., description="Summary of the collaboration")
    agents_involved: List[str] = Field(..., description="List of agents that participated")


# Workflow Models
class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    step_id: str = Field(..., description="Unique step identifier")
    agent_type: AgentType = Field(..., description="Agent responsible for this step")
    task: str = Field(..., description="Task description")
    dependencies: List[str] = Field(default_factory=list, description="Dependent step IDs")
    timeout: int = Field(default=60, description="Step timeout in seconds")
    retry_count: int = Field(default=0, description="Number of retries allowed")


class WorkflowConfiguration(BaseModel):
    """Configuration for workflow execution."""
    name: str = Field(..., description="Workflow name")
    type: WorkflowType = Field(..., description="Workflow type")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    max_duration: int = Field(default=300, description="Maximum workflow duration in seconds")
    enable_human_review: bool = Field(default=False, description="Enable human-in-the-loop")


class WorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    task: str = Field(..., description="Overall task to complete")
    workflow_type: WorkflowType = Field(..., description="Type of workflow to execute")
    configuration: Optional[WorkflowConfiguration] = Field(default=None)
    context: Optional[Dict[str, Any]] = Field(default=None)


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class WorkflowExecutionResult(BaseModel):
    """Result of workflow step execution."""
    step_id: str = Field(..., description="Step identifier")
    agent_name: str = Field(..., description="Agent that executed the step")
    result: str = Field(..., description="Step execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    success: bool = Field(..., description="Whether step succeeded")
    error_message: Optional[str] = Field(default=None)


class WorkflowResponse(BaseResponseModel):
    """Response from workflow execution."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    results: List[WorkflowExecutionResult] = Field(default_factory=list)
    final_output: Optional[str] = Field(default=None)
    execution_time: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


# Human-in-the-Loop Models
class ApprovalRequest(BaseModel):
    """Request for human approval in workflow."""
    workflow_id: str = Field(..., description="Workflow identifier")
    step_id: str = Field(..., description="Step requiring approval")
    description: str = Field(..., description="Description of what needs approval")
    proposed_action: str = Field(..., description="Proposed action")
    context: Dict[str, Any] = Field(default_factory=dict)
    urgency: Literal["low", "medium", "high"] = Field(default="medium")


class ApprovalResponse(BaseModel):
    """Human approval response."""
    approval_id: str = Field(..., description="Approval request identifier")
    approved: bool = Field(..., description="Whether request is approved")
    feedback: Optional[str] = Field(default=None, description="Human feedback")
    modifications: Optional[Dict[str, Any]] = Field(default=None, description="Requested modifications")


class HumanFeedback(BaseModel):
    """Human feedback for agent improvement."""
    agent_name: str = Field(..., description="Agent receiving feedback")
    interaction_id: str = Field(..., description="Interaction identifier")
    feedback_type: Literal["positive", "negative", "suggestion"] = Field(..., description="Type of feedback")
    content: str = Field(..., description="Feedback content")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating from 1-5")


# Scenario Models
class EventPlanningScenario(BaseModel):
    """Event planning learning scenario."""
    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    difficulty: DifficultyLevel = Field(..., description="Scenario difficulty")
    requirements: Dict[str, Any] = Field(..., description="Event requirements")
    learning_objectives: List[str] = Field(..., description="Learning objectives")
    expected_agents: List[AgentType] = Field(..., description="Expected agents to be used")
    workflow_pattern: WorkflowType = Field(..., description="Recommended workflow pattern")
    estimated_duration: int = Field(..., description="Estimated completion time in minutes")


# Azure AI Foundry Models
class FoundryDeployment(BaseModel):
    """Azure AI Foundry model deployment."""
    deployment_id: str = Field(..., description="Deployment identifier")
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    endpoint_url: str = Field(..., description="Deployment endpoint URL")
    status: Literal["creating", "running", "failed", "deleting"] = Field(..., description="Deployment status")
    created_at: datetime = Field(..., description="Creation timestamp")


class FoundryMetrics(BaseModel):
    """Performance metrics from Azure AI Foundry."""
    deployment_id: str = Field(..., description="Deployment identifier")
    requests_per_minute: float = Field(..., description="Requests per minute")
    average_latency: float = Field(..., description="Average latency in milliseconds")
    success_rate: float = Field(..., description="Success rate as percentage")
    token_usage: int = Field(..., description="Total tokens used")
    cost: float = Field(..., description="Cost in USD")


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: Literal["workflow_event", "agent_response", "error", "status"] = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorkflowEvent(BaseModel):
    """Workflow execution event for streaming."""
    workflow_id: str = Field(..., description="Workflow identifier")
    event_type: Literal["started", "step_completed", "step_failed", "completed", "failed"] = Field(
        ..., description="Event type"
    )
    step_id: Optional[str] = Field(default=None, description="Step identifier if applicable")
    agent_name: Optional[str] = Field(default=None, description="Agent name if applicable")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)