"""
AI Agent Platform - Main Application

A production-ready platform for building and deploying AI agents with React frontend,
FastAPI backend, and Supabase database integration.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging.config
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import os
import time
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse

from auth import get_current_user, get_optional_user
from config.environment import get_settings, validate_required_settings, get_logging_config
from logging_system import (
    setup_logging_middleware, get_logger, get_performance_logger,
    get_security_logger, log_startup_info, log_shutdown_info
)
from config.google_ai import validate_google_ai_environment, get_google_ai_config
from agent import get_agent_registry
from agent_discovery import get_agent_discovery_system
from agent_framework import register_agent_endpoints, get_all_agent_info, get_registered_agents
from agents import discover_and_register_agents, instantiate_and_register_agents, get_discovery_status
from job_pipeline import start_job_pipeline, stop_job_pipeline, get_job_pipeline
from database import get_database_operations, check_database_health
from models import JobCreateRequest, JobResponse, JobListResponse, JobCreateResponse, JobDetailResponse
from config.agent_config import get_agent_config_manager, get_agent_config, AgentProfile, AgentPerformanceMode
from static_files import setup_static_file_serving, get_static_file_info

# Initialize settings and validate required configuration
settings = get_settings()
validate_required_settings()

# Configure logging
logging_config = get_logging_config()
logging.config.dictConfig(logging_config)

# Initialize structured loggers
logger = get_logger(__name__)
perf_logger = get_performance_logger()
security_logger = get_security_logger()

class AgentError(HTTPException):
    """Base exception for agent-related errors"""
    pass

class AgentNotFoundError(AgentError):
    """Exception for when an agent is not found"""
    def __init__(self, agent_identifier: str, detail: str = None):
        self.agent_identifier = agent_identifier
        detail = detail or f"Agent '{agent_identifier}' not found"
        super().__init__(status_code=404, detail=detail)

class AgentDisabledError(AgentError):
    """Exception for when an agent is disabled"""
    def __init__(self, agent_identifier: str, lifecycle_state: str = None, detail: str = None):
        self.agent_identifier = agent_identifier
        self.lifecycle_state = lifecycle_state
        if not detail:
            if lifecycle_state:
                detail = f"Agent '{agent_identifier}' is {lifecycle_state} and not available for use"
            else:
                detail = f"Agent '{agent_identifier}' is not enabled"
        super().__init__(status_code=400, detail=detail)

class AgentNotLoadedError(AgentError):
    """Exception for when an agent exists but is not loaded"""
    def __init__(self, agent_identifier: str, detail: str = None):
        self.agent_identifier = agent_identifier
        detail = detail or f"Agent '{agent_identifier}' is not currently loaded or available"
        super().__init__(status_code=503, detail=detail)

def validate_agent_exists_and_enabled(agent_identifier: str, require_loaded: bool = False) -> Dict[str, Any]:
    """
    Centralized agent validation with consistent error handling.
    
    Args:
        agent_identifier: The agent identifier to validate
        require_loaded: Whether to require the agent instance to be loaded
        
    Returns:
        dict: Agent metadata and instance information
        
    Raises:
        AgentNotFoundError: If agent doesn't exist
        AgentDisabledError: If agent is disabled
        AgentNotLoadedError: If require_loaded=True and agent not loaded
    """
    # Check if agent exists via discovery system
    discovery = get_agent_discovery_system()
    metadata = discovery.get_agent_metadata(agent_identifier)
    
    if not metadata:
        logger.warning("Agent validation failed - not found", agent_identifier=agent_identifier)
        raise AgentNotFoundError(agent_identifier)
    
    # Check if agent is enabled
    if metadata.lifecycle_state.value != "enabled":
        logger.warning(
            "Agent validation failed - not enabled", 
            agent_identifier=agent_identifier,
            lifecycle_state=metadata.lifecycle_state.value
        )
        raise AgentDisabledError(agent_identifier, metadata.lifecycle_state.value)
    
    # Check if agent has load errors
    if metadata.load_error:
        logger.warning(
            "Agent validation failed - has load error",
            agent_identifier=agent_identifier,
            load_error=metadata.load_error
        )
        raise AgentDisabledError(
            agent_identifier,
            detail=f"Agent '{agent_identifier}' has load errors: {metadata.load_error}"
        )
    
    result = {
        "metadata": metadata,
        "instance": None,
        "instance_available": False
    }
    
    # Check for loaded instance if required
    if require_loaded:
        # Try to get registered agents first
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_identifier)
        
        if not agent_instance:
            # Try to get from registry as fallback
            registry = get_agent_registry()
            agent_instance = registry.get_agent(agent_identifier)
        
        if not agent_instance:
            logger.warning(
                "Agent validation failed - not loaded",
                agent_identifier=agent_identifier
            )
            raise AgentNotLoadedError(agent_identifier)
        
        result["instance"] = agent_instance
        result["instance_available"] = True
    
    logger.debug("Agent validation successful", agent_identifier=agent_identifier)
    return result

def log_agent_access(agent_identifier: str, operation: str, user_id: str = None, success: bool = True):
    """Centralized logging for agent access operations"""
    log_data = {
        "agent_identifier": agent_identifier,
        "operation": operation,
        "success": success
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if success:
        logger.info(f"Agent {operation} successful", **log_data)
    else:
        logger.warning(f"Agent {operation} failed", **log_data)

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
        logger.error("Error stopping job pipeline", exception=e)
    
    log_shutdown_info()

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

# Core Application Endpoints
@app.get("/")
async def root():
    """Health check endpoint - public"""
    with perf_logger.time_operation("health_check_root"):
        logger.info("Root health check requested")
        
        return {
            "message": f"{settings.app_name} v1.0 is running",
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "framework_version": "1.0",
            "agent_framework": "self-contained",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    with perf_logger.time_operation("health_check"):
        logger.info("Health check requested")
        
        try:
            # Quick database connectivity check
            db_health = await check_database_health()
            
            health_status = {
                "status": "healthy",
                "version": settings.app_version,
                "environment": settings.environment.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": db_health,
                "cors_origins": len(get_cors_origins())
            }
            
            return health_status
            
        except Exception as e:
            logger.error("Health check failed", exception=e)
            return {
                "status": "unhealthy",
                "version": settings.app_version,
                "environment": settings.environment.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

@app.get("/stats")
async def get_public_stats():
    """Get public job statistics - public endpoint"""
    try:
        db_ops = get_database_operations()
        stats = await db_ops.get_job_statistics()
        
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error("Failed to get public statistics", exception=e)
        return {
            "status": "error",
            "message": "Failed to retrieve statistics",
            "error": str(e)
        }

@app.get("/cors-info") 
async def cors_info():
    """Get CORS configuration info - public endpoint for debugging"""
    with perf_logger.time_operation("cors_info"):
        logger.info("CORS info requested")
        
        if get_settings().is_development():
            return {
                "cors_origins": get_cors_origins(),
                "cors_settings": {
                    "allow_credentials": get_settings().cors_allow_credentials,
                    "max_age": get_settings().cors_max_age
                },
                "environment": get_settings().environment.value,
                "message": "CORS configuration (development mode)"
            }
        else:
            return {
                "cors_enabled": True,
                "origins_count": len(get_cors_origins()),
                "cors_settings": {
                    "allow_credentials": get_settings().cors_allow_credentials,
                    "max_age": get_settings().cors_max_age
                },
                "environment": get_settings().environment.value,
                "message": "CORS configuration (production mode - details hidden)"
            }

# Authentication endpoints
@app.get("/auth/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user info"""
    with perf_logger.time_operation("auth_get_user_info", user_id=user["id"]):
        logger.info("User info requested", user_id=user["id"])
        
        security_logger.log_auth_success(
            user_id=user["id"],
            method="jwt"
        )
        
        return {
            "user": user,
            "message": "Authentication successful"
        }

# Agent Framework Management Endpoints
@app.get("/agents")
async def list_agents():
    """List all registered agents with their capabilities - public endpoint"""
    with perf_logger.time_operation("list_agents"):
        logger.info("Agent list requested")
        
        try:
            # Use agent discovery system for proper agent metadata retrieval
            discovery = get_agent_discovery_system()
            
            # Get discovery statistics
            discovery_stats = discovery.get_discovery_stats()
            
            # Get all agents with metadata
            all_agents = discovery.discover_agents()
            
            # Get enabled agents for environment
            enabled_agents = discovery.get_enabled_agents()
            
            # Format agent information for response
            agents_info = {}
            for identifier, metadata in all_agents.items():
                agents_info[identifier] = {
                    "identifier": metadata.identifier,
                    "name": metadata.name,
                    "description": metadata.description,
                    "class_name": metadata.class_name,
                    "lifecycle_state": metadata.lifecycle_state.value,
                    "supported_environments": [env.value for env in metadata.supported_environments],
                    "version": metadata.version,
                    "enabled": metadata.lifecycle_state.value == "enabled" and not metadata.load_error,
                    "has_error": bool(metadata.load_error),
                    "error_message": metadata.load_error if metadata.load_error else None,
                    "created_at": metadata.created_at.isoformat(),
                    "last_updated": metadata.last_updated.isoformat()
                }
            
            return {
                "status": "success",
                "framework_version": "1.0",
                "discovery_system": "agent_discovery",
                "discovery_stats": discovery_stats,
                "agents": agents_info,
                "summary": {
                    "total_agents": len(all_agents),
                    "enabled_agents": len(enabled_agents),
                    "disabled_agents": len(all_agents) - len(enabled_agents),
                    "current_environment": discovery.current_environment.value
                }
            }
            
        except Exception as e:
            logger.error("Failed to list agents via discovery system", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve agent list via discovery system",
                "error": str(e)
            }

@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get detailed information about a specific agent - public endpoint"""
    with perf_logger.time_operation("get_agent_info", agent_name=agent_name):
        log_agent_access(agent_name, "info_request")
        
        try:
            # Use centralized validation - this endpoint shows all agents including disabled ones
            discovery = get_agent_discovery_system()
            metadata = discovery.get_agent_metadata(agent_name)
            
            if not metadata:
                log_agent_access(agent_name, "info_request", success=False)
                raise AgentNotFoundError(agent_name)
            
            # Format detailed agent information
            agent_info = {
                "identifier": metadata.identifier,
                "name": metadata.name,
                "description": metadata.description,
                "class_name": metadata.class_name,
                "module_path": metadata.module_path,
                "lifecycle_state": metadata.lifecycle_state.value,
                "supported_environments": [env.value for env in metadata.supported_environments],
                "version": metadata.version,
                "enabled": metadata.lifecycle_state.value == "enabled" and not metadata.load_error,
                "has_error": bool(metadata.load_error),
                "error_message": metadata.load_error if metadata.load_error else None,
                "created_at": metadata.created_at.isoformat(),
                "last_updated": metadata.last_updated.isoformat(),
                "metadata_extras": metadata.metadata_extras or {}
            }
            
            # Try to get additional runtime information from agent instance if available
            try:
                registry = get_agent_registry()
                agent_instance = registry.get_agent(agent_name)
                
                if agent_instance:
                    runtime_info = await agent_instance.get_agent_info()
                    agent_info["runtime_info"] = runtime_info
                    agent_info["instance_available"] = True
                else:
                    agent_info["instance_available"] = False
                    
            except Exception as e:
                logger.warning("Could not get runtime agent info", agent_name=agent_name, exception=e)
                agent_info["instance_available"] = False
                agent_info["runtime_error"] = str(e)
            
            return {
                "status": "success",
                "agent": agent_info
            }
            
        except AgentError:
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except Exception as e:
            log_agent_access(agent_name, "info_request", success=False)
            logger.error("Failed to get agent info via discovery system", exception=e, agent_name=agent_name)
            return {
                "status": "error",
                "message": "Failed to retrieve agent information via discovery system",
                "error": str(e)
            }

@app.get("/agents/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status of a specific agent - public endpoint"""
    with perf_logger.time_operation("get_agent_health", agent_name=agent_name):
        log_agent_access(agent_name, "health_check")
        
        try:
            # Use centralized validation - health checks require loaded and enabled agents
            validation_result = validate_agent_exists_and_enabled(agent_name, require_loaded=True)
            agent_instance = validation_result["instance"]
            
            health = await agent_instance.health_check()
            return {
                "status": "success",
                "health": health
            }
            
        except AgentError:
            log_agent_access(agent_name, "health_check", success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except Exception as e:
            log_agent_access(agent_name, "health_check", success=False)
            logger.error("Failed to get agent health", exception=e, agent_name=agent_name)
            return {
                "status": "error",
                "message": "Failed to retrieve agent health",
                "error": str(e)
            }

@app.get("/agents/{agent_id}/schema")
async def get_agent_schema(agent_id: str):
    """Get job data schema for an agent to enable dynamic form generation - public endpoint"""
    with perf_logger.time_operation("get_agent_schema", agent_id=agent_id):
        log_agent_access(agent_id, "schema_request")
        
        try:
            # Use centralized validation - schema requests can work with just discovery data
            # but prefer loaded instances for model access
            discovery = get_agent_discovery_system()
            metadata = discovery.get_agent_metadata(agent_id)
            
            if not metadata:
                log_agent_access(agent_id, "schema_request", success=False)
                raise AgentNotFoundError(agent_id)
            
            # Try to get agent instance for schema extraction (not required)
            agent_instance = None
            try:
                # Get registered agents to access schema information
                registered_agents = get_registered_agents()
                agent_instance = registered_agents.get(agent_id)
                
                if not agent_instance:
                    # Try to get from registry as fallback
                    registry = get_agent_registry()
                    agent_instance = registry.get_agent(agent_id)
            except Exception as e:
                logger.warning("Could not load agent instance for schema", agent_id=agent_id, exception=e)
            
            if not agent_instance:
                return {
                    "status": "success",
                    "message": f"Agent '{agent_id}' found but not currently loaded - schema unavailable",
                    "agent_id": agent_id,
                    "agent_name": metadata.name,
                    "description": metadata.description,
                    "agent_found": True,
                    "instance_available": False,
                    "available_models": [],
                    "schemas": {}
                }
            
            # Extract job data models from the agent
            models = agent_instance.get_models() if hasattr(agent_instance, 'get_models') else {}
            
            schema_info = {
                "agent_id": agent_id,
                "agent_name": metadata.name,
                "description": metadata.description,
                "available_models": list(models.keys()),
                "schemas": {}
            }
            
            # Generate JSON schemas for each model
            for model_name, model_class in models.items():
                try:
                    # Generate Pydantic JSON schema
                    schema = model_class.model_json_schema()
                    
                    # Enhance schema with additional metadata for form generation
                    enhanced_schema = {
                        "model_name": model_name,
                        "model_class": model_class.__name__,
                        "title": schema.get("title", model_name),
                        "description": schema.get("description", f"Job data schema for {model_name}"),
                        "type": schema.get("type", "object"),
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                        "definitions": schema.get("$defs", schema.get("definitions", {}))
                    }
                    
                    # Add form generation hints
                    for prop_name, prop_schema in enhanced_schema["properties"].items():
                        # Only infer form_field_type if not explicitly set
                        if "form_field_type" not in prop_schema:
                            prop_schema["form_field_type"] = _infer_form_field_type(prop_schema)
                    
                    schema_info["schemas"][model_name] = enhanced_schema
                    
                except Exception as e:
                    logger.warning(f"Failed to generate schema for model {model_name}", exception=e)
                    schema_info["schemas"][model_name] = {
                        "error": f"Failed to generate schema: {str(e)}",
                        "model_name": model_name
                    }
            
            if not schema_info["schemas"]:
                return {
                    "status": "success",
                    "message": f"Agent '{agent_id}' has no defined job data models",
                    "instance_available": True,
                    **schema_info
                }
            
            return {
                "status": "success",
                "instance_available": True,
                **schema_info
            }
            
        except AgentError:
            log_agent_access(agent_id, "schema_request", success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except Exception as e:
            log_agent_access(agent_id, "schema_request", success=False)
            logger.error("Failed to get agent schema", exception=e, agent_id=agent_id)
            return {
                "status": "error",
                "message": "Failed to retrieve agent schema",
                "error": str(e)
            }

def _infer_form_field_type(prop_schema: Dict[str, Any]) -> str:
    """Infer appropriate form field type from JSON schema property"""
    prop_type = prop_schema.get("type", "string")
    prop_format = prop_schema.get("format")
    
    # Handle anyOf schemas (e.g., field can be object or null)
    if "anyOf" in prop_schema:
        any_of_types = []
        for option in prop_schema["anyOf"]:
            if "type" in option and option["type"] != "null":
                any_of_types.append(option["type"])
        
        # Use the first non-null type for form field inference
        if any_of_types:
            prop_type = any_of_types[0]
            # If it's an object type in anyOf, use object field type
            if "object" in any_of_types:
                return "object"
    
    if prop_type == "string":
        if prop_format == "password":
            return "password"
        elif prop_format in ["email", "uri", "date", "time", "date-time"]:
            return prop_format
        elif prop_schema.get("enum"):
            return "select"
        elif prop_schema.get("maxLength", 0) > 100:
            return "textarea"
        else:
            return "text"
    elif prop_type == "integer" or prop_type == "number":
        return "number"
    elif prop_type == "boolean":
        return "checkbox"
    elif prop_type == "array":
        return "array"
    elif prop_type == "object":
        return "object"
    else:
        return "text"

# Google AI Configuration endpoints
@app.get("/google-ai/validate")
async def validate_google_ai_setup():
    """Validate Google AI configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("google_ai_validate"):
        logger.info("Google AI configuration validation requested")
        
        try:
            validation_result = validate_google_ai_environment()
            
            # Handle both old and new format of validation_result
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Google AI configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Google AI is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Google AI configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Google AI configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Google AI validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Google AI configuration",
                "error": str(e)
            }

@app.get("/google-ai/models")
async def get_available_models():
    """Get available Google AI models - public endpoint"""
    with perf_logger.time_operation("google_ai_get_models"):
        logger.info("Available models requested")
        
        try:
            google_ai_config = get_google_ai_config()
            
            # Handle both config object and dict return
            if hasattr(google_ai_config, 'get_available_models'):
                models = google_ai_config.get_available_models()
                default_model = google_ai_config.default_model
                use_vertex_ai = google_ai_config.use_vertex_ai
            else:
                # Fallback for dict format
                models = google_ai_config.get("available_models", [])
                default_model = google_ai_config.get("default_model", "gemini-2.0-flash")
                use_vertex_ai = google_ai_config.get("use_vertex_ai", False)
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "Vertex AI" if use_vertex_ai else "Google AI Studio"
            }
            
        except Exception as e:
            logger.error("Failed to get available models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available models",
                "error": str(e)
            }

@app.get("/google-ai/connection-test")
async def test_google_ai_connection():
    """Test connection to Google AI services - public endpoint for setup testing"""
    with perf_logger.time_operation("google_ai_connection_test"):
        logger.info("Google AI connection test requested")
        
        try:
            google_ai_config = get_google_ai_config()
            connection_result = google_ai_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("Google AI connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to Google AI services",
                    "service": connection_result["service"],
                    "model": connection_result["model"],
                    "project": connection_result.get("project")
                }
            else:
                logger.warning("Google AI connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to Google AI services",
                    "error": connection_result["error"],
                    "service": connection_result["service"]
                }
                
        except Exception as e:
            logger.error("Google AI connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

# OpenAI Configuration endpoints
@app.get("/openai/validate")
async def validate_openai_setup():
    """Validate OpenAI configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("openai_validate"):
        logger.info("OpenAI configuration validation requested")
        
        try:
            from config.openai import validate_openai_environment
            validation_result = validate_openai_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("OpenAI configuration validation successful")
                return {
                    "status": "valid",
                    "message": "OpenAI is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("OpenAI configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "OpenAI configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("OpenAI validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate OpenAI configuration",
                "error": str(e)
            }

@app.get("/openai/models")
async def get_available_openai_models():
    """Get available OpenAI models - public endpoint"""
    with perf_logger.time_operation("openai_get_models"):
        logger.info("Available OpenAI models requested")
        
        try:
            from config.openai import get_openai_config
            openai_config = get_openai_config()
            
            models = openai_config.get_available_models()
            default_model = openai_config.default_model
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "OpenAI"
            }
            
        except Exception as e:
            logger.error("Failed to get available OpenAI models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available OpenAI models",
                "error": str(e)
            }

@app.get("/openai/connection-test")
async def test_openai_connection():
    """Test connection to OpenAI services - public endpoint for setup testing"""
    with perf_logger.time_operation("openai_connection_test"):
        logger.info("OpenAI connection test requested")
        
        try:
            from config.openai import get_openai_config
            openai_config = get_openai_config()
            connection_result = openai_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("OpenAI connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to OpenAI services",
                    "service": connection_result["service"],
                    "model": connection_result["model"],
                    "api_key_prefix": connection_result.get("api_key_prefix")
                }
            else:
                logger.warning("OpenAI connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to OpenAI services",
                    "error": connection_result["error"],
                    "service": connection_result["service"]
                }
                
        except Exception as e:
            logger.error("OpenAI connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

# Grok Configuration endpoints
@app.get("/grok/validate")
async def validate_grok_setup():
    """Validate Grok configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("grok_validate"):
        logger.info("Grok configuration validation requested")
        
        try:
            from config.grok import validate_grok_environment
            validation_result = validate_grok_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Grok configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Grok is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Grok configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Grok configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Grok validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Grok configuration",
                "error": str(e)
            }

@app.get("/grok/models")
async def get_available_grok_models():
    """Get available Grok models - public endpoint"""
    with perf_logger.time_operation("grok_get_models"):
        logger.info("Available Grok models requested")
        
        try:
            from config.grok import get_grok_config
            grok_config = get_grok_config()
            
            models = grok_config.get_available_models()
            default_model = grok_config.default_model
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "Grok",
                "provider": "xAI"
            }
            
        except Exception as e:
            logger.error("Failed to get available Grok models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available Grok models",
                "error": str(e)
            }

@app.get("/grok/connection-test")
async def test_grok_connection():
    """Test connection to Grok services - public endpoint for setup testing"""
    with perf_logger.time_operation("grok_connection_test"):
        logger.info("Grok connection test requested")
        
        try:
            from config.grok import get_grok_config
            grok_config = get_grok_config()
            connection_result = grok_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("Grok connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to Grok services",
                    "service": connection_result["service"],
                    "provider": connection_result["provider"],
                    "model": connection_result["model"],
                    "base_url": connection_result.get("base_url"),
                    "api_key_prefix": connection_result.get("api_key_prefix")
                }
            else:
                logger.warning("Grok connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to Grok services",
                    "error": connection_result["error"],
                    "service": connection_result["service"],
                    "provider": connection_result.get("provider", "xAI")
                }
                
        except Exception as e:
            logger.error("Grok connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

# Anthropic Configuration endpoints
@app.get("/anthropic/validate")
async def validate_anthropic_setup():
    """Validate Anthropic configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("anthropic_validate"):
        logger.info("Anthropic configuration validation requested")
        
        try:
            from config.anthropic import validate_anthropic_environment
            validation_result = validate_anthropic_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Anthropic configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Anthropic is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Anthropic configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Anthropic configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Anthropic validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Anthropic configuration",
                "error": str(e)
            }

@app.get("/anthropic/models")
async def get_available_anthropic_models():
    """Get available Anthropic models - public endpoint"""
    with perf_logger.time_operation("anthropic_get_models"):
        logger.info("Available Anthropic models requested")
        
        try:
            from config.anthropic import get_anthropic_config
            anthropic_config = get_anthropic_config()
            
            models = anthropic_config.get_available_models()
            default_model = anthropic_config.default_model
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "Anthropic",
                "provider": "Anthropic"
            }
            
        except Exception as e:
            logger.error("Failed to get available Anthropic models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available Anthropic models",
                "error": str(e)
            }

@app.get("/anthropic/connection-test")
async def test_anthropic_connection():
    """Test connection to Anthropic services - public endpoint for setup testing"""
    with perf_logger.time_operation("anthropic_connection_test"):
        logger.info("Anthropic connection test requested")
        
        try:
            from config.anthropic import get_anthropic_config
            anthropic_config = get_anthropic_config()
            connection_result = anthropic_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("Anthropic connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to Anthropic services",
                    "service": connection_result["service"],
                    "provider": connection_result["provider"],
                    "model": connection_result["model"],
                    "api_key_prefix": connection_result.get("api_key_prefix")
                }
            else:
                logger.warning("Anthropic connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to Anthropic services",
                    "error": connection_result["error"],
                    "service": connection_result["service"],
                    "provider": connection_result.get("provider", "Anthropic")
                }
                
        except Exception as e:
            logger.error("Anthropic connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

# DeepSeek Configuration endpoints
@app.get("/deepseek/validate")
async def validate_deepseek_setup():
    """Validate DeepSeek configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("deepseek_validate"):
        logger.info("DeepSeek configuration validation requested")
        
        try:
            from config.deepseek import validate_deepseek_environment
            validation_result = validate_deepseek_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("DeepSeek configuration validation successful")
                return {
                    "status": "valid",
                    "message": "DeepSeek is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("DeepSeek configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "DeepSeek configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("DeepSeek validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate DeepSeek configuration",
                "error": str(e)
            }

@app.get("/deepseek/models")
async def get_available_deepseek_models():
    """Get available DeepSeek models - public endpoint"""
    with perf_logger.time_operation("deepseek_get_models"):
        logger.info("Available DeepSeek models requested")
        
        try:
            from config.deepseek import get_deepseek_config
            deepseek_config = get_deepseek_config()
            
            models = deepseek_config.get_available_models()
            default_model = deepseek_config.default_model
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "DeepSeek",
                "provider": "DeepSeek"
            }
            
        except Exception as e:
            logger.error("Failed to get available DeepSeek models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available DeepSeek models",
                "error": str(e)
            }

@app.get("/deepseek/connection-test")
async def test_deepseek_connection():
    """Test connection to DeepSeek services - public endpoint for setup testing"""
    with perf_logger.time_operation("deepseek_connection_test"):
        logger.info("DeepSeek connection test requested")
        
        try:
            from config.deepseek import get_deepseek_config
            deepseek_config = get_deepseek_config()
            connection_result = deepseek_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("DeepSeek connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to DeepSeek services",
                    "service": connection_result["service"],
                    "provider": connection_result["provider"],
                    "model": connection_result["model"],
                    "base_url": connection_result.get("base_url"),
                    "api_key_prefix": connection_result.get("api_key_prefix")
                }
            else:
                logger.warning("DeepSeek connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to DeepSeek services",
                    "error": connection_result["error"],
                    "service": connection_result["service"],
                    "provider": connection_result.get("provider", "DeepSeek")
                }
                
        except Exception as e:
            logger.error("DeepSeek connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

# Development-only endpoints
@app.get("/config")
async def get_config_info():
    """Get configuration information - development only"""
    if not settings.is_development():
        logger.warning("Configuration endpoint accessed in non-development environment")
        raise HTTPException(status_code=404, detail="Not found")
    
    with perf_logger.time_operation("get_config_info"):
        logger.info("Configuration info requested")
        
        validate_google_ai_environment()
        discovery_status = get_discovery_status()
        
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "framework_version": "1.0",
            "environment": settings.environment.value,
            "debug": settings.debug,
            "cors_origins_count": len(cors_origins),
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "log_level": settings.log_level.value,
            "agent_discovery": discovery_status,
            "performance_metrics": perf_logger.get_metrics_summary(),
            "message": "Configuration info (development mode only)"
        }

@app.get("/logs/metrics")
async def get_logging_metrics():
    """Get logging and performance metrics - development only"""
    if not settings.is_development():
        logger.warning("Logging metrics endpoint accessed in non-development environment")
        raise HTTPException(status_code=404, detail="Not found")
    
    with perf_logger.time_operation("get_logging_metrics"):
        logger.info("Logging metrics requested")
        
        metrics = perf_logger.get_metrics_summary()
        
        return {
            "performance_metrics": metrics,
            "total_operations": sum(m["count"] for m in metrics.values()),
            "average_response_time": sum(m["average_time"] for m in metrics.values()) / len(metrics) if metrics else 0,
            "message": "Logging metrics (development mode only)"
        }

# Job Management Endpoints
@app.post("/jobs", response_model=JobCreateResponse)
async def create_job(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new job for processing"""
    with perf_logger.time_operation("create_job", user_id=user["id"]):
        log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"])
        
        try:
            # Use centralized validation - job creation requires enabled agents
            validation_result = validate_agent_exists_and_enabled(request.agent_identifier)
            agent_metadata = validation_result["metadata"]
            
            # Validate job data against agent schema requirements
            schema_validation_result = await _validate_job_data_against_agent_schema(
                request.agent_identifier, 
                request.data
            )
            
            if not schema_validation_result["valid"]:
                log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
                logger.warning(
                    "Job data validation failed",
                    agent_identifier=request.agent_identifier,
                    user_id=user["id"],
                    validation_errors=schema_validation_result["errors"]
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Job data validation failed",
                        "agent_identifier": request.agent_identifier,
                        "validation_errors": schema_validation_result["errors"],
                        "expected_schema": schema_validation_result.get("schema_info")
                    }
                )
            
            # Generate job ID as proper UUID
            import uuid
            job_id = str(uuid.uuid4())
            
            # Get database operations
            db_ops = get_database_operations()
            
            # Create job in database with agent_identifier
            job_data = {
                "id": job_id,
                "user_id": user["id"],
                "agent_identifier": request.agent_identifier,
                "status": "pending",
                "data": request.data,
                "priority": request.priority or 0,
                "tags": request.tags or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            created_job = await db_ops.create_job(job_data)
            
            # Submit job to pipeline for processing
            pipeline = get_job_pipeline()
            if pipeline and pipeline.is_running:
                await pipeline.submit_job(
                    job_id=created_job["id"],
                    user_id=created_job["user_id"],
                    agent_name=created_job["agent_identifier"],
                    job_data=created_job["data"],
                    priority=created_job.get("priority", 5),
                    tags=created_job.get("tags", [])
                )
                logger.info("Job submitted to pipeline", job_id=job_id, user_id=user["id"], agent_identifier=request.agent_identifier)
            else:
                logger.warning("Job created but pipeline not running", job_id=job_id, user_id=user["id"])
            
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"])
            
            return JobCreateResponse(
                success=True,
                message="Job created successfully",
                job_id=job_id,
                job=created_job
            )
            
        except AgentError:
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except HTTPException:
            raise
        except Exception as e:
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
            logger.error("Job creation failed", exception=e, user_id=user["id"], agent_identifier=getattr(request, 'agent_identifier', 'unknown'))
            raise HTTPException(status_code=500, detail=f"Job creation failed: {str(e)}")

async def _validate_job_data_against_agent_schema(agent_identifier: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate job data against agent's defined schema requirements.
    
    Returns:
        dict: Validation result with 'valid', 'errors', 'model_used', and 'schema_info' fields
    """
    try:
        # Get registered agents to access schema information
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_identifier)
        
        if not agent_instance:
            # Try to get from registry as fallback
            registry = get_agent_registry()
            agent_instance = registry.get_agent(agent_identifier)
        
        if not agent_instance:
            # Agent not loaded - allow but log warning
            logger.warning(f"Agent '{agent_identifier}' not loaded for validation - allowing job creation")
            return {
                "valid": True,
                "warnings": [f"Agent '{agent_identifier}' not loaded - schema validation skipped"],
                "model_used": None
            }
        
        # Extract job data models from the agent
        models = agent_instance.get_models() if hasattr(agent_instance, 'get_models') else {}
        
        if not models:
            # No models defined - allow generic data
            logger.info(f"Agent '{agent_identifier}' has no defined models - allowing generic job data")
            return {
                "valid": True,
                "warnings": [f"Agent '{agent_identifier}' has no defined job data models"],
                "model_used": None
            }
        
        # Try to find the most appropriate model for validation
        # Priority: exact match by model name, single model, first available model
        model_to_use = None
        model_name = None
        
        # If only one model, use it
        if len(models) == 1:
            model_name, model_to_use = next(iter(models.items()))
        else:
            # Use the first model available (agents should typically define one primary model)
            model_name, model_to_use = next(iter(models.items()))
        
        # Validate the job data against the selected model
        try:
            # Create an instance of the model to validate the data
            validated_data = model_to_use(**job_data)
            
            return {
                "valid": True,
                "model_used": model_name,
                "validated_data": validated_data.dict(),
                "schema_info": {
                    "model_name": model_name,
                    "available_models": list(models.keys())
                }
            }
            
        except Exception as validation_error:
            # Extract meaningful validation errors
            errors = []
            if hasattr(validation_error, 'errors'):
                # Pydantic validation errors
                for error in validation_error.errors():
                    field_path = " -> ".join(str(loc) for loc in error['loc'])
                    errors.append({
                        "field": field_path,
                        "message": error['msg'],
                        "type": error['type'],
                        "input": error.get('input')
                    })
            else:
                errors.append({
                    "field": "general",
                    "message": str(validation_error),
                    "type": "validation_error"
                })
            
            # Get schema information for helpful error response
            schema_info = {
                "model_name": model_name,
                "available_models": list(models.keys()),
                "schema": model_to_use.model_json_schema() if hasattr(model_to_use, 'model_json_schema') else None
            }
            
            return {
                "valid": False,
                "errors": errors,
                "model_used": model_name,
                "schema_info": schema_info
            }
        
    except Exception as e:
        logger.error(f"Error during job data validation for agent '{agent_identifier}'", exception=e)
        return {
            "valid": True,  # Allow on system errors
            "warnings": [f"Validation system error: {str(e)}"],
            "model_used": None
        }

@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List jobs for the current user"""
    with perf_logger.time_operation("list_jobs", user_id=user["id"]):
        logger.info("Job list requested", user_id=user["id"], limit=limit, offset=offset)
        
        try:
            db_ops = get_database_operations()
            jobs = await db_ops.get_user_jobs(user["id"], limit=limit, offset=offset)
            
            job_responses = []
            for job in jobs:
                job_responses.append(JobResponse(
                    id=job["id"],
                    status=job["status"],
                    agent_identifier=job.get("agent_identifier", "unknown"),
                    data=job["data"],
                    result=job.get("result"),
                    error_message=job.get("error_message"),
                    created_at=job["created_at"],
                    updated_at=job["updated_at"]
                ))
            
            logger.info("Job list retrieved", user_id=user["id"], count=len(job_responses))
            
            return JobListResponse(
                success=True,
                message="Jobs retrieved successfully",
                jobs=job_responses,
                total_count=len(job_responses)
            )
            
        except Exception as e:
            logger.error("Job list retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve jobs: {str(e)}")

@app.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific job"""
    with perf_logger.time_operation("get_job", user_id=user["id"]):
        logger.info("Job detail requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                logger.warning("Job not found or access denied", job_id=job_id, user_id=user["id"])
                raise HTTPException(status_code=404, detail="Job not found or access denied")
            
            logger.info("Job detail retrieved", job_id=job_id, user_id=user["id"], status=job.get("status"))
            
            return JobDetailResponse(
                success=True,
                message="Job retrieved successfully",
                job=job
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")

@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific job"""
    with perf_logger.time_operation("delete_job", user_id=user["id"], job_id=job_id):
        logger.info("Job deletion requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            success = await db_ops.delete_job(job_id, user_id=user["id"])
            
            if not success:
                raise HTTPException(status_code=404, detail="Job not found")
            
            logger.info("Job deleted successfully", job_id=job_id, user_id=user["id"])
            
            return {
                "success": True,
                "message": "Job deleted successfully",
                "job_id": job_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job deletion failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

@app.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get status of a specific job"""
    with perf_logger.time_operation("get_job_status", user_id=user["id"], job_id=job_id):
        logger.info("Job status requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return {
                "success": True,
                "message": "Job status retrieved",
                "data": {
                    "status": job["status"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job status retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.post("/jobs/batch/status")
async def get_batch_job_status(
    request: Dict[str, List[str]],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get status of multiple jobs in batch"""
    with perf_logger.time_operation("get_batch_job_status", user_id=user["id"]):
        job_ids = request.get("job_ids", [])
        logger.info("Batch job status requested", job_ids=job_ids, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            batch_status = {}
            
            for job_id in job_ids:
                try:
                    job = await db_ops.get_job(job_id, user_id=user["id"])
                    if job:
                        batch_status[job_id] = {
                            "status": job["status"],
                            "updated_at": job["updated_at"]
                        }
                except Exception:
                    # Job not found or error - skip it
                    continue
            
            return {
                "success": True,
                "message": "Batch job status retrieved",
                "data": batch_status
            }
            
        except Exception as e:
            logger.error("Batch job status retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get batch job status: {str(e)}")

@app.get("/jobs/minimal")
async def get_jobs_minimal(
    limit: int = 50,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get minimal job data for polling (lighter weight)"""
    with perf_logger.time_operation("get_jobs_minimal", user_id=user["id"]):
        logger.info("Minimal job list requested", user_id=user["id"], limit=limit, offset=offset)
        
        try:
            db_ops = get_database_operations()
            jobs = await db_ops.get_user_jobs(user["id"], limit=limit, offset=offset)
            
            minimal_jobs = []
            for job in jobs:
                minimal_jobs.append({
                    "id": job["id"],
                    "status": job["status"],
                    "updated_at": job["updated_at"]
                })
            
            return {
                "success": True,
                "message": "Minimal jobs retrieved",
                "data": minimal_jobs
            }
            
        except Exception as e:
            logger.error("Minimal job list retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve minimal jobs: {str(e)}")

@app.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Retry a failed job"""
    with perf_logger.time_operation("retry_job", user_id=user["id"], job_id=job_id):
        logger.info("Job retry requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if job["status"] not in ["failed", "cancelled"]:
                raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")
            
            # Get agent_identifier from the job data
            agent_identifier = job.get("agent_identifier", "unknown")
            log_agent_access(agent_identifier, "job_retry", user_id=user["id"])
            
            # Use centralized validation - job retry requires enabled agents
            validation_result = validate_agent_exists_and_enabled(agent_identifier)
            
            # Validate existing job data against current agent schema requirements
            schema_validation_result = await _validate_job_data_against_agent_schema(
                agent_identifier, 
                job["data"]
            )
            
            if not schema_validation_result["valid"]:
                log_agent_access(agent_identifier, "job_retry", user_id=user["id"], success=False)
                logger.warning(
                    "Job retry failed - existing data no longer valid",
                    job_id=job_id,
                    agent_identifier=agent_identifier,
                    user_id=user["id"],
                    validation_errors=schema_validation_result["errors"]
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Cannot retry job - existing job data no longer meets agent requirements",
                        "job_id": job_id,
                        "agent_identifier": agent_identifier,
                        "validation_errors": schema_validation_result["errors"],
                        "expected_schema": schema_validation_result.get("schema_info"),
                        "suggestion": "The agent schema may have changed since this job was created. Please create a new job with updated data."
                    }
                )
            
            # Update job status to pending and resubmit
            await db_ops.update_job_status(job_id, "pending")
            
            # Resubmit to pipeline using agent_identifier
            pipeline = get_job_pipeline()
            
            success = await pipeline.submit_job(
                job_id=job_id,
                user_id=user["id"],
                agent_name=agent_identifier,  # Use agent_identifier directly
                job_data=job["data"],
                priority=job.get("priority", 5),
                tags=job.get("tags", [])
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to requeue job for processing")
            
            # Get updated job
            updated_job = await db_ops.get_job(job_id, user_id=user["id"])
            
            job_response = JobResponse(
                id=updated_job["id"],
                status=updated_job["status"],
                agent_identifier=updated_job.get("agent_identifier", "unknown"),
                data=updated_job["data"],
                result=updated_job.get("result"),
                error_message=updated_job.get("error_message"),
                created_at=updated_job["created_at"],
                updated_at=updated_job["updated_at"]
            )
            
            logger.info("Job retried successfully", 
                       job_id=job_id, 
                       user_id=user["id"], 
                       agent_identifier=agent_identifier,
                       validation_model=schema_validation_result.get("model_used"))
            
            return {
                "success": True,
                "message": "Job retried successfully",
                "data": job_response
            }
            
        except AgentError:
            if 'agent_identifier' in locals():
                log_agent_access(agent_identifier, "job_retry", user_id=user["id"], success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except HTTPException:
            raise
        except Exception as e:
            if 'agent_identifier' in locals():
                log_agent_access(agent_identifier, "job_retry", user_id=user["id"], success=False)
            logger.error("Job retry failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")

@app.post("/jobs/{job_id}/rerun")
async def rerun_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Rerun any job by creating a new job with the same configuration"""
    with perf_logger.time_operation("rerun_job", user_id=user["id"], job_id=job_id):
        logger.info("Job rerun requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            original_job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not original_job:
                raise HTTPException(status_code=404, detail="Original job not found")
            
            # Get agent_identifier from the original job
            agent_identifier = original_job.get("agent_identifier", "unknown")
            log_agent_access(agent_identifier, "job_rerun", user_id=user["id"])
            
            # Use centralized validation - job rerun requires enabled agents
            validation_result = validate_agent_exists_and_enabled(agent_identifier)
            
            # Validate original job data against current agent schema requirements
            schema_validation_result = await _validate_job_data_against_agent_schema(
                agent_identifier, 
                original_job["data"]
            )
            
            if not schema_validation_result["valid"]:
                log_agent_access(agent_identifier, "job_rerun", user_id=user["id"], success=False)
                logger.warning(
                    "Job rerun failed - original data no longer valid",
                    job_id=job_id,
                    agent_identifier=agent_identifier,
                    user_id=user["id"],
                    validation_errors=schema_validation_result["errors"]
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Cannot rerun job - original job data no longer meets agent requirements",
                        "original_job_id": job_id,
                        "agent_identifier": agent_identifier,
                        "validation_errors": schema_validation_result["errors"],
                        "expected_schema": schema_validation_result.get("schema_info"),
                        "suggestion": "The agent schema may have changed since this job was created. Please create a new job with updated data."
                    }
                )
            
            # Generate new job ID
            import uuid
            new_job_id = str(uuid.uuid4())
            
            # Create new job data based on original job
            new_job_data = {
                "id": new_job_id,
                "user_id": user["id"],
                "agent_identifier": agent_identifier,
                "status": "pending",
                "data": original_job["data"],  # Copy original job data
                "priority": original_job.get("priority", 0),
                "tags": original_job.get("tags", []),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Create the new job in database
            created_job = await db_ops.create_job(new_job_data)
            
            # Submit new job to pipeline
            pipeline = get_job_pipeline()
            if pipeline and pipeline.is_running:
                success = await pipeline.submit_job(
                    job_id=new_job_id,
                    user_id=user["id"],
                    agent_name=agent_identifier,
                    job_data=original_job["data"],
                    priority=original_job.get("priority", 5),
                    tags=original_job.get("tags", [])
                )
                
                if not success:
                    # Clean up the created job if pipeline submission fails
                    await db_ops.delete_job(new_job_id, user_id=user["id"])
                    raise HTTPException(status_code=500, detail="Failed to submit rerun job to processing pipeline")
                
                logger.info("Rerun job submitted to pipeline", 
                           new_job_id=new_job_id, 
                           original_job_id=job_id,
                           user_id=user["id"], 
                           agent_identifier=agent_identifier)
            else:
                logger.warning("Rerun job created but pipeline not running", 
                              new_job_id=new_job_id, 
                              original_job_id=job_id,
                              user_id=user["id"])
            
            # Create response object
            job_response = JobResponse(
                id=created_job["id"],
                status=created_job["status"],
                agent_identifier=created_job.get("agent_identifier", "unknown"),
                data=created_job["data"],
                result=created_job.get("result"),
                error_message=created_job.get("error_message"),
                created_at=created_job["created_at"],
                updated_at=created_job["updated_at"]
            )
            
            logger.info("Job rerun successful", 
                       new_job_id=new_job_id,
                       original_job_id=job_id,
                       user_id=user["id"], 
                       agent_identifier=agent_identifier,
                       original_status=original_job["status"])
            
            return {
                "success": True,
                "message": "Job rerun successful - new job created",
                "original_job_id": job_id,
                "new_job_id": new_job_id,
                "original_job_status": original_job["status"],
                "data": job_response
            }
            
        except AgentError:
            if 'agent_identifier' in locals():
                log_agent_access(agent_identifier, "job_rerun", user_id=user["id"], success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except HTTPException:
            raise
        except Exception as e:
            if 'agent_identifier' in locals():
                log_agent_access(agent_identifier, "job_rerun", user_id=user["id"], success=False)
            logger.error("Job rerun failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to rerun job: {str(e)}")

@app.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get logs for a specific job"""
    with perf_logger.time_operation("get_job_logs", user_id=user["id"], job_id=job_id):
        logger.info("Job logs requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # For now, return basic status information as logs
            # In a full implementation, you'd have actual log storage
            logs = [
                f"Job {job_id} created at {job['created_at']}",
                f"Current status: {job['status']}",
                f"Last updated: {job['updated_at']}"
            ]
            
            if job.get("error_message"):
                logs.append(f"Error: {job['error_message']}")
            
            if job.get("result"):
                logs.append(f"Result available: {len(str(job['result']))} characters")
            
            return {
                "success": True,
                "message": "Job logs retrieved",
                "data": logs
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job logs retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve job logs: {str(e)}")

@app.get("/pipeline/status")
async def get_pipeline_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get job pipeline status and metrics"""
    with perf_logger.time_operation("get_pipeline_status", user_id=user["id"]):
        logger.info("Pipeline status requested", user_id=user["id"])
        
        try:
            pipeline = get_job_pipeline()
            status = pipeline.get_pipeline_status()
            
            return {
                "success": True,
                "message": "Pipeline status retrieved",
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Pipeline status retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")

@app.get("/pipeline/metrics")
async def get_pipeline_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """Get detailed pipeline metrics"""
    with perf_logger.time_operation("get_pipeline_metrics", user_id=user["id"]):
        logger.info("Pipeline metrics requested", user_id=user["id"])
        
        try:
            pipeline = get_job_pipeline()
            status = pipeline.get_pipeline_status()
            
            return {
                "success": True,
                "message": "Pipeline metrics retrieved",
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Pipeline metrics retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get pipeline metrics: {str(e)}")

@app.get("/config/agents")
async def list_agent_configs(user: Dict[str, Any] = Depends(get_current_user)):
    """Get list of all agent configurations"""
    with perf_logger.time_operation("list_agent_configs", user_id=user["id"]):
        logger.info("Agent configurations list requested", user_id=user["id"])
        
        try:
            config_manager = get_agent_config_manager()
            agent_names = config_manager.list_configs()
            
            configs = {}
            for agent_name in agent_names:
                config = config_manager.get_config(agent_name)
                configs[agent_name] = {
                    "name": config.name,
                    "description": config.description,
                    "profile": config.profile.value,
                    "performance_mode": config.performance_mode.value,
                    "enabled": config.enabled
                }
            
            return {
                "success": True,
                "message": "Agent configurations retrieved",
                "configs": configs,
                "total_count": len(configs)
            }
            
        except Exception as e:
            logger.error("Agent configs list retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve agent configs: {str(e)}")

@app.get("/config/agents/{agent_name}")
async def get_agent_config_endpoint(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed configuration for a specific agent"""
    with perf_logger.time_operation("get_agent_config", user_id=user["id"], agent_name=agent_name):
        logger.info("Agent configuration requested", agent_name=agent_name, user_id=user["id"])
        
        try:
            config = get_agent_config(agent_name)
            
            return {
                "success": True,
                "message": f"Configuration retrieved for agent: {agent_name}",
                "config": config.to_dict()
            }
            
        except Exception as e:
            logger.error("Agent config retrieval failed", exception=e, agent_name=agent_name, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve config for {agent_name}: {str(e)}")

@app.put("/config/agents/{agent_name}")
async def update_agent_config_endpoint(
    agent_name: str,
    config_updates: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update configuration for a specific agent"""
    with perf_logger.time_operation("update_agent_config", user_id=user["id"], agent_name=agent_name):
        logger.info("Agent configuration update requested", agent_name=agent_name, user_id=user["id"])
        
        try:
            config_manager = get_agent_config_manager()
            
            # Validate the current config first
            current_config = config_manager.get_config(agent_name)
            
            # Apply updates temporarily for validation
            temp_config = current_config.from_dict({**current_config.to_dict(), **config_updates})
            validation_errors = config_manager.validate_config(temp_config)
            
            if validation_errors:
                return {
                    "success": False,
                    "message": "Configuration validation failed",
                    "errors": validation_errors
                }
            
            # Apply the updates
            success = config_manager.update_config(agent_name, config_updates)
            
            if success:
                return {
                    "success": True,
                    "message": f"Configuration updated for agent: {agent_name}",
                    "config": config_manager.get_config(agent_name).to_dict()
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to update configuration")
            
        except Exception as e:
            logger.error("Agent config update failed", exception=e, agent_name=agent_name, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to update config for {agent_name}: {str(e)}")

@app.post("/config/agents/{agent_name}/save")
async def save_agent_config_endpoint(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Save agent configuration to file"""
    with perf_logger.time_operation("save_agent_config", user_id=user["id"], agent_name=agent_name):
        logger.info("Agent configuration save requested", agent_name=agent_name, user_id=user["id"])
        
        try:
            config_manager = get_agent_config_manager()
            success = config_manager.save_config(agent_name)
            
            if success:
                return {
                    "success": True,
                    "message": f"Configuration saved for agent: {agent_name}"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save configuration")
            
        except Exception as e:
            logger.error("Agent config save failed", exception=e, agent_name=agent_name, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to save config for {agent_name}: {str(e)}")

@app.get("/config/profiles")
async def get_agent_profiles(user: Dict[str, Any] = Depends(get_current_user)):
    """Get available agent configuration profiles"""
    with perf_logger.time_operation("get_agent_profiles", user_id=user["id"]):
        logger.info("Agent profiles requested", user_id=user["id"])
        
        try:
            config_manager = get_agent_config_manager()
            
            profiles = {}
            for profile in AgentProfile:
                profiles[profile.value] = {
                    "name": profile.value,
                    "defaults": config_manager.get_profile_defaults(profile)
                }
            
            performance_modes = [mode.value for mode in AgentPerformanceMode]
            
            return {
                "success": True,
                "message": "Agent profiles retrieved",
                "profiles": profiles,
                "performance_modes": performance_modes
            }
            
        except Exception as e:
            logger.error("Agent profiles retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve agent profiles: {str(e)}")

@app.post("/config/agents/{agent_name}/profile")
async def set_agent_profile(
    agent_name: str,
    profile_data: Dict[str, str],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Set agent configuration profile"""
    with perf_logger.time_operation("set_agent_profile", user_id=user["id"], agent_name=agent_name):
        logger.info("Agent profile update requested", agent_name=agent_name, user_id=user["id"])
        
        try:
            profile_name = profile_data.get("profile")
            performance_mode = profile_data.get("performance_mode")
            
            if not profile_name:
                raise HTTPException(status_code=400, detail="Profile name is required")
            
            # Validate profile
            try:
                profile = AgentProfile(profile_name)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid profile: {profile_name}")
            
            # Validate performance mode if provided
            if performance_mode:
                try:
                    perf_mode = AgentPerformanceMode(performance_mode)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid performance mode: {performance_mode}")
            
            # Update configuration
            updates = {"profile": profile_name}
            if performance_mode:
                updates["performance_mode"] = performance_mode
            
            config_manager = get_agent_config_manager()
            success = config_manager.update_config(agent_name, updates)
            
            if success:
                return {
                    "success": True,
                    "message": f"Profile updated for agent: {agent_name}",
                    "config": config_manager.get_config(agent_name).to_dict()
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to update profile")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Agent profile update failed", exception=e, agent_name=agent_name, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to update profile for {agent_name}: {str(e)}")

@app.get("/static-info")
async def get_static_file_info_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """Get information about static file serving configuration"""
    with perf_logger.time_operation("get_static_file_info", user_id=user["id"]):
        logger.info("Static file info requested", user_id=user["id"])
        
        try:
            static_info = get_static_file_info()
            return {
                "success": True,
                "message": "Static file information retrieved",
                "static_file_config": static_info
            }
        except Exception as e:
            logger.error("Static file info retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve static file info: {str(e)}")

@app.post("/jobs/validate")
async def validate_job_data(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate job data against agent schema without creating a job"""
    with perf_logger.time_operation("validate_job_data", user_id=user["id"]):
        log_agent_access(request.agent_identifier, "job_validation", user_id=user["id"])
        
        try:
            # Use centralized validation - job validation requires enabled agents
            validation_result = validate_agent_exists_and_enabled(request.agent_identifier)
            
            # Validate job data against agent schema requirements
            schema_validation_result = await _validate_job_data_against_agent_schema(
                request.agent_identifier, 
                request.data
            )
            
            logger.info("Job data validation completed", 
                       user_id=user["id"], 
                       agent_identifier=request.agent_identifier,
                       valid=schema_validation_result["valid"],
                       model_used=schema_validation_result.get("model_used"))
            
            return {
                "success": True,
                "message": "Job data validation completed",
                "validation_result": {
                    "valid": schema_validation_result["valid"],
                    "agent_identifier": request.agent_identifier,
                    "model_used": schema_validation_result.get("model_used"),
                    "errors": schema_validation_result.get("errors", []),
                    "warnings": schema_validation_result.get("warnings", []),
                    "schema_info": schema_validation_result.get("schema_info"),
                    "validated_data": schema_validation_result.get("validated_data")
                }
            }
            
        except AgentError:
            log_agent_access(request.agent_identifier, "job_validation", user_id=user["id"], success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except HTTPException:
            raise
        except Exception as e:
            log_agent_access(request.agent_identifier, "job_validation", user_id=user["id"], success=False)
            logger.error("Job data validation failed", exception=e, user_id=user["id"], agent_identifier=getattr(request, 'agent_identifier', 'unknown'))
            raise HTTPException(status_code=500, detail=f"Job data validation failed: {str(e)}")

# Set up static file serving after all API routes are defined
# This must be done before the global exception handler
setup_static_file_serving(app)

# Custom exception handlers
@app.exception_handler(AgentError)
async def agent_error_handler(request, exc: AgentError):
    """Custom handler for agent-specific errors with consistent formatting"""
    error_type = type(exc).__name__
    
    # Log the agent error with context
    logger.warning(
        f"Agent error: {error_type}",
        agent_identifier=getattr(exc, 'agent_identifier', 'unknown'),
        lifecycle_state=getattr(exc, 'lifecycle_state', None),
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code
    )
    
    # Create consistent error response format
    error_response = {
        "error": error_type,
        "message": str(exc.detail),
        "status_code": exc.status_code,
        "agent_identifier": getattr(exc, 'agent_identifier', 'unknown')
    }
    
    # Add lifecycle state for disabled agent errors
    if hasattr(exc, 'lifecycle_state') and exc.lifecycle_state:
        error_response["lifecycle_state"] = exc.lifecycle_state
    
    # Add helpful context based on error type
    if isinstance(exc, AgentNotFoundError):
        error_response["suggestion"] = "Check available agents using GET /agents endpoint"
    elif isinstance(exc, AgentDisabledError):
        error_response["suggestion"] = "Agent is not enabled or has load errors. Check agent status or contact administrator."
    elif isinstance(exc, AgentNotLoadedError):
        error_response["suggestion"] = "Agent exists but is not currently loaded. Try again later or contact administrator."
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with comprehensive logging"""
    logger.error(
        "Unhandled exception occurred",
        exception=exc,
        path=request.url.path,
        method=request.method
    )
    
    if isinstance(exc, (HTTPException,)) and exc.status_code in [401, 403]:
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

# Meta Llama Configuration endpoints
@app.get("/llama/validate")
async def validate_llama_setup():
    """Validate Meta Llama configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("llama_validate"):
        logger.info("Meta Llama configuration validation requested")
        
        try:
            from config.llama import validate_llama_environment
            validation_result = validate_llama_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Meta Llama configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Meta Llama is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Meta Llama configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Meta Llama configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Meta Llama validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Meta Llama configuration",
                "error": str(e)
            }

@app.get("/llama/models")
async def get_available_llama_models():
    """Get available Meta Llama models - public endpoint"""
    with perf_logger.time_operation("llama_get_models"):
        logger.info("Available Meta Llama models requested")
        
        try:
            from config.llama import get_llama_config
            llama_config = get_llama_config()
            
            models = llama_config.get_available_models()
            default_model = llama_config.default_model
            
            return {
                "status": "success",
                "available_models": models,
                "default_model": default_model,
                "service": "Meta Llama",
                "provider": "Meta",
                "api_provider": llama_config.api_provider
            }
            
        except Exception as e:
            logger.error("Failed to get available Meta Llama models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available Meta Llama models",
                "error": str(e)
            }

@app.get("/llama/connection-test")
async def test_llama_connection():
    """Test connection to Meta Llama services - public endpoint for setup testing"""
    with perf_logger.time_operation("llama_connection_test"):
        logger.info("Meta Llama connection test requested")
        
        try:
            from config.llama import get_llama_config
            llama_config = get_llama_config()
            connection_result = llama_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("Meta Llama connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to Meta Llama services",
                    "service": connection_result["service"],
                    "provider": connection_result["provider"],
                    "model": connection_result["model"],
                    "base_url": connection_result.get("base_url"),
                    "api_provider": connection_result.get("api_provider"),
                    "api_key_prefix": connection_result.get("api_key_prefix")
                }
            else:
                logger.warning("Meta Llama connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to Meta Llama services",
                    "error": connection_result["error"],
                    "service": connection_result["service"],
                    "provider": connection_result.get("provider", "Meta")
                }
                
        except Exception as e:
            logger.error("Meta Llama connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Connection test failed",
                "error": str(e)
            }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.is_development(),
        log_level=settings.log_level.value.lower()
    ) 