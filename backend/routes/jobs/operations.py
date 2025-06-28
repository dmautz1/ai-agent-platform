"""
Job operations endpoints for the AI Agent Platform.

Handles:
- Job retry operations
- Job rerun functionality  
- Job cancellation/termination
- Job priority updates
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Union
from datetime import datetime, timezone

from auth import get_current_user
from database import get_database_operations
from job_pipeline import get_job_pipeline
from models import ApiResponse
from logging_system import get_logger
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["job-operations"])

# Job Operations Response Types
JobRetryResponse = Dict[str, Union[str, bool]]
JobRerunResponse = Dict[str, Union[str, bool, Dict[str, Any]]]
JobCancelResponse = Dict[str, str]
JobPriorityResponse = Dict[str, Union[str, int]]

@router.post("/{job_id}/retry", response_model=ApiResponse[JobRetryResponse])
@api_response_validator(result_type=JobRetryResponse)
async def retry_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a retry of a failed job.
    Only allowed for jobs in 'failed' status.
    """
    logger.info("Job retry requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
        
        # Get the original job
        original_job = await db_ops.get_job(job_id, user_id=user["id"])
        if not original_job:
            return create_error_response(
                error_message="Job not found or access denied",
                message="Job not found",
                metadata={
                    "error_code": "JOB_NOT_FOUND",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if job can be retried
        if original_job["status"] != "failed":
            return create_error_response(
                error_message=f"Cannot retry job with status '{original_job['status']}'",
                message="Invalid job status for retry",
                metadata={
                    "error_code": "INVALID_STATUS",
                    "allowed_statuses": ["failed"],
                    "current_status": original_job["status"],
                    "suggestion": "Only failed jobs can be retried",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Create a new job with the same parameters
        retry_job_data = {
            "user_id": user["id"],
            "agent_identifier": original_job["agent_identifier"],
            "data": original_job["data"],
            "priority": original_job.get("priority", 5),
            "tags": (original_job.get("tags") or []) + ["retry"],
            "title": f"Retry: {original_job.get('title', 'Untitled Job')}",
            "status": "pending"
        }
        
        new_job = await db_ops.create_job(retry_job_data)
        
        if not new_job:
            return create_error_response(
                error_message="Failed to create retry job",
                message="Job retry creation failed",
                metadata={
                    "error_code": "RETRY_CREATION_FAILED",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Submit the retry job to the pipeline for execution
        pipeline_submitted = False
        pipeline = get_job_pipeline()
        if pipeline and pipeline.is_running:
            try:
                pipeline_submitted = await pipeline.submit_job(
                    job_id=new_job["id"],
                    user_id=user["id"],
                    agent_name=new_job["agent_identifier"],
                    job_data=new_job["data"],
                    priority=new_job.get("priority", 5),
                    tags=new_job.get("tags", [])
                )
                
                if pipeline_submitted:
                    logger.info("Retry job submitted to pipeline", job_id=new_job["id"])
                else:
                    logger.warning("Retry job created but failed to submit to pipeline", job_id=new_job["id"])
            except Exception as e:
                logger.warning("Failed to submit retry job to pipeline", exception=e, job_id=new_job["id"])
        else:
            logger.warning("Retry job created but pipeline not running", job_id=new_job["id"])
        
        logger.info(
            "Job retry created successfully",
            original_job_id=job_id,
            retry_job_id=new_job["id"],
            user_id=user["id"]
        )
        
        result_data = {
            "job_id": new_job["id"],
            "original_job_id": job_id,
            "new_status": "pending",
            "pipeline_submitted": pipeline_submitted
        }
        
        return create_success_response(
            result=result_data,
            message="Retry job created successfully",
            metadata={
                "endpoint": "retry_job",
                "job_id": job_id,
                "retry_job_id": new_job["id"],
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to retry job", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retry job",
            metadata={
                "error_code": "JOB_RETRY_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/{job_id}/rerun", response_model=ApiResponse[JobRerunResponse])
@api_response_validator(result_type=JobRerunResponse)
async def rerun_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Rerun a completed job with the same parameters.
    Allowed for jobs in 'completed', 'failed', or 'cancelled' status.
    """
    logger.info("Job rerun requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
        
        # Get the original job
        original_job = await db_ops.get_job(job_id, user_id=user["id"])
        if not original_job:
            return create_error_response(
                error_message="Job not found or access denied",
                message="Job not found",
                metadata={
                    "error_code": "JOB_NOT_FOUND",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if job can be rerun
        allowed_statuses = ["completed", "failed", "cancelled"]
        if original_job["status"] not in allowed_statuses:
            return create_error_response(
                error_message=f"Cannot rerun job with status '{original_job['status']}'",
                message="Invalid job status for rerun",
                metadata={
                    "error_code": "INVALID_STATUS",
                    "allowed_statuses": allowed_statuses,
                    "current_status": original_job["status"],
                    "suggestion": "Jobs can only be rerun after completion, failure, or cancellation",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Create a new job with the same parameters
        rerun_job_data = {
            "user_id": user["id"],
            "agent_identifier": original_job["agent_identifier"],
            "data": original_job["data"],
            "priority": original_job.get("priority", 5),
            "tags": (original_job.get("tags") or []) + ["rerun"],
            "title": f"Rerun: {original_job.get('title', 'Untitled Job')}",
            "status": "pending"
        }
        
        new_job = await db_ops.create_job(rerun_job_data)
        
        if not new_job:
            return create_error_response(
                error_message="Failed to create rerun job",
                message="Job rerun creation failed",
                metadata={
                    "error_code": "RERUN_CREATION_FAILED",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Submit the rerun job to the pipeline for execution
        pipeline_submitted = False
        pipeline = get_job_pipeline()
        if pipeline and pipeline.is_running:
            try:
                pipeline_submitted = await pipeline.submit_job(
                    job_id=new_job["id"],
                    user_id=user["id"],
                    agent_name=new_job["agent_identifier"],
                    job_data=new_job["data"],
                    priority=new_job.get("priority", 5),
                    tags=new_job.get("tags", [])
                )
                
                if pipeline_submitted:
                    logger.info("Rerun job submitted to pipeline", job_id=new_job["id"])
                else:
                    logger.warning("Rerun job created but failed to submit to pipeline", job_id=new_job["id"])
            except Exception as e:
                logger.warning("Failed to submit rerun job to pipeline", exception=e, job_id=new_job["id"])
        else:
            logger.warning("Rerun job created but pipeline not running", job_id=new_job["id"])
        
        logger.info(
            "Job rerun created successfully",
            original_job_id=job_id,
            rerun_job_id=new_job["id"],
            user_id=user["id"]
        )
        
        result_data = {
            "original_job_id": job_id,
            "new_job_id": new_job["id"],
            "new_job": new_job,
            "pipeline_submitted": pipeline_submitted
        }
        
        return create_success_response(
            result=result_data,
            message="Rerun job created successfully",
            metadata={
                "endpoint": "rerun_job",
                "job_id": job_id,
                "rerun_job_id": new_job["id"],
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to rerun job", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to rerun job",
            metadata={
                "error_code": "JOB_RERUN_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/{job_id}/cancel", response_model=ApiResponse[JobCancelResponse])
@api_response_validator(result_type=JobCancelResponse)
async def cancel_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancel a running or pending job.
    Only allowed for jobs in 'pending' or 'running' status.
    """
    logger.info("Job cancellation requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
        
        # Get the job
        job = await db_ops.get_job(job_id, user_id=user["id"])
        if not job:
            return create_error_response(
                error_message="Job not found or access denied",
                message="Job not found",
                metadata={
                    "error_code": "JOB_NOT_FOUND",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if job can be cancelled
        allowed_statuses = ["pending", "running"]
        if job["status"] not in allowed_statuses:
            return create_error_response(
                error_message=f"Cannot cancel job with status '{job['status']}'",
                message="Invalid job status for cancellation",
                metadata={
                    "error_code": "INVALID_STATUS",
                    "allowed_statuses": allowed_statuses,
                    "current_status": job["status"],
                    "suggestion": "Only pending or running jobs can be cancelled",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Update job status to cancelled
        await db_ops.update_job_status(job_id, "cancelled", {
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": user["id"],
            "cancellation_reason": "User requested cancellation"
        })
        
        # If job is running, try to signal the job pipeline to stop it
        if job["status"] == "running":
            try:
                pipeline = get_job_pipeline()
                await pipeline.cancel_job(job_id)
            except Exception as e:
                logger.warning(
                    "Failed to signal job cancellation to pipeline",
                    exception=e,
                    job_id=job_id
                )
                # Don't fail the request if we can't signal the pipeline
        
        logger.info(
            "Job cancelled successfully",
            job_id=job_id,
            user_id=user["id"],
            previous_status=job["status"]
        )
        
        result_data = {
            "job_id": job_id,
            "previous_status": job["status"],
            "new_status": "cancelled"
        }
        
        return create_success_response(
            result=result_data,
            message="Job cancelled successfully",
            metadata={
                "endpoint": "cancel_job",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to cancel job", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to cancel job",
            metadata={
                "error_code": "JOB_CANCEL_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/{job_id}/priority", response_model=ApiResponse[JobPriorityResponse])
@api_response_validator(result_type=JobPriorityResponse)
async def update_job_priority(
    job_id: str,
    request: Dict[str, int],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the priority of a pending job.
    Only allowed for jobs in 'pending' status.
    """
    new_priority = request.get("priority")
    
    if new_priority is None:
        return create_error_response(
            error_message="priority field is required",
            message="Missing required field",
            metadata={
                "error_code": "MISSING_PRIORITY",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    if not isinstance(new_priority, int) or not (1 <= new_priority <= 10):
        return create_error_response(
            error_message="priority must be an integer between 1 and 10",
            message="Invalid priority value",
            metadata={
                "error_code": "INVALID_PRIORITY",
                "provided_priority": new_priority,
                "valid_range": "1-10",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    logger.info(
        "Job priority update requested",
        job_id=job_id,
        user_id=user["id"],
        new_priority=new_priority
    )
    
    try:
        db_ops = get_database_operations()
        
        # Get the job
        job = await db_ops.get_job(job_id, user_id=user["id"])
        if not job:
            return create_error_response(
                error_message="Job not found or access denied",
                message="Job not found",
                metadata={
                    "error_code": "JOB_NOT_FOUND",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Check if job priority can be updated
        if job["status"] != "pending":
            return create_error_response(
                error_message=f"Cannot update priority for job with status '{job['status']}'",
                message="Invalid job status for priority update",
                metadata={
                    "error_code": "INVALID_STATUS",
                    "allowed_statuses": ["pending"],
                    "current_status": job["status"],
                    "suggestion": "Priority can only be updated for pending jobs",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Update job priority using the correct database method
        await db_ops.update_job(job_id, {
            "priority": new_priority
        })
        
        logger.info(
            "Job priority updated successfully",
            job_id=job_id,
            user_id=user["id"],
            old_priority=job.get("priority", 5),
            new_priority=new_priority
        )
        
        result_data = {
            "job_id": job_id,
            "old_priority": job.get("priority", 5),
            "new_priority": new_priority
        }
        
        return create_success_response(
            result=result_data,
            message="Job priority updated successfully",
            metadata={
                "endpoint": "update_job_priority",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to update job priority", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to update job priority",
            metadata={
                "error_code": "JOB_PRIORITY_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 