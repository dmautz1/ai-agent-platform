"""
AI Agent Template - Main Application

Simplified main application using the new self-contained agent framework.
Agents are automatically discovered and registered from the agents/ directory.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging.config
from typing import List, Optional, Dict, Any
from datetime import datetime

from auth import get_current_user, get_optional_user
from config.environment import get_settings, validate_required_settings, get_logging_config
from logging_system import (
    setup_logging_middleware, get_logger, get_performance_logger,
    get_security_logger, log_startup_info, log_shutdown_info
)
from config.adk import validate_adk_environment, get_adk_config
from agent import get_agent_registry
from agent_framework import register_agent_endpoints, get_all_agent_info
from agents import discover_and_register_agents, get_discovery_status
from job_pipeline import start_job_pipeline, stop_job_pipeline, get_job_pipeline
from database import get_database_operations
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

def get_cors_origins() -> List[str]:
    """Get CORS origins for the application - used by tests and configuration."""
    return settings.get_cors_origins()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI Agent Template with Self-Contained Agent Framework v2.0",
    version=settings.app_version,
    debug=settings.debug
)

# CORS Configuration
cors_origins = get_cors_origins()

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

@app.on_startup
async def startup_event():
    """Application startup with automatic agent discovery and registration"""
    log_startup_info()
    
    logger.info(
        "Starting AI Agent Template v2.0",
        cors_origins_count=len(cors_origins),
        debug_mode=settings.debug,
        environment=settings.environment.value
    )
    
    try:
        # Get agent registry
        registry = get_agent_registry()
        
        # Auto-discover and register agents from agents/ directory
        discovery_result = discover_and_register_agents(registry)
        
        logger.info(
            "Agent auto-discovery completed",
            agents_discovered=discovery_result['total_registered'],
            errors=discovery_result['total_errors'],
            agent_files_found=discovery_result['agent_files_found']
        )
        
        # Auto-register all agent endpoints with FastAPI
        endpoint_count = register_agent_endpoints(app, registry)
        
        logger.info(
            "Agent framework initialization completed",
            total_agents=discovery_result['total_registered'],
            total_endpoints=endpoint_count,
            framework_version="2.0"
        )
        
        # Log any discovery errors
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

@app.on_shutdown
async def shutdown_event():
    """Application shutdown event with comprehensive logging"""
    logger.info("Beginning application shutdown")
    
    # Stop job processing pipeline
    try:
        await stop_job_pipeline()
        logger.info("Job processing pipeline stopped")
    except Exception as e:
        logger.error("Error stopping job pipeline", exception=e)
    
    log_shutdown_info()

# Core Application Endpoints
@app.get("/")
async def root():
    """Health check endpoint - public"""
    with perf_logger.time_operation("health_check_root"):
        logger.info("Root health check requested")
        
        return {
            "message": f"{settings.app_name} v2.0 is running",
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "framework_version": "2.0",
            "agent_framework": "self-contained",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint - public"""
    with perf_logger.time_operation("health_check_detailed"):
        logger.info("Detailed health check requested")
        
        # Get performance metrics summary
        metrics_summary = perf_logger.get_metrics_summary()
        
        # Get agent discovery status
        discovery_status = get_discovery_status()
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "framework_version": "2.0",
            "cors_origins": len(cors_origins),
            "debug": settings.debug,
            "agent_status": discovery_status,
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": metrics_summary if settings.is_development() else {}
        }

@app.get("/cors-info") 
async def cors_info():
    """Get CORS configuration info - public endpoint for debugging"""
    with perf_logger.time_operation("cors_info"):
        logger.info("CORS info requested")
        
        if settings.is_development():
            return {
                "cors_origins": cors_origins,
                "environment": settings.environment.value,
                "allow_credentials": settings.cors_allow_credentials,
                "max_age": settings.cors_max_age,
                "message": "CORS configuration (development mode)"
            }
        else:
            return {
                "cors_enabled": True,
                "origins_count": len(cors_origins),
                "environment": settings.environment.value,
                "allow_credentials": settings.cors_allow_credentials,
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
            discovery_status = get_discovery_status()
            agent_info = get_all_agent_info()
            
            return {
                "status": "success",
                "framework_version": "2.0",
                "discovery_status": discovery_status,
                "agents": agent_info,
                "total_agents": discovery_status['total_agents']
            }
            
        except Exception as e:
            logger.error("Failed to list agents", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve agent list",
                "error": str(e)
            }

@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get detailed information about a specific agent - public endpoint"""
    with perf_logger.time_operation("get_agent_info", agent_name=agent_name):
        logger.info("Agent info requested", agent_name=agent_name)
        
        try:
            registry = get_agent_registry()
            agent = registry.get_agent(agent_name)
            
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
            info = await agent.get_agent_info()
            return {
                "status": "success",
                "agent": info
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get agent info", exception=e, agent_name=agent_name)
            return {
                "status": "error",
                "message": "Failed to retrieve agent information",
                "error": str(e)
            }

@app.get("/agents/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status of a specific agent - public endpoint"""
    with perf_logger.time_operation("get_agent_health", agent_name=agent_name):
        logger.info("Agent health check requested", agent_name=agent_name)
        
        try:
            registry = get_agent_registry()
            agent = registry.get_agent(agent_name)
            
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
            
            health = await agent.health_check()
            return {
                "status": "success",
                "health": health
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get agent health", exception=e, agent_name=agent_name)
            return {
                "status": "error",
                "message": "Failed to retrieve agent health",
                "error": str(e)
            }

# Google ADK Configuration endpoints
@app.get("/adk/validate")
async def validate_adk_setup():
    """Validate Google ADK configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("adk_validate"):
        logger.info("ADK configuration validation requested")
        
        try:
            validation_result = validate_adk_environment()
            
            if validation_result["valid"]:
                logger.info("ADK configuration validation successful")
                return {
                    "status": "success",
                    "message": "Google ADK is properly configured",
                    "config": validation_result["config"]
                }
            else:
                logger.warning("ADK configuration validation failed", errors=validation_result["errors"])
                return {
                    "status": "error",
                    "message": "Google ADK configuration has issues",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }
                
        except Exception as e:
            logger.error("ADK validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate ADK configuration",
                "error": str(e)
            }

@app.get("/adk/models")
async def get_available_models():
    """Get available Google AI models - public endpoint"""
    with perf_logger.time_operation("adk_get_models"):
        logger.info("Available models requested")
        
        try:
            adk_config = get_adk_config()
            models = adk_config.get_available_models()
            
            return {
                "status": "success",
                "models": models,
                "default_model": adk_config.default_model,
                "service": "Vertex AI" if adk_config.use_vertex_ai else "Google AI Studio"
            }
            
        except Exception as e:
            logger.error("Failed to get available models", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve available models",
                "error": str(e)
            }

@app.get("/adk/connection-test")
async def test_adk_connection():
    """Test connection to Google AI services - public endpoint for setup testing"""
    with perf_logger.time_operation("adk_connection_test"):
        logger.info("ADK connection test requested")
        
        try:
            adk_config = get_adk_config()
            connection_result = adk_config.test_connection()
            
            if connection_result["status"] == "success":
                logger.info("ADK connection test successful")
                return {
                    "status": "success",
                    "message": "Successfully connected to Google AI services",
                    "service": connection_result["service"],
                    "model": connection_result["model"],
                    "project": connection_result.get("project")
                }
            else:
                logger.warning("ADK connection test failed", error=connection_result["error"])
                return {
                    "status": "error",
                    "message": "Failed to connect to Google AI services",
                    "error": connection_result["error"],
                    "service": connection_result["service"]
                }
                
        except Exception as e:
            logger.error("ADK connection test failed with exception", exception=e)
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
        
        validate_adk_environment()
        discovery_status = get_discovery_status()
        
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "framework_version": "2.0",
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
        logger.info("Job creation requested", user_id=user["id"], job_data=request.data)
        
        try:
            # Generate job ID
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:8]}"
            
            # Create job in database
            db_ops = get_database_operations()
            job_data = {
                "id": job_id,
                "user_id": user["id"],
                "status": "pending",
                "data": request.data,
                "priority": request.priority or 0,
                "tags": request.tags or [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            created_job = await db_ops.create_job(job_data)
            
            # Submit to job pipeline
            pipeline = get_job_pipeline()
            
            # Extract agent name from job data or determine from job type
            agent_name = request.data.get('agent', 'text_processing')  # Default agent
            
            success = await pipeline.submit_job(
                job_id=job_id,
                user_id=user["id"],
                agent_name=agent_name,
                job_data=request.data,
                priority=request.priority or 5,
                tags=request.tags
            )
            
            if not success:
                logger.error("Failed to submit job to pipeline", job_id=job_id)
                raise HTTPException(status_code=500, detail="Failed to queue job for processing")
            
            logger.info("Job created and queued successfully", job_id=job_id, user_id=user["id"])
            
            return JobCreateResponse(
                success=True,
                message="Job created and queued for processing",
                job_id=job_id
            )
            
        except Exception as e:
            logger.error("Job creation failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Job creation failed: {str(e)}")

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
    """Get details of a specific job"""
    with perf_logger.time_operation("get_job", user_id=user["id"], job_id=job_id):
        logger.info("Job details requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job_response = JobResponse(
                id=job["id"],
                status=job["status"],
                data=job["data"],
                result=job.get("result"),
                error_message=job.get("error_message"),
                created_at=job["created_at"],
                updated_at=job["updated_at"]
            )
            
            logger.info("Job details retrieved", job_id=job_id, user_id=user["id"])
            
            return JobDetailResponse(
                success=True,
                message="Job details retrieved successfully",
                job=job_response
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
                "timestamp": datetime.utcnow().isoformat()
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
                "timestamp": datetime.utcnow().isoformat()
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

# Set up static file serving after all API routes are defined
# This must be done before the global exception handler
setup_static_file_serving(app)

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
        return {
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    else:
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.is_development(),
        log_level=settings.log_level.value.lower()
    ) 