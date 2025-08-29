"""
Redis caching service for the Microsoft Agent Framework Reference implementation.

This module provides caching capabilities for agent responses, session management,
and performance optimization using Redis.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import aioredis
import structlog

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

logger = structlog.get_logger(__name__)


class RedisService:
    """Redis service for caching and session management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis: Optional[aioredis.Redis] = None
        self.key_prefix = self.settings.REDIS_KEY_PREFIX
        self.default_ttl = self.settings.REDIS_DEFAULT_TTL
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis = aioredis.from_url(
                self.settings.REDIS_CONNECTION_STRING,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            
            logger.info("Redis service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis service", error=str(e))
            raise DatabaseError("redis_initialization", str(e))
    
    async def close(self):
        """Close Redis connection."""
        try:
            if self.redis:
                await self.redis.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error("Error closing Redis connection", error=str(e))
    
    def _make_key(self, key: str) -> str:
        """Create a prefixed key."""
        return f"{self.key_prefix}{key}"
    
    # Basic Cache Operations
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            if not self.redis:
                logger.warning("Redis not initialized")
                return False
            
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            cache_key = self._make_key(key)
            ttl_seconds = ttl or self.default_ttl
            
            await self.redis.setex(cache_key, ttl_seconds, serialized_value)
            
            logger.debug("Value cached", key=key, ttl=ttl_seconds)
            return True
            
        except Exception as e:
            logger.error("Failed to cache value", key=key, error=str(e))
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            if not self.redis:
                logger.warning("Redis not initialized")
                return None
            
            cache_key = self._make_key(key)
            value = await self.redis.get(cache_key)
            
            if value is None:
                logger.debug("Cache miss", key=key)
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
            
        except Exception as e:
            logger.error("Failed to retrieve cached value", key=key, error=str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            if not self.redis:
                logger.warning("Redis not initialized")
                return False
            
            cache_key = self._make_key(key)
            deleted_count = await self.redis.delete(cache_key)
            
            logger.debug("Key deleted from cache", key=key, existed=deleted_count > 0)
            return deleted_count > 0
            
        except Exception as e:
            logger.error("Failed to delete cached value", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            if not self.redis:
                return False
            
            cache_key = self._make_key(key)
            exists = await self.redis.exists(cache_key)
            return bool(exists)
            
        except Exception as e:
            logger.error("Failed to check key existence", key=key, error=str(e))
            return False
    
    # Agent Response Caching
    async def cache_agent_response(
        self, 
        agent_type: str,
        message_hash: str,
        response: str,
        level: str = "default",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache agent response for reuse."""
        cache_key = f"agent_response:{agent_type}:{level}:{message_hash}"
        
        response_data = {
            "response": response,
            "agent_type": agent_type,
            "level": level,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        return await self.set(cache_key, response_data, ttl or 3600)  # 1 hour default
    
    async def get_cached_agent_response(
        self, 
        agent_type: str,
        message_hash: str,
        level: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached agent response."""
        cache_key = f"agent_response:{agent_type}:{level}:{message_hash}"
        return await self.get(cache_key)
    
    # Session Management
    async def create_session(
        self, 
        session_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new user session."""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        session_key = f"session:{session_id}"
        user_sessions_key = f"user_sessions:{user_id}"
        
        # Store session data and add to user's session list
        success = await self.set(session_key, session_data, ttl=86400)  # 24 hours
        
        if success and self.redis:
            try:
                await self.redis.sadd(self._make_key(user_sessions_key), session_id)
                await self.redis.expire(self._make_key(user_sessions_key), 86400)  # 24 hours
            except Exception as e:
                logger.error("Failed to add session to user list", error=str(e))
        
        return success
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        session_key = f"session:{session_id}"
        return await self.get(session_key)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session's last activity timestamp."""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        session_key = f"session:{session_id}"
        return await self.set(session_key, session_data, ttl=86400)  # 24 hours
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user."""
        try:
            if not self.redis:
                return []
            
            user_sessions_key = self._make_key(f"user_sessions:{user_id}")
            session_ids = await self.redis.smembers(user_sessions_key)
            
            return list(session_ids) if session_ids else []
            
        except Exception as e:
            logger.error("Failed to retrieve user sessions", user_id=user_id, error=str(e))
            return []
    
    # Workflow State Caching
    async def cache_workflow_step(
        self, 
        workflow_id: str, 
        step_id: str, 
        step_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache workflow step result."""
        cache_key = f"workflow_step:{workflow_id}:{step_id}"
        
        step_cache = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "data": step_data,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        return await self.set(cache_key, step_cache, ttl or 1800)  # 30 minutes default
    
    async def get_cached_workflow_step(
        self, 
        workflow_id: str, 
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached workflow step."""
        cache_key = f"workflow_step:{workflow_id}:{step_id}"
        return await self.get(cache_key)
    
    # Rate Limiting
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int = 60
    ) -> Dict[str, Union[bool, int]]:
        """Check and update rate limit for an identifier."""
        try:
            if not self.redis:
                return {"allowed": True, "remaining": limit, "reset_time": 0}
            
            rate_key = self._make_key(f"rate_limit:{identifier}")
            current = await self.redis.get(rate_key)
            
            if current is None:
                # First request in window
                await self.redis.setex(rate_key, window_seconds, 1)
                return {"allowed": True, "remaining": limit - 1, "reset_time": window_seconds}
            
            current_count = int(current)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = await self.redis.ttl(rate_key)
                return {"allowed": False, "remaining": 0, "reset_time": ttl}
            
            # Increment counter
            await self.redis.incr(rate_key)
            ttl = await self.redis.ttl(rate_key)
            
            return {
                "allowed": True, 
                "remaining": limit - current_count - 1, 
                "reset_time": ttl
            }
            
        except Exception as e:
            logger.error("Failed to check rate limit", identifier=identifier, error=str(e))
            return {"allowed": True, "remaining": limit, "reset_time": 0}
    
    # Learning Progress Caching
    async def cache_learning_state(
        self, 
        user_id: str, 
        level: str, 
        state: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache user's learning state for a specific level."""
        cache_key = f"learning_state:{user_id}:{level}"
        
        state_data = {
            "user_id": user_id,
            "level": level,
            "state": state,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return await self.set(cache_key, state_data, ttl or 3600)  # 1 hour default
    
    async def get_learning_state(
        self, 
        user_id: str, 
        level: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached learning state."""
        cache_key = f"learning_state:{user_id}:{level}"
        cached = await self.get(cache_key)
        
        return cached["state"] if cached else None
    
    # Analytics Caching
    async def cache_analytics_data(
        self, 
        analytics_key: str, 
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache analytics data."""
        cache_key = f"analytics:{analytics_key}"
        
        analytics_cache = {
            "data": data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return await self.set(cache_key, analytics_cache, ttl or 600)  # 10 minutes default
    
    async def get_cached_analytics(self, analytics_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analytics data."""
        cache_key = f"analytics:{analytics_key}"
        cached = await self.get(cache_key)
        
        return cached["data"] if cached else None
    
    # Utility Methods
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern."""
        try:
            if not self.redis:
                return []
            
            full_pattern = self._make_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            # Remove prefix from returned keys
            return [key.replace(self.key_prefix, "") for key in keys]
            
        except Exception as e:
            logger.error("Failed to get keys by pattern", pattern=pattern, error=str(e))
            return []
    
    async def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cached data for a user."""
        try:
            if not self.redis:
                return False
            
            # Get all keys related to the user
            patterns = [
                f"session:{user_id}:*",
                f"user_sessions:{user_id}",
                f"learning_state:{user_id}:*",
                f"agent_response:*:{user_id}:*"
            ]
            
            keys_to_delete = []
            for pattern in patterns:
                pattern_keys = await self.get_keys_by_pattern(pattern)
                keys_to_delete.extend([self._make_key(key) for key in pattern_keys])
            
            if keys_to_delete:
                deleted_count = await self.redis.delete(*keys_to_delete)
                logger.info(f"Cleared {deleted_count} cache entries for user", user_id=user_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to clear user cache", user_id=user_id, error=str(e))
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if not self.redis:
                return {}
            
            info = await self.redis.info()
            
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
            
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {}