"""
Learning Progression Router

This router provides all learning progression endpoints organized by skill level.
Each level builds upon the previous, providing a structured educational experience.
"""

from fastapi import APIRouter
from .basic_agents import router as basic_agents_router
from .agent_tools import router as agent_tools_router
from .multi_agent import router as multi_agent_router
from .workflows import router as workflows_router
from .orchestration import router as orchestration_router
from .human_loop import router as human_loop_router

router = APIRouter()

# Include all learning level routers
router.include_router(
    basic_agents_router, 
    prefix="/basic_agents", 
    tags=["Level 1: Basic Agents"]
)
router.include_router(
    agent_tools_router, 
    prefix="/agent_tools", 
    tags=["Level 2: Agent Tools"]
)
router.include_router(
    multi_agent_router, 
    prefix="/multi_agent", 
    tags=["Level 3: Multi-Agent"]
)
router.include_router(
    workflows_router, 
    prefix="/workflows", 
    tags=["Level 4: Workflows"]
)
router.include_router(
    orchestration_router, 
    prefix="/orchestration", 
    tags=["Level 5: Orchestration"]
)
router.include_router(
    human_loop_router, 
    prefix="/human_loop", 
    tags=["Level 6: Human-in-the-Loop"]
)

@router.get("/", summary="Learning Path Overview")
async def learning_overview():
    """
    Get an overview of the complete learning progression path.
    
    Returns information about all learning levels, their objectives,
    and recommended progression path for users.
    """
    return {
        "title": "Microsoft Agent Framework Learning Path",
        "description": "Structured progression from basic agent interactions to advanced orchestration",
        "total_levels": 6,
        "levels": {
            "1": {
                "name": "Basic Agents",
                "description": "Single agent conversations and instructions",
                "endpoints": ["/basic_agents/simple_chat", "/basic_agents/with_instructions"],
                "learning_objectives": [
                    "Understanding agent creation and configuration",
                    "Basic prompt engineering and instructions",
                    "Single agent conversation patterns"
                ],
                "estimated_duration": "30 minutes"
            },
            "2": {
                "name": "Agent Tools",
                "description": "Python function tools, MCP integration, Hosted Code Interpreter",
                "endpoints": ["/agent_tools/native_tools", "/agent_tools/mcp_integration", "/agent_tools/hosted_tools"],
                "learning_objectives": [
                    "Creating and registering Python function tools",
                    "Understanding MCP (Model Context Protocol) integration",
                    "Using Hosted Code Interpreter for data analysis"
                ],
                "estimated_duration": "45 minutes"
            },
            "3": {
                "name": "Multi-Agent",
                "description": "Collaboration, group discussion, task delegation",
                "endpoints": ["/multi_agent/simple_collaboration", "/multi_agent/group_discussion", "/multi_agent/task_delegation"],
                "learning_objectives": [
                    "Agent-to-agent communication patterns",
                    "Task distribution and specialization",
                    "Coordination and consensus building"
                ],
                "estimated_duration": "60 minutes"
            },
            "4": {
                "name": "Workflows",
                "description": "Sequential, parallel, and conditional workflows",
                "endpoints": ["/workflows/sequential", "/workflows/parallel", "/workflows/conditional"],
                "learning_objectives": [
                    "Workflow design patterns",
                    "Sequential and parallel execution",
                    "Conditional logic and branching"
                ],
                "estimated_duration": "75 minutes"
            },
            "5": {
                "name": "Orchestration",
                "description": "Magentic patterns, adaptive coordination",
                "endpoints": ["/orchestration/magentic", "/orchestration/adaptive", "/orchestration/hybrid"],
                "learning_objectives": [
                    "Advanced orchestration patterns",
                    "Magentic workflow implementation",
                    "Adaptive coordination strategies"
                ],
                "estimated_duration": "90 minutes"
            },
            "6": {
                "name": "Human-in-the-Loop",
                "description": "Approvals, feedback, interventions",
                "endpoints": ["/human_loop/approval", "/human_loop/feedback", "/human_loop/intervention"],
                "learning_objectives": [
                    "Human approval workflows",
                    "Feedback integration patterns",
                    "Manual intervention capabilities"
                ],
                "estimated_duration": "45 minutes"
            }
        },
        "prerequisites": {
            "technical_skills": [
                "Basic Python programming knowledge",
                "Understanding of REST APIs",
                "Familiarity with async/await patterns"
            ],
            "business_knowledge": [
                "Basic understanding of event planning concepts",
                "Workflow and process design thinking"
            ]
        },
        "learning_path_recommendations": [
            "Complete levels in order for optimal learning progression",
            "Practice with the provided scenarios after each level",
            "Review code examples and explanations thoroughly",
            "Experiment with different parameters and configurations"
        ]
    }