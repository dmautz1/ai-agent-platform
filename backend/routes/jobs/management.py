"""
Job management endpoints for the AI Agent Platform.

Handles:
- Job listing and retrieval
- Job status management
- Job metadata operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from auth import get_current_user
from database import get_database_operations
from models import JobListResponse, JobDetailResponse, JobResponse
from logging_system import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()

router = APIRouter(tags=["job-management"])

@router.get("/list", response_model=JobListResponse)
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
    with perf_logger.time_operation("list_jobs", user_id=user["id"]):
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
            
            return JobListResponse(
                success=True,
                message=f"Retrieved {len(job_responses)} jobs",
                jobs=job_responses,
                total_count=len(job_responses)
            )
            
        except Exception as e:
            logger.error("Failed to list jobs", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve jobs: {str(e)}",
                    "error_code": "DATABASE_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/minimal")
async def get_jobs_minimal(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a minimal list of jobs for dashboard/summary views.
    Returns only essential fields for performance.
    """
    with perf_logger.time_operation("get_jobs_minimal", user_id=user["id"]):
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
            
            return {
                "success": True,
                "message": f"Retrieved {len(minimal_jobs)} jobs (minimal)",
                "jobs": minimal_jobs,
                "count": len(minimal_jobs)
            }
            
        except Exception as e:
            logger.error("Failed to get minimal jobs", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve minimal jobs: {str(e)}"
            )

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information about a specific job.
    """
    with perf_logger.time_operation("get_job", user_id=user["id"], job_id=job_id):
        logger.info("Job detail requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": "Job not found or access denied",
                        "error_code": "JOB_NOT_FOUND",
                        "job_id": job_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            
            return JobDetailResponse(
                success=True,
                message="Job retrieved successfully",
                job=job
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get job", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve job: {str(e)}",
                    "error_code": "DATABASE_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current status of a specific job.
    Lightweight endpoint for status polling.
    """
    with perf_logger.time_operation("get_job_status", user_id=user["id"], job_id=job_id):
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or access denied"
                )
            
            return {
                "success": True,
                "job_id": job_id,
                "status": job["status"],
                "updated_at": job["updated_at"],
                "progress": job.get("progress"),
                "estimated_completion": job.get("estimated_completion")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get job status", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve job status: {str(e)}"
            )

@router.post("/batch/status")
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
        raise HTTPException(
            status_code=400,
            detail="job_ids list is required"
        )
    
    if len(job_ids) > 50:
        raise HTTPException(
            status_code=400,
            detail="Cannot request status for more than 50 jobs at once"
        )
    
    with perf_logger.time_operation("get_batch_job_status", user_id=user["id"], job_count=len(job_ids)):
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
            
            return {
                "success": True,
                "message": f"Retrieved status for {len(statuses)} jobs",
                "statuses": statuses,
                "requested_count": len(job_ids),
                "returned_count": len(statuses)
            }
            
        except Exception as e:
            logger.error("Failed to get batch job status", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve batch job status: {str(e)}"
            )

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a job.
    Can only delete jobs that are not currently running.
    """
    with perf_logger.time_operation("delete_job", user_id=user["id"], job_id=job_id):
        logger.info("Job deletion requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # Check if job exists and get its status
            job = await db_ops.get_job(job_id, user_id=user["id"])
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or access denied"
                )
            
            # Check if job can be deleted
            if job["status"] == "running":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Cannot delete running job",
                        "error_code": "JOB_RUNNING",
                        "suggestion": "Stop the job first, then delete it",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            
            # Delete the job
            success = await db_ops.delete_job(job_id, user_id=user["id"])
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to delete job"
                )
            
            logger.info("Job deleted successfully", job_id=job_id, user_id=user["id"])
            
            return {
                "success": True,
                "message": "Job deleted successfully",
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete job", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to delete job: {str(e)}",
                    "error_code": "DATABASE_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ) 