"""
Exception handling and custom exceptions for the Microsoft Agent Framework Reference implementation.

This module provides centralized exception handling and custom exception classes
for better error management and user experience.
"""

import traceback
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from pydantic import ValidationError
import structlog

logger = structlog.get_logger(__name__)


# Custom Exception Classes
class AgentFrameworkException(Exception):
    """Base exception for all Agent Framework related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "AGENT_ERROR", 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AgentCreationError(AgentFrameworkException):
    """Raised when agent creation fails."""
    
    def __init__(self, agent_type: str, reason: str):
        super().__init__(
            message=f"Failed to create agent of type '{agent_type}': {reason}",
            error_code="AGENT_CREATION_ERROR",
            details={"agent_type": agent_type, "reason": reason}
        )


class AgentExecutionError(AgentFrameworkException):
    """Raised when agent execution fails."""
    
    def __init__(self, agent_name: str, task: str, reason: str):
        super().__init__(
            message=f"Agent '{agent_name}' failed to execute task: {reason}",
            error_code="AGENT_EXECUTION_ERROR",
            details={"agent_name": agent_name, "task": task, "reason": reason}
        )


class WorkflowError(AgentFrameworkException):
    """Raised when workflow execution fails."""
    
    def __init__(self, workflow_id: str, step: str, reason: str):
        super().__init__(
            message=f"Workflow '{workflow_id}' failed at step '{step}': {reason}",
            error_code="WORKFLOW_ERROR",
            details={"workflow_id": workflow_id, "step": step, "reason": reason}
        )


class ToolExecutionError(AgentFrameworkException):
    """Raised when tool execution fails."""
    
    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {reason}",
            error_code="TOOL_EXECUTION_ERROR",
            details={"tool_name": tool_name, "reason": reason}
        )


class ConfigurationError(AgentFrameworkException):
    """Raised when configuration is invalid."""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{config_key}': {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, "reason": reason}
        )


class LearningError(AgentFrameworkException):
    """Raised when learning operations fail."""
    
    def __init__(self, level: str, operation: str, reason: str):
        super().__init__(
            message=f"Learning error at level '{level}' during '{operation}': {reason}",
            error_code="LEARNING_ERROR",
            details={"level": level, "operation": operation, "reason": reason}
        )


class DatabaseError(AgentFrameworkException):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            error_code="DATABASE_ERROR",
            details={"operation": operation, "reason": reason}
        )


class ExternalServiceError(AgentFrameworkException):
    """Raised when external service calls fail."""
    
    def __init__(self, service_name: str, operation: str, reason: str):
        super().__init__(
            message=f"External service '{service_name}' operation '{operation}' failed: {reason}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service_name": service_name, "operation": operation, "reason": reason}
        )


class RateLimitError(AgentFrameworkException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, resource: str, limit: int):
        super().__init__(
            message=f"Rate limit exceeded for '{resource}': {limit} requests per minute",
            error_code="RATE_LIMIT_ERROR",
            details={"resource": resource, "limit": limit}
        )


class AuthenticationError(AgentFrameworkException):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Authentication failed: {reason}",
            error_code="AUTHENTICATION_ERROR",
            details={"reason": reason}
        )


class AuthorizationError(AgentFrameworkException):
    """Raised when authorization fails."""
    
    def __init__(self, resource: str, action: str):
        super().__init__(
            message=f"Access denied to '{resource}' for action '{action}'",
            error_code="AUTHORIZATION_ERROR",
            details={"resource": resource, "action": action}
        )


# Exception Handlers
async def agent_framework_exception_handler(request: Request, exc: AgentFrameworkException):
    """Handle custom Agent Framework exceptions."""
    logger.error(
        "Agent Framework exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    
    # Map error codes to HTTP status codes
    status_code_map = {
        "AGENT_CREATION_ERROR": 400,
        "AGENT_EXECUTION_ERROR": 500,
        "WORKFLOW_ERROR": 500,
        "TOOL_EXECUTION_ERROR": 500,
        "CONFIGURATION_ERROR": 400,
        "LEARNING_ERROR": 400,
        "DATABASE_ERROR": 500,
        "EXTERNAL_SERVICE_ERROR": 502,
        "RATE_LIMIT_ERROR": 429,
        "AUTHENTICATION_ERROR": 401,
        "AUTHORIZATION_ERROR": 403,
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "type": "agent_framework_error"
            },
            "timestamp": str(datetime.utcnow()),
            "path": request.url.path,
            "method": request.method
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    error_id = str(uuid4())
    
    logger.error(
        "Unexpected exception",
        error_id=error_id,
        exception_type=type(exc).__name__,
        message=str(exc),
        traceback=traceback.format_exc(),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "error_id": error_id,
                "type": "internal_error"
            },
            "timestamp": str(datetime.utcnow()),
            "path": request.url.path,
            "method": request.method
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    
    # Format validation errors for better user experience
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data provided",
                "details": {
                    "validation_errors": formatted_errors
                },
                "type": "validation_error"
            },
            "timestamp": str(datetime.utcnow()),
            "path": request.url.path,
            "method": request.method
        }
    )


async def http_exception_handler_custom(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with enhanced logging."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    return await http_exception_handler(request, exc)


def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI application."""
    from datetime import datetime
    from uuid import uuid4
    
    # Custom exception handlers
    app.add_exception_handler(AgentFrameworkException, agent_framework_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler_custom)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers configured")


# Context Managers and Utilities
class ErrorContext:
    """Context manager for enhanced error handling and logging."""
    
    def __init__(
        self, 
        operation: str, 
        component: str, 
        context: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.component = component
        self.context = context or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(
            f"Starting {self.operation}",
            component=self.component,
            context=self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            logger.debug(
                f"Completed {self.operation}",
                component=self.component,
                duration=duration,
                context=self.context
            )
        else:
            logger.error(
                f"Failed {self.operation}",
                component=self.component,
                duration=duration,
                context=self.context,
                exception=str(exc_val),
                exception_type=exc_type.__name__
            )
        
        return False  # Don't suppress exceptions


# Validation Utilities
def validate_learning_level(level: str) -> bool:
    """Validate learning level format."""
    valid_levels = ["level_1", "level_2", "level_3", "level_4", "level_5", "level_6"]
    return level in valid_levels


def validate_agent_type(agent_type: str) -> bool:
    """Validate agent type."""
    valid_types = [
        "event_planner", "venue_researcher", "budget_analyst",
        "catering_coordinator", "logistics_manager", "compliance_officer",
        "customer_liaison"
    ]
    return agent_type in valid_types


def validate_workflow_type(workflow_type: str) -> bool:
    """Validate workflow type."""
    valid_types = ["sequential", "parallel", "conditional", "magentic", "adaptive", "hybrid"]
    return workflow_type in valid_types