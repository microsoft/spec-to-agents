"""
Azure CosmosDB service for the Microsoft Agent Framework Reference implementation.

This module provides database operations for storing workflow states, learning progress,
and other persistent data using Azure CosmosDB.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions
import structlog

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

logger = structlog.get_logger(__name__)


class CosmosService:
    """Azure CosmosDB service for data persistence."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.containers: Dict[str, ContainerProxy] = {}
        
        # Container configurations
        self.container_configs = {
            "workflow_states": {
                "partition_key": PartitionKey(path="/workflow_id"),
                "unique_key_policy": {"uniqueKeys": [{"paths": ["/id"]}]}
            },
            "learning_progress": {
                "partition_key": PartitionKey(path="/user_id"),
                "unique_key_policy": {"uniqueKeys": [{"paths": ["/id"]}]}
            },
            "agent_interactions": {
                "partition_key": PartitionKey(path="/session_id"),
                "unique_key_policy": {"uniqueKeys": [{"paths": ["/id"]}]}
            },
            "scenarios": {
                "partition_key": PartitionKey(path="/scenario_type"),
                "unique_key_policy": {"uniqueKeys": [{"paths": ["/id"]}]}
            },
            "user_sessions": {
                "partition_key": PartitionKey(path="/user_id"),
                "unique_key_policy": {"uniqueKeys": [{"paths": ["/id"]}]}
            }
        }
    
    async def initialize(self):
        """Initialize CosmosDB client and containers."""
        try:
            if not self.settings.COSMOS_ENDPOINT or not self.settings.COSMOS_KEY:
                logger.warning("CosmosDB credentials not provided, skipping initialization")
                return
            
            # Initialize client
            self.client = CosmosClient(
                url=self.settings.COSMOS_ENDPOINT,
                credential=self.settings.COSMOS_KEY
            )
            
            # Create or get database
            self.database = await self.client.create_database_if_not_exists(
                id=self.settings.COSMOS_DATABASE_NAME
            )
            
            # Create or get containers
            for container_name, config in self.container_configs.items():
                container = await self.database.create_container_if_not_exists(
                    id=container_name,
                    partition_key=config["partition_key"],
                    unique_key_policy=config.get("unique_key_policy")
                )
                self.containers[container_name] = container
            
            logger.info("CosmosDB service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize CosmosDB service", error=str(e))
            raise DatabaseError("cosmos_initialization", str(e))
    
    async def close(self):
        """Close CosmosDB client connection."""
        try:
            if self.client:
                await self.client.close()
                logger.info("CosmosDB client closed")
        except Exception as e:
            logger.error("Error closing CosmosDB client", error=str(e))
    
    # Workflow State Operations
    async def store_workflow_state(
        self, 
        workflow_id: str, 
        state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store workflow execution state."""
        try:
            container = self.containers.get("workflow_states")
            if not container:
                logger.warning("Workflow states container not available")
                return False
            
            document = {
                "id": workflow_id,
                "workflow_id": workflow_id,
                "state": state,
                "timestamp": datetime.utcnow().isoformat(),
                "ttl": ttl or self.settings.WORKFLOW_STATE_TTL
            }
            
            await container.upsert_item(document)
            logger.debug("Workflow state stored", workflow_id=workflow_id)
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to store workflow state", 
                workflow_id=workflow_id, 
                error=str(e)
            )
            raise DatabaseError("store_workflow_state", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error storing workflow state", 
                workflow_id=workflow_id, 
                error=str(e)
            )
            return False
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow execution state."""
        try:
            container = self.containers.get("workflow_states")
            if not container:
                return None
            
            item = await container.read_item(
                item=workflow_id,
                partition_key=workflow_id
            )
            
            logger.debug("Workflow state retrieved", workflow_id=workflow_id)
            return item["state"] if item else None
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug("Workflow state not found", workflow_id=workflow_id)
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to retrieve workflow state", 
                workflow_id=workflow_id, 
                error=str(e)
            )
            raise DatabaseError("get_workflow_state", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error retrieving workflow state", 
                workflow_id=workflow_id, 
                error=str(e)
            )
            return None
    
    # Learning Progress Operations
    async def store_learning_progress(
        self, 
        user_id: str, 
        progress: Dict[str, Any]
    ) -> bool:
        """Store user learning progress."""
        try:
            container = self.containers.get("learning_progress")
            if not container:
                logger.warning("Learning progress container not available")
                return False
            
            document = {
                "id": f"{user_id}_progress",
                "user_id": user_id,
                "progress": progress,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            await container.upsert_item(document)
            logger.debug("Learning progress stored", user_id=user_id)
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to store learning progress", 
                user_id=user_id, 
                error=str(e)
            )
            raise DatabaseError("store_learning_progress", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error storing learning progress", 
                user_id=user_id, 
                error=str(e)
            )
            return False
    
    async def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user learning progress."""
        try:
            container = self.containers.get("learning_progress")
            if not container:
                return None
            
            item = await container.read_item(
                item=f"{user_id}_progress",
                partition_key=user_id
            )
            
            logger.debug("Learning progress retrieved", user_id=user_id)
            return item["progress"] if item else None
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug("Learning progress not found", user_id=user_id)
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to retrieve learning progress", 
                user_id=user_id, 
                error=str(e)
            )
            raise DatabaseError("get_learning_progress", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error retrieving learning progress", 
                user_id=user_id, 
                error=str(e)
            )
            return None
    
    # Agent Interaction Operations
    async def store_agent_interaction(
        self, 
        interaction_id: str,
        session_id: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """Store agent interaction data."""
        try:
            container = self.containers.get("agent_interactions")
            if not container:
                logger.warning("Agent interactions container not available")
                return False
            
            document = {
                "id": interaction_id,
                "session_id": session_id,
                "interaction_data": interaction_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await container.create_item(document)
            logger.debug("Agent interaction stored", interaction_id=interaction_id)
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to store agent interaction", 
                interaction_id=interaction_id, 
                error=str(e)
            )
            raise DatabaseError("store_agent_interaction", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error storing agent interaction", 
                interaction_id=interaction_id, 
                error=str(e)
            )
            return False
    
    async def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all interactions for a session."""
        try:
            container = self.containers.get("agent_interactions")
            if not container:
                return []
            
            query = "SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c.timestamp"
            parameters = [{"name": "@session_id", "value": session_id}]
            
            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id
            ):
                items.append(item)
            
            logger.debug(f"Retrieved {len(items)} interactions for session", session_id=session_id)
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to retrieve session interactions", 
                session_id=session_id, 
                error=str(e)
            )
            raise DatabaseError("get_session_interactions", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error retrieving session interactions", 
                session_id=session_id, 
                error=str(e)
            )
            return []
    
    # Scenario Operations
    async def store_scenario(self, scenario: Dict[str, Any]) -> bool:
        """Store learning scenario."""
        try:
            container = self.containers.get("scenarios")
            if not container:
                logger.warning("Scenarios container not available")
                return False
            
            scenario["timestamp"] = datetime.utcnow().isoformat()
            
            await container.upsert_item(scenario)
            logger.debug("Scenario stored", scenario_id=scenario.get("id"))
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to store scenario", 
                scenario_id=scenario.get("id"), 
                error=str(e)
            )
            raise DatabaseError("store_scenario", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error storing scenario", 
                scenario_id=scenario.get("id"), 
                error=str(e)
            )
            return False
    
    async def get_scenarios_by_type(self, scenario_type: str) -> List[Dict[str, Any]]:
        """Retrieve scenarios by type."""
        try:
            container = self.containers.get("scenarios")
            if not container:
                return []
            
            query = "SELECT * FROM c WHERE c.scenario_type = @scenario_type"
            parameters = [{"name": "@scenario_type", "value": scenario_type}]
            
            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters,
                partition_key=scenario_type
            ):
                items.append(item)
            
            logger.debug(f"Retrieved {len(items)} scenarios", scenario_type=scenario_type)
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(
                "Failed to retrieve scenarios", 
                scenario_type=scenario_type, 
                error=str(e)
            )
            raise DatabaseError("get_scenarios_by_type", str(e))
        except Exception as e:
            logger.error(
                "Unexpected error retrieving scenarios", 
                scenario_type=scenario_type, 
                error=str(e)
            )
            return []
    
    # Analytics Operations
    async def get_learning_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregated learning analytics."""
        try:
            container = self.containers.get("learning_progress")
            if not container:
                return {}
            
            # Build query based on date range
            query = "SELECT * FROM c"
            parameters = []
            
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append("c.last_updated >= @start_date")
                    parameters.append({"name": "@start_date", "value": start_date.isoformat()})
                if end_date:
                    conditions.append("c.last_updated <= @end_date")
                    parameters.append({"name": "@end_date", "value": end_date.isoformat()})
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # Collect all progress records
            progress_records = []
            async for item in container.query_items(query=query, parameters=parameters):
                progress_records.append(item["progress"])
            
            # Aggregate analytics
            analytics = {
                "total_users": len(progress_records),
                "level_completions": {},
                "average_success_rates": {},
                "total_interactions": 0
            }
            
            # Process each user's progress
            for progress in progress_records:
                # Count level completions
                for level, completion_count in progress.get("level_completions", {}).items():
                    analytics["level_completions"][level] = analytics["level_completions"].get(level, 0) + completion_count
                
                # Count total interactions
                analytics["total_interactions"] += progress.get("total_interactions", 0)
            
            logger.debug(f"Retrieved analytics for {len(progress_records)} users")
            return analytics
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error("Failed to retrieve learning analytics", error=str(e))
            raise DatabaseError("get_learning_analytics", str(e))
        except Exception as e:
            logger.error("Unexpected error retrieving learning analytics", error=str(e))
            return {}