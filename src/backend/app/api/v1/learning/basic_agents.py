"""
Level 1: Basic Agents API

This module implements the fundamental learning level for agent interactions.
Users learn to create, configure, and interact with single agents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import structlog
import asyncio
from datetime import datetime

# Microsoft Agent Framework imports
try:
    from agent_framework import ChatClientAgent
    from agent_framework.azure import AzureChatClient
except ImportError:
    # Fallback for development/testing
    class ChatClientAgent:
        def __init__(self, **kwargs):
            pass
        async def run(self, message: str):
            return f"[Mock Response] Processed: {message}"
    
    class AzureChatClient:
        pass

from app.core.config import get_settings
from app.core.models import CodeExample, LearningLevel

logger = structlog.get_logger(__name__)

router = APIRouter()

# Request/Response Models
class SimpleAgentRequest(BaseModel):
    """Request model for simple agent chat interactions."""
    message: str = Field(..., description="User message to send to the agent", example="Plan a birthday party for 25 people")
    agent_type: str = Field(default="event_planner", description="Type of agent to use", example="event_planner")
    difficulty: str = Field(default="beginner", description="Learning difficulty level", example="beginner")

class AgentInstructionsRequest(BaseModel):
    """Request model for agent interactions with custom instructions."""
    message: str = Field(..., description="User message to send to the agent")
    custom_instructions: str = Field(..., description="Custom instructions for the agent")
    agent_name: str = Field(default="CustomAgent", description="Name for the agent")
    personality_style: str = Field(default="professional", description="Agent personality style")

class AgentResponse(BaseModel):
    """Response model for agent interactions."""
    agent_response: str
    agent_name: str
    processing_time_ms: float
    explanation: Dict[str, Any]
    learning_notes: List[str]
    code_example: CodeExample

# Agent Instructions Templates
AGENT_INSTRUCTIONS = {
    "event_planner": {
        "beginner": """
        You are a friendly Event Planning Assistant helping users plan their events.
        - Ask clarifying questions about budget, date, location, and attendee count
        - Provide simple, actionable suggestions
        - Keep responses conversational and encouraging
        - Focus on the most important aspects first (venue, catering, timeline)
        """,
        "intermediate": """
        You are an experienced Event Planning Specialist with expertise in various event types.
        - Analyze requirements comprehensively and identify potential challenges
        - Provide detailed recommendations with alternatives
        - Consider budget optimization and vendor coordination
        - Include timeline planning and contingency suggestions
        """,
        "advanced": """
        You are a Senior Event Planning Consultant with expertise in complex, large-scale events.
        - Conduct thorough stakeholder analysis and requirements gathering
        - Develop comprehensive event strategies with risk management
        - Coordinate multiple vendors and manage intricate logistics
        - Provide executive-level insights and strategic recommendations
        """
    },
    "budget_analyst": {
        "beginner": """
        You are a Budget Analysis Helper focused on event cost estimation.
        - Break down costs into simple categories (venue, food, entertainment)
        - Provide rough estimates and cost-saving tips
        - Explain budget allocation in easy-to-understand terms
        """,
        "intermediate": """
        You are a Financial Analyst specializing in event budgeting.
        - Perform detailed cost analysis with multiple scenarios
        - Identify cost optimization opportunities and trade-offs
        - Provide ROI analysis and financial recommendations
        """,
        "advanced": """
        You are a Senior Financial Consultant for enterprise-level events.
        - Conduct comprehensive financial modeling and risk analysis
        - Develop sophisticated budgeting strategies with contingency planning
        - Provide executive financial insights and strategic cost management
        """
    },
    "venue_researcher": {
        "beginner": """
        You are a Venue Research Assistant helping find suitable event locations.
        - Ask about basic requirements: capacity, location, budget, date
        - Suggest popular venue types and considerations
        - Provide simple comparison factors
        """,
        "intermediate": """
        You are a Venue Research Specialist with comprehensive location knowledge.
        - Analyze venue requirements against multiple criteria
        - Provide detailed venue comparisons and recommendations
        - Consider logistics, accessibility, and vendor restrictions
        """,
        "advanced": """
        You are a Senior Venue Consultant with expertise in unique and complex locations.
        - Conduct sophisticated venue analysis including regulatory compliance
        - Negotiate venue terms and coordinate complex logistics
        - Provide strategic venue selection for high-profile events
        """
    }
}

def get_agent_instructions(agent_type: str, difficulty: str) -> str:
    """Get instructions for a specific agent type and difficulty level."""
    return AGENT_INSTRUCTIONS.get(agent_type, {}).get(
        difficulty, 
        AGENT_INSTRUCTIONS["event_planner"]["beginner"]
    )

def generate_learning_explanation(interaction_type: str) -> Dict[str, Any]:
    """Generate educational explanation for the interaction."""
    explanations = {
        "basic_interaction": {
            "concept": "Single Agent Interaction",
            "what_happened": [
                "Created a ChatClientAgent with specific instructions",
                "Configured the agent with a personality and expertise area", 
                "Sent your message to the agent for processing",
                "Received a contextual response based on the agent's configuration"
            ],
            "key_learnings": [
                "Agents are configured with instructions that shape their behavior",
                "Different agent types have different areas of expertise",
                "Agent responses are influenced by their configuration and context",
                "Instructions act as the 'personality' and 'expertise' of the agent"
            ],
            "microsoft_agent_framework_concepts": [
                "ChatClientAgent: Core agent class for conversational interactions",
                "Instructions: Text that defines agent behavior and expertise",
                "AzureChatClient: Azure OpenAI integration for agent responses"
            ]
        },
        "custom_instructions": {
            "concept": "Custom Agent Instructions",
            "what_happened": [
                "Created an agent with your custom instructions",
                "Applied personality style to modify agent behavior",
                "Processed your message through the customized agent",
                "Generated response reflecting your specific instructions"
            ],
            "key_learnings": [
                "Custom instructions allow fine-tuned control over agent behavior",
                "Personality styles can modify how agents communicate",
                "Instructions should be clear, specific, and actionable",
                "Well-crafted instructions lead to more relevant and useful responses"
            ],
            "microsoft_agent_framework_concepts": [
                "Dynamic instruction configuration",
                "Personality and style modulation", 
                "Flexible agent behavior customization"
            ]
        }
    }
    return explanations.get(interaction_type, explanations["basic_interaction"])

def get_learning_notes(level: str) -> List[str]:
    """Get learning notes for the current level."""
    notes = {
        "level_1": [
            "🎯 **Core Concept**: Single agents are the building blocks of all agent systems",
            "💡 **Best Practice**: Write clear, specific instructions that define the agent's role and expertise",
            "🔧 **Technical Tip**: Use descriptive agent names that reflect their function",
            "📚 **Next Steps**: Try different agent types and difficulty levels to see how instructions affect behavior",
            "🎨 **Customization**: Experiment with personality styles (professional, friendly, analytical, creative)",
            "⚡ **Performance**: Simple agents respond faster and use fewer resources than complex multi-agent systems"
        ]
    }
    return notes.get(level, [])

def generate_code_example(example_type: str, **kwargs) -> CodeExample:
    """Generate code examples for learning purposes."""
    examples = {
        "basic_agent": CodeExample(
            title="Creating a Basic Agent",
            language="python",
            code=f"""
# Import the Microsoft Agent Framework components
from agent_framework import ChatClientAgent
from agent_framework.azure import AzureChatClient

# Create an agent with specific instructions
agent = ChatClientAgent(
    name="{kwargs.get('agent_name', 'EventPlannerAgent')}",
    description="Specialized agent for event planning assistance",
    instructions=\"\"\"
    {kwargs.get('instructions', 'You are a helpful event planning assistant...')}
    \"\"\",
    chat_client=AzureChatClient()
)

# Send a message to the agent
response = await agent.run("{kwargs.get('message', 'Plan a birthday party')}")
print(response)
            """.strip(),
            explanation="ChatClientAgent is the core class for conversational agents. Instructions define the agent's behavior, expertise, and personality. AzureChatClient provides Azure OpenAI integration. The run() method processes messages and returns responses.",
            level=LearningLevel.LEVEL_1
        ),
        "custom_instructions": CodeExample(
            title="Agent with Custom Instructions",
            language="python", 
            code=f"""
# Create an agent with custom instructions and personality
custom_agent = ChatClientAgent(
    name="{kwargs.get('agent_name', 'CustomAgent')}",
    description="Agent with user-defined behavior",
    instructions=\"\"\"
    {kwargs.get('custom_instructions', 'Custom instructions here...')}
    
    Communication Style: {kwargs.get('personality_style', 'professional')}
    \"\"\",
    chat_client=AzureChatClient()
)

# Process the message
result = await custom_agent.run("{kwargs.get('message', 'Hello!')}")
            """.strip(),
            explanation="Custom instructions allow precise control over agent behavior. Personality styles can be embedded in instructions. Clear instructions lead to more predictable and useful responses.",
            level=LearningLevel.LEVEL_1
        )
    }
    return examples.get(example_type, examples["basic_agent"])

@router.post("/simple_chat", response_model=AgentResponse, summary="Simple Agent Chat")
async def simple_agent_chat(
    request: SimpleAgentRequest,
    settings = Depends(get_settings)
) -> AgentResponse:
    """
    **Level 1 Learning Objective: Basic Agent Interaction**
    
    Create and interact with a single agent using predefined instructions.
    This endpoint demonstrates the fundamental concepts of agent creation,
    configuration, and basic conversation patterns.
    
    **What You'll Learn:**
    - How to create a ChatClientAgent
    - How instructions shape agent behavior
    - Different agent types and difficulty levels
    - Basic agent-user interaction patterns
    
    **Try These Examples:**
    - "Plan a birthday party for 25 people with a $500 budget"
    - "I need help organizing a corporate team building event"
    - "What should I consider when planning an outdoor wedding?"
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing simple agent chat", 
                   agent_type=request.agent_type, 
                   difficulty=request.difficulty)
        
        # Get appropriate instructions for the agent type and difficulty
        instructions = get_agent_instructions(request.agent_type, request.difficulty)
        agent_name = f"{request.agent_type.replace('_', ' ').title()} ({request.difficulty.title()})"
        
        # Create the agent
        agent = ChatClientAgent(
            name=agent_name,
            description=f"Specialized {request.agent_type} agent at {request.difficulty} level",
            instructions=instructions,
            chat_client=AzureChatClient()
        )
        
        # Process the message
        response = await agent.run(request.message)
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return AgentResponse(
            agent_response=response,
            agent_name=agent_name,
            processing_time_ms=processing_time,
            explanation=generate_learning_explanation("basic_interaction"),
            learning_notes=get_learning_notes("level_1"),
            code_example=generate_code_example(
                "basic_agent",
                agent_name=agent_name,
                instructions=instructions,
                message=request.message
            )
        )
        
    except Exception as e:
        logger.error("Error in simple agent chat", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@router.post("/with_instructions", response_model=AgentResponse, summary="Agent with Custom Instructions")
async def agent_with_custom_instructions(
    request: AgentInstructionsRequest,
    settings = Depends(get_settings)
) -> AgentResponse:
    """
    **Level 1 Learning Objective: Custom Agent Instructions**
    
    Create an agent with your own custom instructions and personality style.
    This endpoint teaches you how to fine-tune agent behavior through
    instruction engineering and personality configuration.
    
    **What You'll Learn:**
    - How to write effective agent instructions
    - Impact of personality styles on agent responses  
    - Instruction engineering best practices
    - Dynamic agent behavior customization
    
    **Instruction Writing Tips:**
    - Be specific about the agent's role and expertise
    - Include examples of desired behavior
    - Specify communication style and tone
    - Define boundaries and limitations
    
    **Try These Personality Styles:**
    - professional, friendly, analytical, creative, enthusiastic, diplomatic
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("Processing agent with custom instructions",
                   agent_name=request.agent_name,
                   personality=request.personality_style)
        
        # Build instructions with personality style
        full_instructions = f"""
        {request.custom_instructions}
        
        Communication Style: {request.personality_style}
        - Maintain a {request.personality_style} tone throughout the conversation
        - Adapt your language and approach to match this personality style
        """
        
        # Create the agent with custom configuration
        agent = ChatClientAgent(
            name=request.agent_name,
            description=f"Custom agent with {request.personality_style} personality",
            instructions=full_instructions,
            chat_client=AzureChatClient()
        )
        
        # Process the message
        response = await agent.run(request.message)
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return AgentResponse(
            agent_response=response,
            agent_name=request.agent_name,
            processing_time_ms=processing_time,
            explanation=generate_learning_explanation("custom_instructions"),
            learning_notes=get_learning_notes("level_1"),
            code_example=generate_code_example(
                "custom_instructions",
                agent_name=request.agent_name,
                custom_instructions=request.custom_instructions,
                personality_style=request.personality_style,
                message=request.message
            )
        )
        
    except Exception as e:
        logger.error("Error in custom instructions agent", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@router.get("/examples", summary="Basic Agent Code Examples")
async def get_basic_agent_examples():
    """
    Get comprehensive code examples and explanations for basic agent patterns.
    
    This endpoint provides ready-to-use code examples that demonstrate
    various ways to create and configure basic agents.
    """
    return {
        "examples": [
            {
                "title": "Simple Event Planner Agent",
                "description": "Create a basic event planning agent with predefined instructions",
                "code": """
from agent_framework import ChatClientAgent
from agent_framework.azure import AzureChatClient

# Create a simple event planner
event_planner = ChatClientAgent(
    name="EventPlannerAgent",
    instructions="You are a helpful event planning assistant. Provide practical advice for organizing events.",
    chat_client=AzureChatClient()
)

# Use the agent
response = await event_planner.run("Help me plan a birthday party")
print(response)
                """,
                "use_cases": ["Birthday parties", "Corporate events", "Weddings", "Social gatherings"]
            },
            {
                "title": "Budget Analyst Agent", 
                "description": "Agent specialized in event budget analysis and cost estimation",
                "code": """
budget_analyst = ChatClientAgent(
    name="BudgetAnalystAgent",
    instructions=\"\"\"
    You are a financial analyst specializing in event budgets.
    - Break down costs by category
    - Suggest cost-saving opportunities
    - Provide realistic price estimates
    \"\"\",
    chat_client=AzureChatClient()
)
                """,
                "use_cases": ["Cost estimation", "Budget optimization", "Financial planning"]
            },
            {
                "title": "Venue Research Agent",
                "description": "Agent focused on finding and evaluating event venues", 
                "code": """
venue_researcher = ChatClientAgent(
    name="VenueResearcherAgent",
    instructions=\"\"\"
    You are a venue research specialist.
    - Ask about capacity, location, and budget requirements
    - Suggest appropriate venue types
    - Consider logistics and accessibility
    \"\"\",
    chat_client=AzureChatClient()
)
                """,
                "use_cases": ["Venue selection", "Location scouting", "Capacity planning"]
            }
        ],
        "best_practices": [
            "Use descriptive agent names that clearly indicate their purpose",
            "Write instructions that are specific but not overly constraining", 
            "Include examples in instructions for better agent understanding",
            "Test agents with various inputs to ensure consistent behavior",
            "Keep instructions focused on a single area of expertise"
        ],
        "common_patterns": {
            "role_definition": "Clearly define what role the agent should play",
            "expertise_area": "Specify the domain knowledge the agent should demonstrate",
            "communication_style": "Set expectations for how the agent should communicate",
            "task_boundaries": "Define what the agent should and shouldn't do"
        }
    }