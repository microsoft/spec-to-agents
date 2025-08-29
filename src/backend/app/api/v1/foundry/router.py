"""
Azure AI Foundry Router

This router provides endpoints for Azure AI Foundry model deployments and management.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Azure AI Foundry Overview")
async def foundry_overview():
    """Get an overview of Azure AI Foundry capabilities."""
    return {
        "message": "Azure AI Foundry API",
        "description": "Integration with Azure AI Foundry for model deployment and management",
        "available_endpoints": [
            "/deployments - List model deployments",
            "/agents/deploy - Deploy agent to Foundry",
            "/agents/{id}/metrics - Get agent performance metrics",
            "/evaluate - Run agent evaluations"
        ]
    }

# TODO: Implement Azure AI Foundry integration endpoints