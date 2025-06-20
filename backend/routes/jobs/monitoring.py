"""
Job monitoring endpoints for the AI Agent Platform.

Handles:
- Job logs and execution history
- Job analytics and metrics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta

from auth import get_current_user
from database import get_database_operations
from models import ApiResponse
from logging_system import get_logger
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["job-monitoring"])

# Job Monitoring Response Types
JobLogsResponse = Dict[str, Union[str, List[Dict[str, Any]], int]]
JobAnalyticsResponse = Dict[str, Union[Dict[str, Any], Optional[Dict[str, str]]]]

@router.get("/{job_id}/logs", response_model=ApiResponse[JobLogsResponse])
@api_response_validator(result_type=JobLogsResponse)
async def get_job_logs(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Number of log entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of log entries to skip"),
    level: Optional[str] = Query(default=None, description="Filter by log level"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get logs for a specific job.
    Returns execution logs, errors, and debug information.
    """
    logger.info("Job logs requested", job_id=job_id, user_id=user["id"])
    
    try:
        db_ops = get_database_operations()
        
        # Verify job exists and user has access
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
        
        # For now, return basic job information as "logs"
        # In a full implementation, this would query a separate logs table
        logs = []
        
        # Add basic job lifecycle events as log entries
        if job.get("created_at"):
            logs.append({
                "timestamp": job["created_at"],
                "level": "INFO",
                "message": f"Job created for agent: {job.get('agent_identifier', 'unknown')}",
                "source": "system"
            })
        
        if job.get("status") == "running" and job.get("updated_at"):
            logs.append({
                "timestamp": job["updated_at"],
                "level": "INFO", 
                "message": "Job execution started",
                "source": "system"
            })
        
        if job.get("status") == "completed" and job.get("updated_at"):
            logs.append({
                "timestamp": job["updated_at"],
                "level": "INFO",
                "message": "Job completed successfully",
                "source": "system"
            })
        
        if job.get("status") == "failed":
            logs.append({
                "timestamp": job.get("updated_at", job["created_at"]),
                "level": "ERROR",
                "message": job.get("error_message", "Job failed"),
                "source": "system"
            })
        
        # Apply level filter if specified
        if level:
            logs = [log for log in logs if log["level"].lower() == level.lower()]
        
        # Apply pagination
        paginated_logs = logs[offset:offset + limit]
        
        result_data = {
            "job_id": job_id,
            "logs": paginated_logs,
            "total_count": len(logs),
            "count": len(paginated_logs)
        }
        
        return create_success_response(
            result=result_data,
            message="Job logs retrieved successfully",
            metadata={
                "endpoint": "job_logs",
                "job_id": job_id,
                "user_id": user["id"],
                "filters": {
                    "level": level,
                    "limit": limit,
                    "offset": offset
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Job logs retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve job logs",
            metadata={
                "error_code": "JOB_LOGS_ERROR",
                "job_id": job_id,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/analytics/summary", response_model=ApiResponse[JobAnalyticsResponse])
@api_response_validator(result_type=JobAnalyticsResponse)
async def get_jobs_analytics_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include"),
    agent_identifier: Optional[str] = Query(default=None, description="Filter by agent"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analytics summary for user's jobs.
    """
    logger.info("Jobs analytics summary requested", user_id=user["id"], days=days)
    
    try:
        db_ops = get_database_operations()
        
        # Get user jobs for analysis (larger limit to get more data)
        jobs = await db_ops.get_user_jobs(user["id"], limit=1000, offset=0)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Filter jobs by date range and agent if specified
        filtered_jobs = []
        for job in jobs:
            job_created = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
            if job_created >= start_date:
                if not agent_identifier or job.get("agent_identifier") == agent_identifier:
                    filtered_jobs.append(job)
        
        # Calculate statistics
        total_jobs = len(filtered_jobs)
        status_counts = {}
        agent_counts = {}
        total_execution_time = 0
        execution_count = 0
        
        for job in filtered_jobs:
            # Count by status
            status = job["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by agent
            agent = job.get("agent_identifier", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            # Calculate execution time for completed/failed jobs
            if status in ["completed", "failed"]:
                try:
                    created_at = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                    updated_at = datetime.fromisoformat(job["updated_at"].replace('Z', '+00:00'))
                    execution_time = (updated_at - created_at).total_seconds()
                    total_execution_time += execution_time
                    execution_count += 1
                except:
                    pass  # Skip if date parsing fails
        
        # Calculate derived metrics
        success_rate = 0
        avg_execution_time = 0
        
        if total_jobs > 0:
            completed_jobs = status_counts.get("completed", 0)
            success_rate = (completed_jobs / total_jobs) * 100
        
        if execution_count > 0:
            avg_execution_time = total_execution_time / execution_count
        
        analytics = {
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "totals": {
                "total_jobs": total_jobs,
                "completed_jobs": status_counts.get("completed", 0),
                "failed_jobs": status_counts.get("failed", 0),
                "pending_jobs": status_counts.get("pending", 0),
                "running_jobs": status_counts.get("running", 0)
            },
            "performance": {
                "success_rate_percentage": round(success_rate, 2),
                "average_execution_time_seconds": round(avg_execution_time, 2),
                "total_execution_time_seconds": round(total_execution_time, 2)
            },
            "breakdown": {
                "by_status": status_counts,
                "by_agent": agent_counts
            }
        }
        
        result_data = {
            "analytics": analytics,
            "filters": {
                "agent_identifier": agent_identifier
            } if agent_identifier else None
        }
        
        return create_success_response(
            result=result_data,
            message="Analytics summary retrieved successfully",
            metadata={
                "endpoint": "job_analytics",
                "user_id": user["id"],
                "period_days": days,
                "agent_filter": agent_identifier,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Jobs analytics retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve analytics",
            metadata={
                "error_code": "JOB_ANALYTICS_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 