"""
Agent Management Router

This router provides endpoints for creating, configuring, and managing individual agents.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Agent Management Overview")
async def agent_overview():
    """Get an overview of agent management capabilities."""
    return {
        "message": "Agent Management API",
        "description": "Create, configure, and manage individual agents",
        "available_endpoints": [
            "/create - Create a new agent",
            "/configure - Configure an existing agent", 
            "/list - List all available agents",
            "/status/{agent_id} - Get agent status"
        ]
    }

# TODO: Implement individual agent management endpoints