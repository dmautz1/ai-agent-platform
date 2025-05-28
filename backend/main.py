from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging.config
from typing import List, Optional, Dict, Any
from datetime import datetime
from auth import get_current_user, get_optional_user
from config import get_settings, validate_required_settings, get_logging_config
from logging_system import (
    setup_logging_middleware, get_logger, get_performance_logger,
    get_security_logger, log_startup_info, log_shutdown_info
)

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

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A template for building AI agents with job scheduling and monitoring",
    version=settings.app_version,
    debug=settings.debug
)

# CORS Configuration using centralized settings
cors_origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since",
        "X-CSRF-Token"
    ],
    expose_headers=[
        "Content-Length",
        "Content-Range",
        "X-Content-Range"
    ],
    max_age=settings.cors_max_age,
)

# Set up comprehensive logging middleware
setup_logging_middleware(app)

# Security
security = HTTPBearer()

@app.on_startup
async def startup_event():
    """Application startup event with comprehensive logging"""
    log_startup_info()
    
    logger.info(
        "Application configuration loaded",
        cors_origins_count=len(cors_origins),
        debug_mode=settings.debug,
        environment=settings.environment.value
    )
    
    logger.info("Application ready to accept requests")

@app.on_shutdown
async def shutdown_event():
    """Application shutdown event with comprehensive logging"""
    logger.info("Beginning application shutdown")
    
    # Log final performance metrics and shutdown info
    log_shutdown_info()

@app.get("/")
async def root():
    """Health check endpoint - public"""
    with perf_logger.time_operation("health_check_root"):
        logger.info("Root health check requested")
        
        return {
            "message": f"{settings.app_name} is running",
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint - public"""
    with perf_logger.time_operation("health_check_detailed"):
        logger.info("Detailed health check requested")
        
        # Get performance metrics summary
        metrics_summary = perf_logger.get_metrics_summary()
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "cors_origins": len(cors_origins),
            "debug": settings.debug,
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": metrics_summary if settings.is_development() else {}
        }

@app.get("/cors-info") 
async def cors_info():
    """Get CORS configuration info - public endpoint for debugging"""
    with perf_logger.time_operation("cors_info"):
        logger.info("CORS info requested")
        
        # Only show detailed CORS info in development
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
        
        # Log successful authentication
        security_logger.log_auth_success(
            user_id=user["id"],
            method="jwt"
        )
        
        return {
            "user": user,
            "message": "Authentication successful"
        }

# Protected job management endpoints
@app.post("/schedule-job")
async def schedule_job(user: Dict[str, Any] = Depends(get_current_user)):
    """Schedule a new AI agent job - requires authentication"""
    with perf_logger.time_operation("schedule_job", user_id=user["id"]):
        logger.info("Job scheduling requested", user_id=user["id"])
        
        # Will be implemented when database operations are connected
        return {
            "message": "Job scheduling endpoint - implementation pending",
            "user_id": user["id"],
            "status": "not_implemented"
        }

@app.get("/jobs")
async def get_jobs(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all jobs with their statuses - requires authentication"""
    with perf_logger.time_operation("get_jobs", user_id=user["id"]):
        logger.info("Jobs list requested", user_id=user["id"])
        
        # Will be implemented when database operations are connected
        return {
            "message": "Get jobs endpoint - implementation pending", 
            "user_id": user["id"],
            "jobs": [],
            "status": "not_implemented"
        }

@app.get("/job/{job_id}")
async def get_job(job_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve specific job details - requires authentication"""
    with perf_logger.time_operation("get_job_details", user_id=user["id"], job_id=job_id):
        logger.info("Job details requested", user_id=user["id"], job_id=job_id)
        
        # Will be implemented when database operations are connected
        return {
            "message": "Get job endpoint - implementation pending",
            "job_id": job_id,
            "user_id": user["id"],
            "status": "not_implemented"
        }

# Optional auth endpoint for public job statistics
@app.get("/public/job-stats")
async def get_public_job_stats():
    """Get public job statistics - no authentication required"""
    with perf_logger.time_operation("public_job_stats"):
        logger.info("Public job stats requested")
        
        # This could show anonymized stats without requiring auth
        return {
            "message": "Public job stats endpoint - implementation pending",
            "stats": {
                "total_jobs": 0,
                "completed_jobs": 0,
                "pending_jobs": 0
            }
        }

# Configuration endpoint (development only)
@app.get("/config")
async def get_config_info():
    """Get configuration information - development only"""
    if not settings.is_development():
        logger.warning("Configuration endpoint accessed in non-development environment")
        raise HTTPException(status_code=404, detail="Not found")
    
    with perf_logger.time_operation("get_config_info"):
        logger.info("Configuration info requested")
        
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment.value,
            "debug": settings.debug,
            "cors_origins_count": len(cors_origins),
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "log_level": settings.log_level.value,
            "performance_metrics": perf_logger.get_metrics_summary(),
            "message": "Configuration info (development mode only)"
        }

# Logging endpoint (development only)
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

# Custom exception handler with logging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with comprehensive logging"""
    logger.error(
        "Unhandled exception occurred",
        exception=exc,
        path=request.url.path,
        method=request.method
    )
    
    # Log security event for certain types of errors
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