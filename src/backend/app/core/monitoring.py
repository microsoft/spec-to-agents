"""
Monitoring and metrics collection for the Microsoft Agent Framework Reference implementation.

This module provides comprehensive monitoring capabilities including metrics collection,
logging, and Azure Application Insights integration.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import structlog
from azure.monitor.opentelemetry import configure_azure_monitor
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, start_http_server

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

# Prometheus Metrics
request_count = PrometheusCounter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

agent_interactions = PrometheusCounter(
    'agent_interactions_total',
    'Total number of agent interactions',
    ['agent_type', 'level', 'success']
)

agent_response_time = Histogram(
    'agent_response_time_seconds',
    'Agent response time in seconds',
    ['agent_type']
)

workflow_executions = PrometheusCounter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_type', 'status']
)

workflow_duration = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type']
)

active_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

learning_progress = PrometheusCounter(
    'learning_progress_total',
    'Learning progression events',
    ['level', 'user_id']
)


def setup_monitoring():
    """Initialize monitoring systems."""
    settings = get_settings()
    
    try:
        # Configure Azure Monitor (Application Insights) if connection string is provided
        if settings.APPLICATION_INSIGHTS_CONNECTION_STRING:
            configure_azure_monitor(
                connection_string=settings.APPLICATION_INSIGHTS_CONNECTION_STRING
            )
            logger.info("Azure Application Insights configured")
        
        # Start Prometheus metrics server if enabled
        if settings.ENABLE_METRICS:
            start_http_server(settings.METRICS_PORT)
            logger.info(f"Prometheus metrics server started on port {settings.METRICS_PORT}")
            
    except Exception as e:
        logger.error("Failed to setup monitoring", error=str(e))
        raise


class MetricsCollector:
    """Centralized metrics collection and analytics."""
    
    def __init__(self):
        self.settings = get_settings()
        self.session_data = defaultdict(dict)
        self.learning_analytics = defaultdict(lambda: {
            'level_completions': Counter(),
            'time_spent': defaultdict(float),
            'success_rate': defaultdict(list),
            'last_activity': None
        })
        
    async def track_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int, 
        duration: float
    ):
        """Track HTTP request metrics."""
        try:
            request_count.labels(
                method=method, 
                endpoint=endpoint, 
                status_code=str(status_code)
            ).inc()
            
            request_duration.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
            
            logger.debug(
                "Request tracked",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration
            )
            
        except Exception as e:
            logger.error("Failed to track request metrics", error=str(e))
    
    async def track_agent_interaction(
        self,
        agent_type: str,
        level: str,
        response_time: float,
        success: bool,
        user_id: Optional[str] = None,
        tokens_used: Optional[int] = None
    ):
        """Track agent interaction metrics."""
        try:
            agent_interactions.labels(
                agent_type=agent_type,
                level=level,
                success=str(success).lower()
            ).inc()
            
            agent_response_time.labels(agent_type=agent_type).observe(response_time)
            
            # Track learning analytics if user_id provided
            if user_id and self.settings.ENABLE_LEARNING_ANALYTICS:
                analytics = self.learning_analytics[user_id]
                analytics['last_activity'] = datetime.utcnow()
                analytics['success_rate'][level].append(success)
                
                if success:
                    analytics['level_completions'][level] += 1
                    learning_progress.labels(level=level, user_id=user_id).inc()
            
            logger.info(
                "Agent interaction tracked",
                agent_type=agent_type,
                level=level,
                response_time=response_time,
                success=success,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error("Failed to track agent interaction", error=str(e))
    
    async def track_workflow_execution(
        self,
        workflow_id: str,
        workflow_type: str,
        status: str,
        duration: Optional[float] = None,
        steps_completed: Optional[int] = None,
        agents_used: Optional[list] = None
    ):
        """Track workflow execution metrics."""
        try:
            workflow_executions.labels(
                workflow_type=workflow_type,
                status=status
            ).inc()
            
            if duration is not None:
                workflow_duration.labels(workflow_type=workflow_type).observe(duration)
            
            logger.info(
                "Workflow execution tracked",
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                status=status,
                duration=duration,
                steps_completed=steps_completed,
                agents_used=agents_used
            )
            
        except Exception as e:
            logger.error("Failed to track workflow execution", error=str(e))
    
    async def track_websocket_connection(self, connected: bool):
        """Track WebSocket connection changes."""
        try:
            if connected:
                active_connections.inc()
            else:
                active_connections.dec()
                
            logger.debug("WebSocket connection tracked", connected=connected)
            
        except Exception as e:
            logger.error("Failed to track WebSocket connection", error=str(e))
    
    async def track_learning_progress(
        self,
        user_id: str,
        level: str,
        completion_time: float,
        success: bool,
        attempts: int = 1
    ):
        """Track detailed learning progress for analytics."""
        try:
            if not self.settings.ENABLE_LEARNING_ANALYTICS:
                return
                
            analytics = self.learning_analytics[user_id]
            analytics['time_spent'][level] += completion_time
            analytics['success_rate'][level].append(success)
            analytics['last_activity'] = datetime.utcnow()
            
            # Store additional metrics
            if success:
                analytics['level_completions'][level] += 1
                learning_progress.labels(level=level, user_id=user_id).inc()
            
            logger.info(
                "Learning progress tracked",
                user_id=user_id,
                level=level,
                completion_time=completion_time,
                success=success,
                attempts=attempts
            )
            
        except Exception as e:
            logger.error("Failed to track learning progress", error=str(e))
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get learning analytics for a specific user."""
        try:
            if user_id not in self.learning_analytics:
                return {}
                
            analytics = self.learning_analytics[user_id]
            
            # Calculate success rates
            success_rates = {}
            for level, results in analytics['success_rate'].items():
                if results:
                    success_rates[level] = sum(results) / len(results)
                    
            # Calculate total time spent
            total_time = sum(analytics['time_spent'].values())
            
            return {
                'level_completions': dict(analytics['level_completions']),
                'time_spent': dict(analytics['time_spent']),
                'total_time_spent': total_time,
                'success_rates': success_rates,
                'last_activity': analytics['last_activity'].isoformat() if analytics['last_activity'] else None,
                'levels_attempted': list(analytics['success_rate'].keys()),
                'total_interactions': sum(len(results) for results in analytics['success_rate'].values())
            }
            
        except Exception as e:
            logger.error("Failed to get user analytics", user_id=user_id, error=str(e))
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics."""
        try:
            # Calculate aggregate learning metrics
            total_users = len(self.learning_analytics)
            total_completions = sum(
                sum(analytics['level_completions'].values())
                for analytics in self.learning_analytics.values()
            )
            
            # Calculate average success rates by level
            level_success_rates = defaultdict(list)
            for analytics in self.learning_analytics.values():
                for level, results in analytics['success_rate'].items():
                    if results:
                        level_success_rates[level].append(sum(results) / len(results))
            
            avg_success_rates = {
                level: sum(rates) / len(rates) if rates else 0
                for level, rates in level_success_rates.items()
            }
            
            return {
                'total_users': total_users,
                'total_level_completions': total_completions,
                'average_success_rates_by_level': avg_success_rates,
                'active_users_last_24h': self._count_recent_users(hours=24),
                'active_users_last_7d': self._count_recent_users(hours=24*7),
                'most_popular_levels': self._get_popular_levels(),
            }
            
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {}
    
    def _count_recent_users(self, hours: int) -> int:
        """Count users active within the specified number of hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return sum(
            1 for analytics in self.learning_analytics.values()
            if analytics['last_activity'] and analytics['last_activity'] > cutoff
        )
    
    def _get_popular_levels(self, top_n: int = 5) -> Dict[str, int]:
        """Get most popular learning levels by completion count."""
        level_counts = Counter()
        
        for analytics in self.learning_analytics.values():
            for level, count in analytics['level_completions'].items():
                level_counts[level] += count
                
        return dict(level_counts.most_common(top_n))
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old analytics data to prevent memory issues."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            users_to_remove = [
                user_id for user_id, analytics in self.learning_analytics.items()
                if analytics['last_activity'] and analytics['last_activity'] < cutoff
            ]
            
            for user_id in users_to_remove:
                del self.learning_analytics[user_id]
                
            logger.info(f"Cleaned up analytics data for {len(users_to_remove)} inactive users")
            
        except Exception as e:
            logger.error("Failed to cleanup old analytics data", error=str(e))