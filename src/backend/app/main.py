"""
Microsoft Agent Framework Reference Sample Implementation
FastAPI Application Entry Point

This is the main FastAPI application that serves as the educational platform
for learning Microsoft Agent Framework orchestration patterns.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import structlog
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.monitoring import setup_monitoring, MetricsCollector
from app.core.exceptions import setup_exception_handlers
from app.api.v1 import learning, agents, workflows, scenarios, foundry
from app.services.database.cosmos_service import CosmosService
from app.services.database.redis_service import RedisService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management for startup and shutdown."""
    settings = get_settings()
    logger.info("Starting Microsoft Agent Framework Reference API", version="1.0.0")
    
    # Initialize services
    try:
        # Setup monitoring
        setup_monitoring()
        logger.info("Monitoring initialized")
        
        # Initialize database connections
        cosmos_service = CosmosService()
        await cosmos_service.initialize()
        app.state.cosmos = cosmos_service
        logger.info("CosmosDB service initialized")
        
        # Initialize Redis cache
        redis_service = RedisService()
        await redis_service.initialize()
        app.state.redis = redis_service
        logger.info("Redis service initialized")
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        app.state.metrics = metrics_collector
        logger.info("Metrics collector initialized")
        
        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    finally:
        # Cleanup resources
        logger.info("Shutting down application")
        if hasattr(app.state, 'cosmos'):
            await app.state.cosmos.close()
        if hasattr(app.state, 'redis'):
            await app.state.redis.close()
        logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Microsoft Agent Framework Reference API",
        description="""
        **Educational platform for learning agent orchestration with Microsoft Agent Framework**
        
        This comprehensive reference implementation demonstrates all major capabilities
        of the Microsoft Agent Framework through practical event planning scenarios.
        
        ## Learning Progression
        
        📚 **Level 1**: Basic Agents - Single agent conversations and instructions  
        🔧 **Level 2**: Agent Tools - Python functions, MCP integration, Hosted Code Interpreter  
        👥 **Level 3**: Multi-Agent - Collaboration, group discussion, task delegation  
        🔄 **Level 4**: Workflows - Sequential, parallel, and conditional workflows  
        🎭 **Level 5**: Orchestration - Magentic patterns, adaptive coordination  
        🤝 **Level 6**: Human-in-the-Loop - Approvals, feedback, interventions  
        
        ## Features
        
        - **Agent Specialists**: Event Planner, Venue Researcher, Budget Analyst, and more
        - **Real-time Streaming**: WebSocket connections for live workflow monitoring
        - **Azure AI Foundry**: Integration with Azure AI model deployments
        - **Production Ready**: Full monitoring, caching, and enterprise patterns
        - **Educational Focus**: Each endpoint includes learning notes and code examples
        """,
        version="1.0.0",
        contact={
            "name": "Microsoft Agent Framework Team",
            "url": "https://github.com/microsoft/agent-framework",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        lifespan=lifespan,
        debug=settings.DEBUG,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        # Track metrics
        if hasattr(request.app.state, 'metrics'):
            await request.app.state.metrics.track_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=process_time
            )
        
        return response
    
    # Include API routers
    app.include_router(
        learning.router, 
        prefix="/api/v1/learning", 
        tags=["Learning Progression"]
    )
    app.include_router(
        agents.router, 
        prefix="/api/v1/agents", 
        tags=["Agent Management"]
    )
    app.include_router(
        workflows.router, 
        prefix="/api/v1/workflows", 
        tags=["Workflow Orchestration"]
    )
    app.include_router(
        scenarios.router, 
        prefix="/api/v1/scenarios", 
        tags=["Learning Scenarios"]
    )
    app.include_router(
        foundry.router, 
        prefix="/api/v1/foundry", 
        tags=["Azure AI Foundry"]
    )
    
    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """System health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "service": "Microsoft Agent Framework Reference API"
        }
    
    # API documentation redirect
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect to API documentation."""
        return JSONResponse({
            "message": "Microsoft Agent Framework Reference API",
            "documentation": "/docs",
            "openapi_spec": "/openapi.json",
            "learning_levels": {
                "level_1": "/api/v1/learning/basic_agents/",
                "level_2": "/api/v1/learning/agent_tools/",
                "level_3": "/api/v1/learning/multi_agent/",
                "level_4": "/api/v1/learning/workflows/",
                "level_5": "/api/v1/learning/orchestration/",
                "level_6": "/api/v1/learning/human_loop/"
            }
        })
    
    return app


# Create application instance
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True
    )