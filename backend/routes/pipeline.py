"""
Pipeline routes for the AI Agent Platform.

Contains endpoints for:
- Pipeline status monitoring
- Pipeline metrics and performance data
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from auth import get_current_user
from job_pipeline import get_job_pipeline
from logging_system import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.get("/status")
async def get_pipeline_status(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current pipeline status and health"""
    with perf_logger.time_operation("get_pipeline_status", user_id=user["id"]):
        logger.info("Pipeline status requested", user_id=user["id"])
        
        try:
            pipeline = get_job_pipeline()
            
            if not pipeline:
                return {
                    "success": True,
                    "message": "Pipeline status retrieved",
                    "status": "not_initialized",
                    "is_running": False
                }
            
            return {
                "success": True,
                "message": "Pipeline status retrieved",
                "status": "running" if pipeline.is_running else "stopped",
                "is_running": pipeline.is_running,
                "queue_size": getattr(pipeline, 'queue_size', 0),
                "worker_count": getattr(pipeline, 'worker_count', 0),
                "processed_jobs": getattr(pipeline, 'processed_jobs', 0)
            }
            
        except Exception as e:
            logger.error("Pipeline status retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get pipeline status: {str(e)}")

@router.get("/metrics")
async def get_pipeline_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """Get detailed pipeline metrics and performance data"""
    with perf_logger.time_operation("get_pipeline_metrics", user_id=user["id"]):
        logger.info("Pipeline metrics requested", user_id=user["id"])
        
        try:
            pipeline = get_job_pipeline()
            
            if not pipeline:
                return {
                    "success": True,
                    "message": "Pipeline metrics retrieved",
                    "metrics": {},
                    "status": "not_initialized"
                }
            
            # Get pipeline metrics if available
            metrics = {}
            if hasattr(pipeline, 'get_metrics'):
                metrics = pipeline.get_metrics()
            
            return {
                "success": True,
                "message": "Pipeline metrics retrieved",
                "metrics": metrics,
                "status": "running" if pipeline.is_running else "stopped"
            }
            
        except Exception as e:
            logger.error("Pipeline metrics retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get pipeline metrics: {str(e)}") 