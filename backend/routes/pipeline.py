"""
Pipeline routes for the AI Agent Platform.

Contains endpoints for:
- Pipeline status monitoring
- Pipeline metrics and performance data
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime, timezone

from auth import get_current_user
from job_pipeline import get_job_pipeline
from logging_system import get_logger
from models import ApiResponse
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Pipeline Response Types
PipelineStatusResponse = Dict[str, Any]
PipelineMetricsResponse = Dict[str, Any]

@router.get("/status", response_model=ApiResponse[PipelineStatusResponse])
@api_response_validator(result_type=PipelineStatusResponse)
async def get_pipeline_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current pipeline status and health"""
    logger.info("Pipeline status requested", user_id=user["id"])
    
    try:
        pipeline = get_job_pipeline()
        
        if not pipeline:
            status_data = {
                "status": "not_initialized",
                "is_running": False
            }
            return create_success_response(
                result=status_data,
                message="Pipeline status retrieved",
                metadata={
                    "endpoint": "pipeline_status",
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        status_data = {
            "status": "running" if pipeline.is_running else "stopped",
            "is_running": pipeline.is_running,
            "queue_size": getattr(pipeline, 'queue_size', 0),
            "worker_count": getattr(pipeline, 'worker_count', 0),
            "processed_jobs": getattr(pipeline, 'processed_jobs', 0)
        }
        
        return create_success_response(
            result=status_data,
            message="Pipeline status retrieved",
            metadata={
                "endpoint": "pipeline_status",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Pipeline status retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to get pipeline status",
            metadata={
                "error_code": "PIPELINE_STATUS_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/metrics", response_model=ApiResponse[PipelineMetricsResponse])
@api_response_validator(result_type=PipelineMetricsResponse)
async def get_pipeline_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """Get detailed pipeline metrics and performance data"""
    logger.info("Pipeline metrics requested", user_id=user["id"])
    
    try:
        pipeline = get_job_pipeline()
        
        if not pipeline:
            metrics_data = {
                "metrics": {},
                "status": "not_initialized"
            }
            return create_success_response(
                result=metrics_data,
                message="Pipeline metrics retrieved",
                metadata={
                    "endpoint": "pipeline_metrics",
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Get pipeline metrics if available
        metrics = {}
        if hasattr(pipeline, 'get_metrics'):
            metrics = pipeline.get_metrics()
        
        metrics_data = {
            "metrics": metrics,
            "status": "running" if pipeline.is_running else "stopped"
        }
        
        return create_success_response(
            result=metrics_data,
            message="Pipeline metrics retrieved",
            metadata={
                "endpoint": "pipeline_metrics",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Pipeline metrics retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to get pipeline metrics",
            metadata={
                "error_code": "PIPELINE_METRICS_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 