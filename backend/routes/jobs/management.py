"""
Job management endpoints for the AI Agent Platform.

Handles:
- Job listing and retrieval
- Job status management
- Job metadata operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from auth import get_current_user
from database import get_database_operations
from models import JobResponse, ApiResponse
from logging_system import get_logger
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["job-management"])

# Job Management Response Types
JobListResponse = Dict[str, Union[List[Dict[str, Any]], int]]
JobsMinimalResponse = Dict[str, Union[List[Dict[str, Any]], int]]
JobDetailResponse = Dict[str, Any]
JobStatusResponse = Dict[str, Any]
BatchStatusResponse = Dict[str, Union[Dict[str, Any], int]]
JobDeleteResponse = Dict[str, str]

@router.get("/list", response_model=ApiResponse[JobListResponse])
@api_response_validator(result_type=JobListResponse)
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(default=0, ge=0, description="Number of jobs to skip"),
    status: Optional[str] = Query(default=None, description="Filter by job status"),
    agent_identifier: Optional[str] = Query(default=None, description="Filter by agent"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a list of user's jobs with pagination and filtering.
    """
    logger.info(
        "Job list requested",
        user_id=user["id"],
        limit=limit,
        offset=offset,
        status_filter=status,
        agent_filter=agent_identifier
    )
    
    try:
        db_ops = get_database_operations()
        
        # Get all user jobs (we'll filter in memory for now)
        jobs = await db_ops.get_user_jobs(
            user_id=user["id"],
            limit=limit,
            offset=offset
        )
        
        # Apply filters in memory (since the database client doesn't support filtering)
        filtered_jobs = jobs
        if status:
            filtered_jobs = [job for job in filtered_jobs if job.get("status") == status]
        if agent_identifier:
            filtered_jobs = [job for job in filtered_jobs if job.get("agent_identifier") == agent_identifier]
        
        # Convert to JobResponse format
        job_responses = []
        for job in filtered_jobs:
            job_responses.append(JobResponse(
                id=job["id"],
                status=job["status"],
                agent_identifier=job.get("agent_identifier", "unknown"),
                data=job.get("job_data", job.get("data", {})),
                result=job.get("result"),
                error_message=job.get("error_message"),
                created_at=job["created_at"],
                updated_at=job["updated_at"],
                title=job.get("title"),
                priority=job.get("priority", 5),
                tags=job.get("tags", [])
            ))
        
        result_data = {
            "jobs": job_responses,
            "total_count": len(job_responses)
        }
        
        return create_success_response(
            result=result_data,
            message=f"Retrieved {len(job_responses)} jobs",
            metadata={
                "endpoint": "list_jobs",
                "user_id": user["id"],
                "filters": {
                    "status": status,
                    "agent_identifier": agent_identifier,
                    "limit": limit,
                    "offset": offset
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to list jobs", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve jobs",
            metadata={
                "error_code": "JOBS_LIST_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/minimal", response_model=ApiResponse[JobsMinimalResponse])
@api_response_validator(result_type=JobsMinimalResponse)
async def get_jobs_minimal(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a minimal list of jobs for dashboard/summary views.
    Returns only essential fields for performance.
    """
    try:
        db_ops = get_database_operations()
        # Use the existing get_user_jobs method and extract minimal fields
        jobs = await db_ops.get_user_jobs(user["id"], limit=limit, offset=offset)
        
        # Convert to minimal format
        minimal_jobs = []
        for job in jobs:
            minimal_jobs.append({
                "id": job["id"],
                "status": job["status"],
                "agent_identifier": job.get("agent_identifier", "unknown"),
                "title": job.get("title", "Untitled Job"),
                "created_at": job["created_at"],
                "updated_at": job["updated_at"]
            })
        
        result_data = {
            "jobs": minimal_jobs,
            "total_count": len(minimal_jobs)
        }
        
        return create_success_response(
            result=result_data,
            message=f"Retrieved {len(minimal_jobs)} jobs (minimal)",
            metadata={
                "endpoint": "jobs_minimal",
                "user_id": user["id"],
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to get minimal jobs", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve minimal jobs",
            metadata={
                "error_code": "JOBS_MINIMAL_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/{job_id}", response_model=ApiResponse[JobDetailResponse])
@api_response_validator(result_type=JobDetailResponse)
async def get_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information about a specific job.
    """
    logger.info("Job detail requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
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
        
        return create_success_response(
            result={"job": job},
            message="Job retrieved successfully",
            metadata={
                "endpoint": "get_job",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to get job", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve job",
            metadata={
                "error_code": "JOB_DETAIL_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/{job_id}/status", response_model=ApiResponse[JobStatusResponse])
@api_response_validator(result_type=JobStatusResponse)
async def get_job_status(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current status of a specific job.
    Lightweight endpoint for status polling.
    """
    try:
        db_ops = get_database_operations()
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
        
        status_data = {
            "job_id": job_id,
            "status": job["status"],
            "updated_at": job["updated_at"],
            "progress": job.get("progress"),
            "estimated_completion": job.get("estimated_completion")
        }
        
        return create_success_response(
            result=status_data,
            message="Job status retrieved",
            metadata={
                "endpoint": "job_status",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to get job status", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve job status",
            metadata={
                "error_code": "JOB_STATUS_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/batch/status", response_model=ApiResponse[BatchStatusResponse])
@api_response_validator(result_type=BatchStatusResponse)
async def get_batch_job_status(
    request: Dict[str, List[str]],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get status for multiple jobs at once.
    Useful for dashboard updates and bulk operations.
    """
    job_ids = request.get("job_ids", [])
    
    if not job_ids:
        return create_error_response(
            error_message="job_ids list is required",
            message="Invalid request",
            metadata={
                "error_code": "MISSING_JOB_IDS",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    if len(job_ids) > 50:
        return create_error_response(
            error_message="Cannot request status for more than 50 jobs at once",
            message="Too many job IDs",
            metadata={
                "error_code": "TOO_MANY_JOB_IDS",
                "requested_count": len(job_ids),
                "max_allowed": 50,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    try:
        db_ops = get_database_operations()
        statuses = {}
        
        # Get status for each job individually (since no batch method exists)
        for job_id in job_ids:
            try:
                job = await db_ops.get_job(job_id, user_id=user["id"])
                if job:
                    statuses[job_id] = {
                        "status": job["status"],
                        "updated_at": job.get("updated_at"),
                        "progress": job.get("progress"),
                        "estimated_completion": job.get("estimated_completion")
                    }
                else:
                    statuses[job_id] = {"status": "not_found"}
            except Exception as e:
                logger.warning(f"Failed to get status for job {job_id}", exception=e)
                statuses[job_id] = {"status": "error", "error": str(e)}
        
        result_data = {
            "statuses": statuses,
            "requested_count": len(job_ids),
            "returned_count": len(statuses)
        }
        
        return create_success_response(
            result=result_data,
            message=f"Retrieved status for {len(statuses)} jobs",
            metadata={
                "endpoint": "batch_job_status",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to get batch job status", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve batch job status",
            metadata={
                "error_code": "BATCH_STATUS_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.delete("/{job_id}", response_model=ApiResponse[JobDeleteResponse])
@api_response_validator(result_type=JobDeleteResponse)
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a job.
    Can only delete jobs that are not currently running.
    """
    logger.info("Job deletion requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
        
        # Check if job exists and get its status
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
        
        # Check if job can be deleted
        if job["status"] == "running":
            return create_error_response(
                error_message="Cannot delete running job",
                message="Job is currently running",
                metadata={
                    "error_code": "JOB_RUNNING",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "suggestion": "Stop the job first, then delete it",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Delete the job
        success = await db_ops.delete_job(job_id, user_id=user["id"])
        
        if not success:
            return create_error_response(
                error_message="Failed to delete job",
                message="Deletion failed",
                metadata={
                    "error_code": "DELETE_FAILED",
                    "job_id": job_id,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        logger.info("Job deleted successfully", job_id=job_id, user_id=user["id"])
        
        result_data = {
            "job_id": job_id
        }
        
        return create_success_response(
            result=result_data,
            message="Job deleted successfully",
            metadata={
                "endpoint": "delete_job",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Failed to delete job", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to delete job",
            metadata={
                "error_code": "JOB_DELETE_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 