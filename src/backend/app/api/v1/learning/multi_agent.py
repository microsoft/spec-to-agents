"""
Level 3: Multi-Agent API

This module implements the third learning level focusing on multi-agent coordination.
Users learn agent-to-agent communication, collaboration patterns, and task delegation.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
import structlog
import asyncio
from datetime import datetime

# Microsoft Agent Framework imports
try:
    from agent_framework import ChatClientAgent
    from agent_framework.azure import AzureChatClient
    from agent_framework.group_chat import GroupChatManager
except ImportError:
    # Fallback for development/testing
    class ChatClientAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Agent')
        async def run(self, message: str):
            return f"[Mock {self.name}] Processed: {message}"
    
    class AzureChatClient:
        pass
    
    class GroupChatManager:
        def __init__(self, **kwargs):
            pass
        async def coordinate_discussion(self, *args, **kwargs):
            return "Mock group discussion result"

from app.core.config import get_settings
from app.core.models import CodeExample, LearningLevel, AgentType

logger = structlog.get_logger(__name__)

router = APIRouter()

# Request/Response Models
class SimpleCollaborationRequest(BaseModel):
    """Request model for simple two-agent collaboration."""
    task: str = Field(..., description="Task requiring two agents to collaborate",
                     example="Plan a corporate retreat for 100 employees with $25,000 budget")
    primary_agent: AgentType = Field(default=AgentType.EVENT_PLANNER, description="Primary coordination agent")
    secondary_agent: AgentType = Field(default=AgentType.BUDGET_ANALYST, description="Supporting specialist agent")
    collaboration_rounds: int = Field(default=3, ge=1, le=5, description="Number of collaboration rounds")

class GroupDiscussionRequest(BaseModel):
    """Request model for multi-agent group discussion."""
    topic: str = Field(..., description="Discussion topic for the agent group",
                      example="Plan a wedding reception for 200 guests in San Francisco")
    agent_types: List[AgentType] = Field(
        default=[AgentType.EVENT_PLANNER, AgentType.VENUE_RESEARCHER, AgentType.BUDGET_ANALYST, AgentType.CATERING_COORDINATOR],
        description="List of agent types to participate in discussion", min_length=3, max_length=6
    )
    discussion_rounds: int = Field(default=4, ge=2, le=8, description="Number of discussion rounds")
    require_consensus: bool = Field(default=True, description="Whether agents must reach consensus")

class TaskDelegationRequest(BaseModel):
    """Request model for task delegation patterns."""
    main_task: str = Field(..., description="Main task to be broken down and delegated",
                          example="Organize a three-day tech conference for 500 attendees")
    complexity: Literal["simple", "moderate", "complex"] = Field(default="moderate", description="Task complexity level")
    available_agents: Optional[List[AgentType]] = Field(default=None, description="Available agent types for delegation")
    auto_delegate: bool = Field(default=True, description="Automatically delegate subtasks to appropriate agents")

class AgentMessage(BaseModel):
    """Message from an agent in multi-agent interaction."""
    agent_name: str
    agent_type: AgentType  
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    round_number: int
    message_type: Literal["proposal", "feedback", "question", "conclusion"] = "proposal"

class MultiAgentResponse(BaseModel):
    """Response from multi-agent collaboration."""
    collaboration_type: str
    conversation: List[AgentMessage]
    final_result: str
    collaboration_summary: str
    agents_involved: List[str]
    processing_time_ms: float
    explanation: Dict[str, Any]
    learning_notes: List[str]
    code_example: CodeExample

# Agent Creation Functions
async def create_event_planner() -> ChatClientAgent:
    """Create an Event Planner agent."""
    return ChatClientAgent(
        name="EventPlannerAgent",
        description="Lead event planning coordination specialist",
        instructions="""
        You are the lead Event Planning Specialist responsible for coordinating complex events.
        
        Your responsibilities:
        - Analyze event requirements and create comprehensive strategies
        - Coordinate with specialized team members
        - Make final decisions based on team recommendations
        - Ensure all aspects meet client requirements
        - Manage timelines and overall project coordination
        
        When collaborating with other agents:
        - Ask specific questions to gather detailed information
        - Synthesize recommendations from specialists
        - Identify potential conflicts or gaps in planning
        - Provide clear next steps and action items
        """,
        chat_client=AzureChatClient()
    )

async def create_venue_researcher() -> ChatClientAgent:
    """Create a Venue Research agent."""
    return ChatClientAgent(
        name="VenueResearcherAgent",
        description="Venue research and selection specialist",
        instructions="""
        You are a Venue Research Specialist with expertise in finding ideal event locations.
        
        Your expertise includes:
        - Venue capacity and layout analysis
        - Location accessibility and logistics
        - Pricing and package negotiations
        - Vendor restrictions and partnerships
        - Backup venue recommendations
        
        When participating in discussions:
        - Ask about specific capacity, location, and budget requirements
        - Provide multiple venue options with detailed comparisons
        - Consider logistics like parking, accessibility, and vendor access
        - Flag potential venue-related challenges early
        """,
        chat_client=AzureChatClient()
    )

async def create_budget_analyst() -> ChatClientAgent:
    """Create a Budget Analyst agent.""" 
    return ChatClientAgent(
        name="BudgetAnalystAgent",
        description="Financial analysis and budget optimization specialist",
        instructions="""
        You are a Budget Analysis Specialist focused on financial planning and optimization.
        
        Your expertise includes:
        - Detailed cost breakdowns and analysis
        - Budget allocation optimization
        - Cost-saving opportunity identification
        - Financial risk assessment
        - ROI analysis for event components
        
        When collaborating:
        - Request specific budget parameters and constraints
        - Provide detailed cost analysis with alternatives
        - Identify areas for cost optimization
        - Alert team to budget risks or overruns
        - Suggest creative financing solutions
        """,
        chat_client=AzureChatClient()
    )

async def create_catering_coordinator() -> ChatClientAgent:
    """Create a Catering Coordinator agent."""
    return ChatClientAgent(
        name="CateringCoordinatorAgent", 
        description="Food service and catering specialist",
        instructions="""
        You are a Catering Coordination Specialist with expertise in food service planning.
        
        Your expertise includes:
        - Menu planning and dietary accommodations
        - Service style recommendations (plated, buffet, cocktail)
        - Vendor selection and management
        - Food safety and logistics
        - Cost estimation and budget optimization
        
        When participating in planning:
        - Ask about dietary restrictions, preferences, and guest count
        - Recommend appropriate service styles for the event type
        - Provide cost estimates with detailed breakdowns
        - Consider venue kitchen facilities and service requirements
        - Suggest beverage pairings and bar service options
        """,
        chat_client=AzureChatClient()
    )

async def create_logistics_manager() -> ChatClientAgent:
    """Create a Logistics Manager agent."""
    return ChatClientAgent(
        name="LogisticsManagerAgent",
        description="Event logistics and operations specialist", 
        instructions="""
        You are a Logistics Management Specialist responsible for operational planning.
        
        Your expertise includes:
        - Timeline and schedule coordination
        - Vendor management and coordination
        - Equipment and supply planning
        - Setup and breakdown logistics
        - Contingency planning
        
        When working with the team:
        - Create detailed timelines with dependencies
        - Identify potential logistical challenges
        - Coordinate vendor arrival and setup schedules
        - Plan for equipment needs and technical requirements
        - Develop backup plans for critical components
        """,
        chat_client=AzureChatClient()
    )

# Agent Factory
AGENT_CREATORS = {
    AgentType.EVENT_PLANNER: create_event_planner,
    AgentType.VENUE_RESEARCHER: create_venue_researcher,
    AgentType.BUDGET_ANALYST: create_budget_analyst,
    AgentType.CATERING_COORDINATOR: create_catering_coordinator,
    AgentType.LOGISTICS_MANAGER: create_logistics_manager,
}

async def create_agent(agent_type: AgentType) -> ChatClientAgent:
    """Create an agent of the specified type."""
    creator = AGENT_CREATORS.get(agent_type)
    if not creator:
        # Fallback for unsupported agent types
        return ChatClientAgent(
            name=f"{agent_type.value.replace('_', ' ').title()}Agent",
            description=f"Specialist in {agent_type.value.replace('_', ' ')}",
            instructions=f"You are a {agent_type.value.replace('_', ' ')} specialist.",
            chat_client=AzureChatClient()
        )
    return await creator()

# Multi-Agent Coordination Functions
async def conduct_simple_collaboration(
    task: str, primary_agent: ChatClientAgent, secondary_agent: ChatClientAgent, rounds: int
) -> List[AgentMessage]:
    """Conduct a simple two-agent collaboration."""
    conversation = []
    current_context = task
    
    for round_num in range(rounds):
        # Primary agent proposes or coordinates
        primary_prompt = f"""
        Task: {task}
        Round {round_num + 1}/{rounds}
        Current context: {current_context}
        
        {"Please provide your initial analysis and coordination approach." if round_num == 0 else
         "Based on the previous discussion, please provide your next steps and coordination."}
        """
        
        primary_response = await primary_agent.run(primary_prompt)
        conversation.append(AgentMessage(
            agent_name=primary_agent.name,
            agent_type=AgentType.EVENT_PLANNER,  # Assuming primary is event planner
            message=primary_response,
            round_number=round_num + 1,
            message_type="proposal"
        ))
        
        # Secondary agent responds with expertise
        secondary_prompt = f"""
        Task: {task}
        Round {round_num + 1}/{rounds}
        
        The Event Planner says: "{primary_response}"
        
        Please provide your specialist input, analysis, and recommendations based on your expertise.
        """
        
        secondary_response = await secondary_agent.run(secondary_prompt)
        conversation.append(AgentMessage(
            agent_name=secondary_agent.name,
            agent_type=AgentType.BUDGET_ANALYST,  # Assuming secondary is budget analyst
            message=secondary_response,
            round_number=round_num + 1,
            message_type="feedback"
        ))
        
        current_context = f"Primary: {primary_response}\nSecondary: {secondary_response}"
    
    return conversation

async def conduct_group_discussion(
    topic: str, agents: List[ChatClientAgent], rounds: int, require_consensus: bool
) -> List[AgentMessage]:
    """Conduct a multi-agent group discussion."""
    conversation = []
    discussion_history = ""
    
    for round_num in range(rounds):
        for agent in agents:
            if round_num == 0:
                prompt = f"""
                Discussion Topic: {topic}
                Round {round_num + 1}/{rounds}
                
                As the first round of discussion, please provide your initial perspective, 
                analysis, and recommendations based on your expertise.
                """
            else:
                prompt = f"""
                Discussion Topic: {topic}
                Round {round_num + 1}/{rounds}
                
                Previous discussion:
                {discussion_history}
                
                Based on the ongoing discussion, please provide your additional insights,
                respond to other agents' points, and contribute your expertise.
                {" Focus on reaching consensus with the group." if require_consensus and round_num >= rounds - 2 else ""}
                """
            
            response = await agent.run(prompt)
            
            # Determine agent type based on name
            agent_type = AgentType.EVENT_PLANNER  # Default
            for atype, name in [(AgentType.VENUE_RESEARCHER, "VenueResearcher"),
                              (AgentType.BUDGET_ANALYST, "BudgetAnalyst"),
                              (AgentType.CATERING_COORDINATOR, "CateringCoordinator")]:
                if name in agent.name:
                    agent_type = atype
                    break
            
            conversation.append(AgentMessage(
                agent_name=agent.name,
                agent_type=agent_type,
                message=response,
                round_number=round_num + 1,
                message_type="conclusion" if round_num == rounds - 1 else "proposal"
            ))
            
            discussion_history += f"\n{agent.name}: {response}\n"
    
    return conversation

# Learning Support Functions
def generate_multi_agent_explanation(collaboration_type: str) -> Dict[str, Any]:
    """Generate educational explanation for multi-agent interactions."""
    explanations = {
        "simple_collaboration": {
            "concept": "Two-Agent Collaboration",
            "what_happened": [
                "Two specialized agents worked together on a shared task",
                "Primary agent provided coordination and overall planning",
                "Secondary agent contributed specialized expertise and analysis",
                "Agents exchanged information and built upon each other's input"
            ],
            "key_learnings": [
                "Multi-agent systems leverage complementary expertise",
                "Coordination agents help orchestrate specialist contributions",
                "Information sharing between agents improves solution quality",
                "Different agents bring unique perspectives to complex problems"
            ],
            "microsoft_agent_framework_concepts": [
                "Agent specialization and role definition",
                "Inter-agent communication patterns",
                "Collaborative problem-solving workflows",
                "Context sharing and state management"
            ]
        },
        "group_discussion": {
            "concept": "Multi-Agent Group Discussion",
            "what_happened": [
                "Multiple specialist agents participated in structured discussion",
                "Each agent contributed expertise from their domain", 
                "Discussion progressed through multiple rounds of interaction",
                "Agents built upon and responded to each other's contributions"
            ],
            "key_learnings": [
                "Group discussions can surface diverse perspectives and solutions",
                "Round-based structure ensures all agents can contribute",
                "Consensus-building requires multiple interaction rounds",
                "Different specialists identify different aspects of complex problems"
            ],
            "microsoft_agent_framework_concepts": [
                "GroupChatManager for coordinating multi-agent discussions",
                "Round-robin communication patterns",
                "Consensus building algorithms",
                "Scalable multi-agent coordination"
            ]
        },
        "task_delegation": {
            "concept": "Intelligent Task Delegation",
            "what_happened": [
                "Complex task was analyzed and broken into subtasks",
                "Subtasks were matched to agents with appropriate expertise",
                "Coordinator agent managed overall task progress",
                "Results were synthesized into comprehensive solution"
            ],
            "key_learnings": [
                "Task decomposition enables parallel processing",
                "Agent expertise should match assigned subtask requirements",
                "Coordination overhead must be managed in delegation",
                "Proper task breakdown is crucial for effective delegation"
            ],
            "microsoft_agent_framework_concepts": [
                "Dynamic task assignment based on agent capabilities",
                "Hierarchical agent coordination patterns",
                "Result aggregation and synthesis",
                "Load balancing across agent specialists"
            ]
        }
    }
    return explanations.get(collaboration_type, explanations["simple_collaboration"])

def get_multi_agent_learning_notes() -> List[str]:
    """Get learning notes for Level 3."""
    return [
        "👥 **Core Concept**: Multi-agent systems solve complex problems through collaboration",
        "🎯 **Specialization**: Each agent should have clear expertise and responsibilities",
        "🔄 **Communication**: Structured interaction patterns prevent chaos in group settings",
        "⚖️ **Coordination**: Balance between agent autonomy and centralized coordination",
        "🧠 **Intelligence**: Group intelligence often exceeds individual agent capabilities",
        "📋 **Task Breakdown**: Complex tasks require thoughtful decomposition for effective delegation",
        "🤝 **Consensus**: Some scenarios benefit from consensus-building among agents",
        "⚡ **Efficiency**: Parallel processing through delegation can improve performance significantly"
    ]

def generate_multi_agent_code_example(example_type: str, **kwargs) -> CodeExample:
    """Generate code examples for multi-agent patterns."""
    examples = {
        "simple_collaboration": CodeExample(
            title="Two-Agent Collaboration",
            language="python",
            code="""
from agent_framework import ChatClientAgent
from agent_framework.azure import AzureChatClient

# Create specialized agents
event_planner = ChatClientAgent(
    name="EventPlannerAgent",
    instructions="You coordinate overall event planning...",
    chat_client=AzureChatClient()
)

budget_analyst = ChatClientAgent(
    name="BudgetAnalystAgent", 
    instructions="You analyze costs and optimize budgets...",
    chat_client=AzureChatClient()
)

# Coordinate collaboration
task = "Plan corporate retreat for 100 employees"

# Round 1: Planner initiates
planner_response = await event_planner.run(f"Task: {task}. Provide initial plan.")

# Round 2: Analyst provides expertise  
analyst_prompt = f"Task: {task}. Planner says: '{planner_response}'. Provide budget analysis."
analyst_response = await budget_analyst.run(analyst_prompt)

# Round 3: Planner synthesizes
final_plan = await event_planner.run(f"Incorporate budget analysis: {analyst_response}")
""".strip(),
            explanation="Two-agent collaboration involves structured information exchange between agents with complementary expertise. Each agent contributes their domain knowledge.",
            level=LearningLevel.LEVEL_3
        ),
        "group_discussion": CodeExample(
            title="Multi-Agent Group Discussion",
            language="python",
            code="""
from agent_framework.group_chat import GroupChatManager

# Create multiple specialist agents
agents = [
    await create_event_planner(),
    await create_venue_researcher(),
    await create_budget_analyst(),
    await create_catering_coordinator()
]

# Set up group discussion
group_manager = GroupChatManager(
    participants=agents,
    max_rounds=4,
    require_consensus=True
)

# Conduct structured discussion
topic = "Plan a wedding reception for 200 guests"
discussion_result = await group_manager.coordinate_discussion(
    topic=topic,
    discussion_style="round_robin"
)

print(f"Final consensus: {discussion_result.consensus}")
""".strip(),
            explanation="Group discussions enable multiple agents to collaborate on complex problems. GroupChatManager coordinates the interaction flow and consensus building.",
            level=LearningLevel.LEVEL_3
        ),
        "task_delegation": CodeExample(
            title="Intelligent Task Delegation",
            language="python",
            code="""
from agent_framework.coordination import TaskCoordinator

# Create coordinator and specialist agents
coordinator = ChatClientAgent(name="CoordinatorAgent", ...)
specialists = {
    "venue": await create_venue_researcher(),
    "budget": await create_budget_analyst(), 
    "catering": await create_catering_coordinator()
}

# Set up task delegation
task_coordinator = TaskCoordinator(
    coordinator_agent=coordinator,
    specialist_agents=specialists
)

# Delegate complex task
main_task = "Organize tech conference for 500 people"
result = await task_coordinator.delegate_task(
    task=main_task,
    auto_assign=True,  # Automatically assign subtasks to appropriate specialists
    parallel_execution=True
)

print(f"Delegated to: {result.assignments}")
print(f"Final result: {result.synthesized_outcome}")
""".strip(),
            explanation="Task delegation automatically breaks complex tasks into subtasks and assigns them to appropriate specialist agents based on their expertise.",
            level=LearningLevel.LEVEL_3
        )
    }
    return examples.get(example_type, examples["simple_collaboration"])

# API Endpoints
@router.get("/", summary="Multi-Agent Overview")
async def multi_agent_overview():
    """Get comprehensive overview of multi-agent collaboration capabilities."""
    return {
        "level": 3,
        "name": "Multi-Agent Collaboration", 
        "description": "Learn agent collaboration and coordination patterns for complex problem solving",
        "learning_objectives": [
            "Understand two-agent collaboration patterns",
            "Master multi-agent group discussions and consensus building",
            "Learn intelligent task delegation strategies",
            "Practice coordination between specialist agents"
        ],
        "collaboration_patterns": {
            "simple_collaboration": {
                "description": "Two agents working together on a shared task",
                "use_cases": ["Coordinator + Specialist", "Peer-to-peer collaboration", "Review workflows"],
                "advantages": ["Simple coordination", "Clear roles", "Fast iteration"]
            },
            "group_discussion": {
                "description": "Multiple agents in structured discussion",
                "use_cases": ["Design reviews", "Planning sessions", "Problem analysis"],
                "advantages": ["Diverse perspectives", "Comprehensive analysis", "Consensus building"]
            },
            "task_delegation": {
                "description": "Intelligent assignment of subtasks to specialists",
                "use_cases": ["Complex project management", "Parallel processing", "Expertise matching"],
                "advantages": ["Scalability", "Parallel execution", "Optimal resource utilization"]
            }
        },
        "endpoints": [
            {
                "path": "/simple_collaboration",
                "description": "Two-agent coordination with structured interaction rounds", 
                "example_request": "Plan corporate retreat with event planner and budget analyst"
            },
            {
                "path": "/group_discussion",
                "description": "Multi-agent group discussion with consensus building",
                "example_request": "Wedding planning discussion with 4 specialist agents"
            },
            {
                "path": "/task_delegation", 
                "description": "Intelligent task breakdown and delegation to specialists",
                "example_request": "Organize tech conference - auto-delegate to appropriate agents"
            }
        ],
        "agent_specialists": [
            f"{agent_type.value}: {agent_type.value.replace('_', ' ').title()}" 
            for agent_type in AgentType
        ]
    }

@router.post("/simple_collaboration", response_model=MultiAgentResponse, summary="Simple Two-Agent Collaboration")
async def simple_collaboration_demo(
    request: SimpleCollaborationRequest,
    settings = Depends(get_settings)
) -> MultiAgentResponse:
    """
    **Level 3 Learning Objective: Two-Agent Collaboration**
    
    Learn how two agents with complementary expertise can collaborate 
    effectively on complex tasks. This demonstrates structured interaction
    patterns, information sharing, and coordinated problem-solving.
    
    **What You'll Learn:**
    - How to structure agent-to-agent communication
    - Coordination patterns between primary and specialist agents  
    - Information sharing and context building across rounds
    - Role specialization in collaborative workflows
    
    **Collaboration Structure:**
    - Primary agent provides coordination and overall direction
    - Secondary agent contributes specialized expertise and analysis
    - Multiple rounds allow for iterative refinement
    - Each round builds upon previous agent interactions
    
    **Try These Examples:**
    - Event Planner + Budget Analyst: "Plan a corporate retreat for 100 employees"
    - Event Planner + Venue Researcher: "Find and secure venue for tech conference"  
    - Budget Analyst + Catering Coordinator: "Optimize catering costs for 200-person dinner"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing simple collaboration", 
                   primary=request.primary_agent, 
                   secondary=request.secondary_agent,
                   rounds=request.collaboration_rounds)
        
        # Create the collaborative agents
        primary_agent = await create_agent(request.primary_agent)
        secondary_agent = await create_agent(request.secondary_agent)
        
        # Conduct collaboration
        conversation = await conduct_simple_collaboration(
            task=request.task,
            primary_agent=primary_agent,
            secondary_agent=secondary_agent, 
            rounds=request.collaboration_rounds
        )
        
        # Generate final collaborative result
        final_prompt = f"""
        Based on the collaboration between {primary_agent.name} and {secondary_agent.name}
        on the task: {request.task}
        
        Please synthesize the discussion into a final comprehensive result that incorporates
        both agents' expertise and recommendations.
        """
        
        final_result = await primary_agent.run(final_prompt)
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Generate collaboration summary
        collaboration_summary = f"""
        Two-agent collaboration completed successfully:
        - Primary Agent ({primary_agent.name}): Provided coordination and overall planning
        - Secondary Agent ({secondary_agent.name}): Contributed specialized expertise
        - Collaboration Rounds: {request.collaboration_rounds}
        - Key Outcome: Integrated solution combining both agents' perspectives
        """
        
        return MultiAgentResponse(
            collaboration_type="simple_collaboration",
            conversation=conversation,
            final_result=final_result,
            collaboration_summary=collaboration_summary,
            agents_involved=[primary_agent.name, secondary_agent.name],
            processing_time_ms=processing_time,
            explanation=generate_multi_agent_explanation("simple_collaboration"),
            learning_notes=get_multi_agent_learning_notes(),
            code_example=generate_multi_agent_code_example("simple_collaboration")
        )
        
    except Exception as e:
        logger.error("Error in simple collaboration", error=str(e))
        raise HTTPException(status_code=500, detail=f"Collaboration failed: {str(e)}")

@router.post("/group_discussion", response_model=MultiAgentResponse, summary="Multi-Agent Group Discussion")  
async def group_discussion_demo(
    request: GroupDiscussionRequest,
    settings = Depends(get_settings)
) -> MultiAgentResponse:
    """
    **Level 3 Learning Objective: Multi-Agent Group Discussion**
    
    Learn how multiple specialist agents can participate in structured
    group discussions to solve complex problems through diverse expertise
    and collaborative decision-making.
    
    **What You'll Learn:**
    - Coordinating discussions with 3+ agents
    - Round-based communication patterns
    - Consensus building among diverse specialists
    - Managing complexity in group agent interactions
    
    **Discussion Structure:**
    - Round 1: Each agent provides initial perspective
    - Middle Rounds: Agents respond to others and build upon ideas
    - Final Round: Consensus building and synthesis
    - Optional: Require explicit consensus from all participants
    
    **Available Specialists:**
    - Event Planner: Overall coordination and strategy
    - Venue Researcher: Location and facility expertise
    - Budget Analyst: Financial analysis and optimization
    - Catering Coordinator: Food service and menu planning
    - Logistics Manager: Operations and timeline management
    
    **Try These Examples:**
    - Wedding Planning: "Plan outdoor wedding reception for 200 guests in wine country"
    - Corporate Event: "Design three-day leadership retreat with team building activities"
    - Conference Organization: "Plan tech conference with 500 attendees and 20 speakers"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing group discussion",
                   topic=request.topic,
                   agent_count=len(request.agent_types),
                   rounds=request.discussion_rounds)
        
        # Create participating agents
        agents = []
        for agent_type in request.agent_types:
            agent = await create_agent(agent_type)
            agents.append(agent)
        
        # Conduct group discussion
        conversation = await conduct_group_discussion(
            topic=request.topic,
            agents=agents,
            rounds=request.discussion_rounds,
            require_consensus=request.require_consensus
        )
        
        # Generate final consensus result
        if request.require_consensus:
            consensus_prompt = f"""
            Topic: {request.topic}
            
            Based on the group discussion, please provide a final consensus solution that 
            integrates all specialists' recommendations and addresses the key requirements.
            Focus on actionable outcomes and next steps.
            """
            final_result = await agents[0].run(consensus_prompt)  # Primary agent synthesizes
        else:
            final_result = "Group discussion completed. Multiple perspectives and recommendations provided."
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Generate collaboration summary
        agent_names = [agent.name for agent in agents]
        collaboration_summary = f"""
        Multi-agent group discussion completed:
        - Participants: {len(agents)} specialist agents
        - Discussion Rounds: {request.discussion_rounds}
        - Consensus Required: {request.require_consensus}
        - Agents Involved: {', '.join(agent_names)}
        - Key Outcome: Comprehensive solution integrating multiple expert perspectives
        """
        
        return MultiAgentResponse(
            collaboration_type="group_discussion",
            conversation=conversation,
            final_result=final_result,
            collaboration_summary=collaboration_summary,
            agents_involved=agent_names,
            processing_time_ms=processing_time,
            explanation=generate_multi_agent_explanation("group_discussion"),
            learning_notes=get_multi_agent_learning_notes(),
            code_example=generate_multi_agent_code_example("group_discussion")
        )
        
    except Exception as e:
        logger.error("Error in group discussion", error=str(e))
        raise HTTPException(status_code=500, detail=f"Group discussion failed: {str(e)}")

@router.post("/task_delegation", response_model=MultiAgentResponse, summary="Intelligent Task Delegation")
async def task_delegation_demo(
    request: TaskDelegationRequest,
    settings = Depends(get_settings)
) -> MultiAgentResponse:
    """
    **Level 3 Learning Objective: Task Delegation**
    
    Learn how to break down complex tasks into subtasks and intelligently
    delegate them to appropriate specialist agents based on their expertise
    and capabilities.
    
    **What You'll Learn:**
    - Task decomposition strategies for complex problems
    - Matching subtasks to agent expertise and capabilities
    - Parallel task execution across multiple agents
    - Result synthesis and coordination
    
    **Delegation Process:**
    1. Analyze main task and identify required expertise areas
    2. Break down task into logical subtasks
    3. Match subtasks to available agents based on specialization
    4. Execute subtasks in parallel where possible
    5. Synthesize results into comprehensive solution
    
    **Task Complexity Levels:**
    - Simple: 2-3 subtasks, minimal coordination
    - Moderate: 4-6 subtasks, some interdependencies
    - Complex: 7+ subtasks, significant coordination required
    
    **Auto-Delegation Logic:**
    - Venue-related tasks → Venue Researcher
    - Budget/financial tasks → Budget Analyst  
    - Food/catering tasks → Catering Coordinator
    - Logistics/operations → Logistics Manager
    - Overall coordination → Event Planner
    
    **Try These Examples:**
    - "Organize a three-day tech conference for 500 attendees with multiple tracks"
    - "Plan a corporate acquisition celebration dinner for 300 executives"
    - "Design a week-long international sales meeting with cultural activities"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing task delegation",
                   task=request.main_task,
                   complexity=request.complexity,
                   auto_delegate=request.auto_delegate)
        
        # Determine agent types needed based on task analysis
        if request.available_agents:
            agent_types = request.available_agents
        else:
            # Auto-determine based on complexity
            complexity_agents = {
                "simple": [AgentType.EVENT_PLANNER, AgentType.BUDGET_ANALYST],
                "moderate": [AgentType.EVENT_PLANNER, AgentType.VENUE_RESEARCHER, AgentType.BUDGET_ANALYST, AgentType.CATERING_COORDINATOR],
                "complex": [AgentType.EVENT_PLANNER, AgentType.VENUE_RESEARCHER, AgentType.BUDGET_ANALYST, 
                          AgentType.CATERING_COORDINATOR, AgentType.LOGISTICS_MANAGER]
            }
            agent_types = complexity_agents[request.complexity]
        
        # Create coordinator and specialist agents
        coordinator = await create_agent(AgentType.EVENT_PLANNER)
        specialists = {}
        for agent_type in agent_types:
            if agent_type != AgentType.EVENT_PLANNER:  # Coordinator is separate
                specialists[agent_type.value] = await create_agent(agent_type)
        
        # Step 1: Coordinator analyzes and delegates tasks
        delegation_prompt = f"""
        Main Task: {request.main_task}
        Complexity: {request.complexity}
        Available Specialists: {list(specialists.keys())}
        
        Please analyze this task and break it down into specific subtasks that can be
        delegated to the available specialists. For each subtask, specify which 
        specialist should handle it and why.
        """
        
        delegation_plan = await coordinator.run(delegation_prompt)
        
        # Step 2: Simulate parallel task execution by specialists
        conversation = []
        
        # Add coordinator's delegation plan
        conversation.append(AgentMessage(
            agent_name=coordinator.name,
            agent_type=AgentType.EVENT_PLANNER,
            message=delegation_plan,
            round_number=1,
            message_type="proposal"
        ))
        
        # Each specialist works on their assigned subtasks
        for specialist_type, specialist_agent in specialists.items():
            specialist_prompt = f"""
            Main Task: {request.main_task}
            
            Coordinator's Delegation Plan:
            {delegation_plan}
            
            Please execute the subtasks assigned to you as a {specialist_type} specialist.
            Provide detailed analysis, recommendations, and deliverables for your area of expertise.
            """
            
            specialist_response = await specialist_agent.run(specialist_prompt)
            
            # Map specialist type to AgentType enum
            agent_type_enum = AgentType.BUDGET_ANALYST  # Default fallback
            for atype in AgentType:
                if atype.value == specialist_type:
                    agent_type_enum = atype
                    break
            
            conversation.append(AgentMessage(
                agent_name=specialist_agent.name,
                agent_type=agent_type_enum,
                message=specialist_response,
                round_number=2,
                message_type="feedback"
            ))
        
        # Step 3: Coordinator synthesizes results
        all_specialist_results = "\n\n".join([
            f"{msg.agent_name}: {msg.message}" 
            for msg in conversation[1:]  # Skip coordinator's initial plan
        ])
        
        synthesis_prompt = f"""
        Main Task: {request.main_task}
        
        All Specialist Results:
        {all_specialist_results}
        
        Please synthesize all specialist contributions into a comprehensive final plan
        that addresses the main task. Ensure all aspects are coordinated and integrated.
        """
        
        final_result = await coordinator.run(synthesis_prompt)
        
        # Add synthesis to conversation
        conversation.append(AgentMessage(
            agent_name=coordinator.name,
            agent_type=AgentType.EVENT_PLANNER,
            message=final_result,
            round_number=3,
            message_type="conclusion"
        ))
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Generate collaboration summary
        all_agents = [coordinator.name] + list(specialists.values())
        agent_names = [coordinator.name] + [agent.name for agent in specialists.values()]
        
        collaboration_summary = f"""
        Task delegation completed successfully:
        - Main Task Complexity: {request.complexity}
        - Coordinator: {coordinator.name}
        - Specialists Involved: {len(specialists)}
        - Parallel Execution: {request.auto_delegate}
        - Key Outcome: Comprehensive delegated solution with specialist expertise integration
        """
        
        return MultiAgentResponse(
            collaboration_type="task_delegation",
            conversation=conversation,
            final_result=final_result,
            collaboration_summary=collaboration_summary,
            agents_involved=agent_names,
            processing_time_ms=processing_time,
            explanation=generate_multi_agent_explanation("task_delegation"),
            learning_notes=get_multi_agent_learning_notes(),
            code_example=generate_multi_agent_code_example("task_delegation")
        )
        
    except Exception as e:
        logger.error("Error in task delegation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Task delegation failed: {str(e)}")

@router.get("/examples", summary="Multi-Agent Code Examples")
async def get_multi_agent_examples():
    """
    Get comprehensive code examples for all multi-agent collaboration patterns.
    
    This endpoint provides ready-to-use examples demonstrating two-agent collaboration,
    group discussions, and intelligent task delegation patterns.
    """
    return {
        "collaboration_examples": [
            {
                "title": "Event Planner + Budget Analyst Collaboration",
                "description": "Two agents collaborating with complementary expertise",
                "code": """
# Create specialized agents
event_planner = ChatClientAgent(
    name="EventPlannerAgent",
    instructions="You coordinate event planning and strategy...",
    chat_client=AzureChatClient()
)

budget_analyst = ChatClientAgent(
    name="BudgetAnalystAgent",
    instructions="You analyze costs and optimize budgets...", 
    chat_client=AzureChatClient()
)

# Structured collaboration rounds
task = "Plan corporate retreat for 100 employees with $50k budget"

# Round 1: Planner provides initial strategy
planner_response = await event_planner.run(f"Task: {task}")

# Round 2: Analyst provides budget expertise
analyst_response = await budget_analyst.run(
    f"Task: {task}. Event Planner says: '{planner_response}'. Provide budget analysis."
)

# Round 3: Final synthesis
final_plan = await event_planner.run(
    f"Incorporate budget analysis: {analyst_response}"
)
                """,
                "use_cases": ["Planning + Analysis", "Strategy + Implementation", "Coordination + Expertise"]
            }
        ],
        "group_discussion_examples": [
            {
                "title": "Multi-Agent Wedding Planning Discussion",
                "description": "Four specialists collaborating on complex wedding planning",
                "code": """
from agent_framework.group_chat import GroupChatManager

# Create specialist agents
agents = [
    await create_event_planner(),      # Overall coordination
    await create_venue_researcher(),   # Location expertise  
    await create_budget_analyst(),     # Financial analysis
    await create_catering_coordinator() # Food service
]

# Configure group discussion
group_manager = GroupChatManager(
    participants=agents,
    max_rounds=4,
    require_consensus=True,
    discussion_style="round_robin"
)

# Run structured discussion
topic = "Plan outdoor wedding reception for 200 guests in wine country"
result = await group_manager.coordinate_discussion(topic=topic)

print(f"Consensus reached: {result.consensus}")
print(f"Final plan: {result.final_outcome}")
                """,
                "use_cases": ["Design sessions", "Strategic planning", "Problem solving", "Consensus building"]
            }
        ],
        "delegation_examples": [
            {
                "title": "Intelligent Task Delegation System",
                "description": "Automatic task breakdown and specialist assignment",
                "code": """
from agent_framework.coordination import TaskCoordinator

# Create coordinator and specialists
coordinator = await create_event_planner()
specialists = {
    "venue": await create_venue_researcher(),
    "budget": await create_budget_analyst(),
    "catering": await create_catering_coordinator(),
    "logistics": await create_logistics_manager()
}

# Configure task coordinator
task_coordinator = TaskCoordinator(
    coordinator_agent=coordinator,
    specialist_agents=specialists,
    parallel_execution=True
)

# Delegate complex task
main_task = "Organize 3-day tech conference for 500 attendees"
result = await task_coordinator.delegate_task(
    task=main_task,
    complexity="complex",
    auto_assign=True
)

print(f"Tasks delegated to: {result.assignments}")
print(f"Execution time: {result.execution_time_ms}ms")
print(f"Final outcome: {result.synthesized_result}")
                """,
                "use_cases": ["Project management", "Parallel processing", "Expertise optimization", "Scalable coordination"]
            }
        ],
        "best_practices": [
            "Define clear roles and responsibilities for each agent",
            "Structure communication patterns to prevent chaos",
            "Use round-based interactions for fair participation", 
            "Implement consensus mechanisms for group decisions",
            "Match agent expertise to task requirements",
            "Consider coordination overhead in complex scenarios",
            "Plan for conflict resolution between agent recommendations",
            "Monitor resource usage in multi-agent scenarios"
        ],
        "coordination_patterns": {
            "hierarchical": "Coordinator agent manages specialist agents",
            "peer_to_peer": "Agents collaborate as equals without central coordination",
            "round_robin": "Agents take turns contributing in structured rounds",
            "consensus_based": "All agents must agree on final decisions",
            "delegation_based": "Tasks automatically assigned based on agent capabilities"
        }
    }