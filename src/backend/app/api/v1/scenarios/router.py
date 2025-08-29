"""
Learning Scenarios Router

This router provides endpoints for educational event planning scenarios.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Learning Scenarios Overview")
async def scenarios_overview():
    """Get an overview of available learning scenarios."""
    return {
        "message": "Learning Scenarios API", 
        "description": "Educational event planning scenarios for learning agent frameworks",
        "available_scenarios": [
            "corporate_retreat - Plan a corporate team retreat",
            "wedding_planning - Comprehensive wedding planning",
            "conference_organization - Large conference planning",
            "birthday_party - Simple birthday party planning"
        ]
    }

# TODO: Implement learning scenario endpoints