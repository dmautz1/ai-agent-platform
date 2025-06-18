"""
AI Agent Platform - Main Application

A production-ready platform for building and deploying AI agents with React frontend,
FastAPI backend, and Supabase database integration.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import uvicorn
import logging.config
from typing import List, Dict, Any
from datetime import datetime, timezone
import asyncio
from contextlib import asynccontextmanager

from auth import get_current_user, get_optional_user
from config.environment import get_settings, validate_required_settings, get_logging_config
from logging_system import (
    setup_logging_middleware, get_logger,
    get_security_logger, log_startup_info, log_shutdown_info
)
from agent import get_agent_registry, AgentError
from agent_discovery import get_agent_discovery_system
from agent_framework import register_agent_endpoints, get_registered_agents
from agents import discover_and_register_agents, instantiate_and_register_agents
from job_pipeline import start_job_pipeline, stop_job_pipeline
from database import get_database_operations, check_database_health
from models import JobCreateRequest, JobResponse
from static_files import setup_static_file_serving

# Import all route modules
from routes import (
    system_router,
    auth_router,
    agents_router,
    pipeline_router,
    llm_providers_router
)
from routes.jobs import router as jobs_router

# Initialize settings and validate required configuration
settings = get_settings()
validate_required_settings()

# Configure logging
logging_config = get_logging_config()
logging.config.dictConfig(logging_config)

# Initialize structured loggers
logger = get_logger(__name__)
security_logger = get_security_logger()

def get_cors_origins() -> List[str]:
    """Get CORS origins for the application - used by tests and configuration."""
    return get_settings().get_cors_origins()

# CORS Configuration
cors_origins = get_cors_origins()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    log_startup_info()
    
    logger.info(
        "Starting AI Agent Platform v1.0",
        extra={
            "startup_info": {
                "version": settings.app_version,
                "environment": settings.environment.value,
                "debug": settings.debug,
                "cors_origins": len(cors_origins),
                "job_queue_enabled": True,
                "agents_discovered": len(get_agent_discovery_system().discover_agents()),
                "enabled_agents": len(get_agent_discovery_system().get_enabled_agents()),
                "disabled_agents": len(get_agent_discovery_system().discover_agents()) - len(get_agent_discovery_system().get_enabled_agents())
            }
        }
    )
    
    try:
        # Get agent registry
        registry = get_agent_registry()
        
        # Auto-discover agent classes from agents/ directory
        discovery_result = discover_and_register_agents(registry)
        
        # Instantiate and register agent instances with explicit names
        instantiation_result = instantiate_and_register_agents(registry)
        
        logger.info(
            "Agent auto-discovery completed",
            classes_discovered=discovery_result['total_registered'],
            agents_instantiated=instantiation_result['total_instantiated'],
            discovery_errors=discovery_result['total_errors'],
            instantiation_errors=instantiation_result['total_errors']
        )
        
        # Auto-register all agent endpoints with FastAPI
        endpoint_count = register_agent_endpoints(app, registry)
        
        logger.info(
            "Agent framework initialization completed",
            total_agents=instantiation_result['total_instantiated'],
            total_endpoints=endpoint_count,
            framework_version="1.0"
        )
        
        # Log any errors
        if discovery_result['errors']:
            for error in discovery_result['errors']:
                logger.warning(f"Agent discovery error: {error}")
        
        # Start job processing pipeline
        await start_job_pipeline()
        logger.info("Job processing pipeline started")
        
    except Exception as e:
        logger.error("Failed to initialize agent framework", exception=e)
        raise
    
    logger.info("Application ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Beginning application shutdown")
    
    # Stop job processing pipeline
    try:
        await stop_job_pipeline()
        logger.info("Job processing pipeline stopped")
    except Exception as e:
        logger.error("Failed to stop job processing pipeline", exception=e)
    
    log_shutdown_info()
    logger.info("Application shutdown completed")

# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Agent Platform API",
    description="AI Agent Platform v1.0 - Self-contained agent framework with automatic discovery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization", "Content-Type", "Accept", "Origin",
        "User-Agent", "DNT", "Cache-Control", "X-Mx-ReqToken",
        "Keep-Alive", "X-Requested-With", "If-Modified-Since", "X-CSRF-Token"
    ],
    expose_headers=["Content-Length", "Content-Range", "X-Content-Range"],
    max_age=settings.cors_max_age,
)

# Set up comprehensive logging middleware
setup_logging_middleware(app)

# Security
security = HTTPBearer()

# Register all route modules
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(jobs_router)
app.include_router(pipeline_router)
app.include_router(llm_providers_router)

# Set up static file serving (for production)
setup_static_file_serving(app)

# Exception Handlers

@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError):
    """Handle agent-specific errors with detailed responses"""
    logger.warning(
        "Agent error occurred",
        exception=exc,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code
    )
    
    # Log security events for authentication failures
    if exc.status_code in [401, 403]:
        security_logger.log_auth_failure(
            reason=str(exc.detail),
            method="agent_operation"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Agent Error",
            "message": str(exc.detail),
            "type": type(exc).__name__,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive logging"""
    logger.error(
        "Unhandled exception occurred",
        exception=exc,
        path=request.url.path,
        method=request.method
    )
    
    if isinstance(exc, HTTPException) and exc.status_code in [401, 403]:
        security_logger.log_auth_failure(
            reason=str(exc.detail),
            method="unknown"
        )
    
    if settings.is_development():
        content = {
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    else:
        content = {
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    
    return JSONResponse(
        status_code=500,
        content=content
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development(),
        log_config=get_logging_config(),
        access_log=True,
        server_header=False,
        date_header=False
    ) 