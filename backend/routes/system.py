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
from typing import Dict, Any
from datetime import datetime, timezone

from auth import get_current_user
from database import check_database_health, get_database_operations
from config.environment import get_settings
from logging_system import get_logger, get_performance_logger
from static_files import get_static_file_info

logger = get_logger(__name__)
perf_logger = get_performance_logger()
settings = get_settings()

router = APIRouter(tags=["system"])

@router.get("/")
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

@router.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    with perf_logger.time_operation("health_check"):
        logger.info("Health check requested")
        
        try:
            # Quick database connectivity check
            db_health = await check_database_health()
            
            from main import get_cors_origins  # Import here to avoid circular import
            
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

@router.get("/stats")
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

@router.get("/cors-info")
async def get_cors_info():
    """Get CORS configuration information - development only"""
    if not settings.is_development():
        raise HTTPException(status_code=404, detail="Not found")
    
    with perf_logger.time_operation("cors_info"):
        logger.info("CORS info requested")
        
        from main import get_cors_origins  # Import here to avoid circular import
        
        return {
            "cors_origins": get_cors_origins(),
            "environment": settings.environment.value,
            "allow_credentials": settings.cors_allow_credentials,
            "max_age": settings.cors_max_age,
            "message": "CORS configuration (development mode)"
        }

@router.get("/config")
async def get_system_config():
    """Get system configuration - public endpoint"""
    with perf_logger.time_operation("get_system_config"):
        logger.info("System configuration requested")
        
        try:
            config_info = {
                "environment": settings.environment.value,
                "version": settings.app_version,
                "debug": settings.is_development(),
                "cors_enabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return {
                "status": "success",
                "message": "System configuration retrieved",
                "config": config_info
            }
            
        except Exception as e:
            logger.error("System config retrieval failed", exception=e)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve system config: {str(e)}")

@router.get("/logs/metrics")
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

@router.get("/static-info")
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