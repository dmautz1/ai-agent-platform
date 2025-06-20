"""
System routes for the AI Agent Platform.

Contains endpoints for:
- Health checks and system status
- Public statistics
- CORS configuration information
- System configuration
- Logging metrics (development only)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Union
from datetime import datetime, timezone

from auth import get_current_user
from database import check_database_health, get_database_operations
from config.environment import get_settings
from logging_system import get_logger
from static_files import get_static_file_info
from models import ApiResponse
from utils.responses import (
    create_success_response, 
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["system"])

# System Response Types
HealthCheckResponse = Dict[str, Union[str, bool, int]]
SystemStatsResponse = Dict[str, Union[str, int, float]]
ConfigResponse = Dict[str, Any]

@router.get("/", response_model=ApiResponse[HealthCheckResponse])
@api_response_validator(result_type=HealthCheckResponse)
async def root():
    """Health check endpoint - public"""
    logger.info("Root health check requested")
    settings = get_settings()  # Get fresh settings
    
    health_data = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment.value,
        "framework_version": "1.0",
        "agent_framework": "self-contained",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return create_success_response(
        result=health_data,
        message=f"{settings.app_name} v1.0 is running",
        metadata={
            "endpoint": "root_health_check",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.get("/health", response_model=ApiResponse[HealthCheckResponse])
@api_response_validator(result_type=HealthCheckResponse)
async def health_check():
    """Health check endpoint with basic status"""
    logger.info("Health check requested")
    settings = get_settings()  # Get fresh settings
    
    health_data = {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return create_success_response(
        result=health_data,
        message="System health check completed",
        metadata={
            "endpoint": "health_check",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.get("/stats", response_model=ApiResponse[SystemStatsResponse])
@api_response_validator(result_type=SystemStatsResponse)
async def get_public_stats():
    """Get public job statistics - public endpoint"""
    try:
        db_ops = get_database_operations()
        stats = await db_ops.get_job_statistics()
        
        return create_success_response(
            result=stats,
            message="Statistics retrieved successfully",
            metadata={
                "endpoint": "public_stats",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error("Failed to get public statistics", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve statistics",
            metadata={
                "error_code": "STATS_RETRIEVAL_ERROR",
                "endpoint": "public_stats",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/cors-info", response_model=ApiResponse[Dict[str, Any]])
@api_response_validator(result_type=Dict[str, Any])
async def get_cors_info():
    """Get CORS configuration information - development only"""
    settings = get_settings()  # Get fresh settings
    if not settings.is_development():
        return create_error_response(
            error_message="Not found",
            message="Endpoint not available in production",
            metadata={
                "error_code": "ENDPOINT_NOT_AVAILABLE",
                "environment": settings.environment.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    logger.info("CORS info requested")
    
    try:
        from main import get_cors_origins  # Import here to avoid circular import
        
        cors_data = {
            "cors_origins": get_cors_origins(),
            "environment": settings.environment.value,
            "allow_credentials": settings.cors_allow_credentials,
            "max_age": settings.cors_max_age
        }
        
        return create_success_response(
            result=cors_data,
            message="CORS configuration (development mode)",
            metadata={
                "endpoint": "cors_info",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error("CORS info retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve CORS information",
            metadata={
                "error_code": "CORS_INFO_ERROR",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/config", response_model=ApiResponse[ConfigResponse])
@api_response_validator(result_type=ConfigResponse)
async def get_system_config():
    """Get system configuration - public endpoint"""
    logger.info("System configuration requested")
    settings = get_settings()  # Get fresh settings
    
    try:
        config_info = {
            "environment": settings.environment.value,
            "version": settings.app_version,
            "debug": settings.is_development(),
            "cors_enabled": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return create_success_response(
            result=config_info,
            message="System configuration retrieved",
            metadata={
                "endpoint": "system_config",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("System config retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve system configuration",
            metadata={
                "error_code": "CONFIG_RETRIEVAL_ERROR",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/logs/metrics", response_model=ApiResponse[Dict[str, Any]])
@api_response_validator(result_type=Dict[str, Any])
async def get_logging_metrics():
    """Get logging metrics - development only"""
    settings = get_settings()  # Get fresh settings
    if not settings.is_development():
        logger.warning("Logging metrics endpoint accessed in non-development environment")
        return create_error_response(
            error_message="Not found",
            message="Endpoint not available in production",
            metadata={
                "error_code": "ENDPOINT_NOT_AVAILABLE",
                "environment": settings.environment.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    logger.info("Logging metrics requested")
    
    metrics_data = {
        "message": "Performance metrics removed - basic logging only",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return create_success_response(
        result=metrics_data,
        message="Logging metrics retrieved",
        metadata={
            "endpoint": "logging_metrics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.get("/static-info", response_model=ApiResponse[Dict[str, Any]])
@api_response_validator(result_type=Dict[str, Any])
async def get_static_file_info_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """Get information about static file serving configuration"""
    logger.info("Static file info requested", user_id=user["id"])
    
    try:
        static_info = get_static_file_info()
        return create_success_response(
            result=static_info,
            message="Static file information retrieved",
            metadata={
                "endpoint": "static_info",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error("Static file info retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve static file information",
            metadata={
                "error_code": "STATIC_INFO_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 