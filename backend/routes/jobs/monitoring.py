"""
Job monitoring endpoints for the AI Agent Platform.

Handles:
- Job logs and execution history
- Job analytics and metrics
- Performance monitoring
- System health checks for job processing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from auth import get_current_user
from database import get_database_operations
from logging_system import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()

router = APIRouter(tags=["job-monitoring"])

@router.get("/{job_id}/logs")
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
    with perf_logger.time_operation("get_job_logs", user_id=user["id"], job_id=job_id):
        logger.info("Job logs requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # Verify job exists and user has access
            job = await db_ops.get_job(job_id, user_id=user["id"])
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or access denied"
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
            
            return {
                "success": True,
                "message": "Job logs retrieved successfully",
                "job_id": job_id,
                "logs": paginated_logs,
                "total_count": len(logs),
                "count": len(paginated_logs)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job logs retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve job logs: {str(e)}",
                    "error_code": "LOGS_RETRIEVAL_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/{job_id}/metrics")
async def get_job_metrics(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get performance metrics for a specific job.
    """
    with perf_logger.time_operation("get_job_metrics", user_id=user["id"], job_id=job_id):
        logger.info("Job metrics requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # Verify job exists and user has access
            job = await db_ops.get_job(job_id, user_id=user["id"])
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Job not found or access denied"
                )
            
            # Calculate basic metrics from job data
            created_at = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(job["updated_at"].replace('Z', '+00:00'))
            
            # Calculate execution time if job is completed or failed
            execution_time = None
            if job["status"] in ["completed", "failed"]:
                execution_time = (updated_at - created_at).total_seconds()
            
            metrics = {
                "job_id": job_id,
                "status": job["status"],
                "agent_identifier": job.get("agent_identifier"),
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "execution_time_seconds": execution_time,
                "priority": job.get("priority", 5),
                "has_result": bool(job.get("result")),
                "has_error": bool(job.get("error_message")),
                "data_size_bytes": len(str(job.get("job_data", job.get("data", {})))),
                "result_size_bytes": len(str(job.get("result", ""))) if job.get("result") else 0
            }
            
            return {
                "success": True,
                "message": "Job metrics retrieved successfully",
                "metrics": metrics
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job metrics retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve job metrics: {str(e)}",
                    "error_code": "METRICS_RETRIEVAL_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/analytics/summary")
async def get_jobs_analytics_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include"),
    agent_identifier: Optional[str] = Query(default=None, description="Filter by agent"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analytics summary for user's jobs.
    """
    with perf_logger.time_operation("get_jobs_analytics_summary", user_id=user["id"]):
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
            
            # Calculate analytics
            total_jobs = len(filtered_jobs)
            status_counts = {}
            agent_counts = {}
            total_execution_time = 0
            completed_jobs = 0
            
            for job in filtered_jobs:
                # Count by status
                status = job["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by agent
                agent = job.get("agent_identifier", "unknown")
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
                # Calculate execution time for completed/failed jobs
                if job["status"] in ["completed", "failed"]:
                    try:
                        created_at = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                        updated_at = datetime.fromisoformat(job["updated_at"].replace('Z', '+00:00'))
                        execution_time = (updated_at - created_at).total_seconds()
                        total_execution_time += execution_time
                        completed_jobs += 1
                    except:
                        pass  # Skip if date parsing fails
            
            # Calculate success rate
            success_rate = 0
            if total_jobs > 0:
                successful_jobs = status_counts.get("completed", 0)
                success_rate = (successful_jobs / total_jobs) * 100
            
            # Calculate average execution time
            avg_execution_time = 0
            if completed_jobs > 0:
                avg_execution_time = total_execution_time / completed_jobs
            
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
            
            return {
                "success": True,
                "message": "Analytics summary retrieved successfully",
                "analytics": analytics,
                "filters": {
                    "agent_identifier": agent_identifier
                } if agent_identifier else None
            }
            
        except Exception as e:
            logger.error("Jobs analytics retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve analytics: {str(e)}",
                    "error_code": "ANALYTICS_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/performance/agents")
async def get_agent_performance_metrics(
    days: int = Query(default=30, ge=1, le=90),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get performance metrics grouped by agent.
    """
    with perf_logger.time_operation("get_agent_performance_metrics", user_id=user["id"]):
        logger.info("Agent performance metrics requested", user_id=user["id"], days=days)
        
        try:
            db_ops = get_database_operations()
            
            # Get user jobs for analysis
            jobs = await db_ops.get_user_jobs(user["id"], limit=1000, offset=0)
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Filter jobs by date range
            filtered_jobs = []
            for job in jobs:
                job_created = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                if job_created >= start_date:
                    filtered_jobs.append(job)
            
            # Group by agent and calculate metrics
            agent_metrics = {}
            
            for job in filtered_jobs:
                agent = job.get("agent_identifier", "unknown")
                
                if agent not in agent_metrics:
                    agent_metrics[agent] = {
                        "agent_identifier": agent,
                        "total_jobs": 0,
                        "completed_jobs": 0,
                        "failed_jobs": 0,
                        "pending_jobs": 0,
                        "running_jobs": 0,
                        "total_execution_time": 0,
                        "execution_count": 0,
                        "success_rate": 0,
                        "average_execution_time": 0
                    }
                
                metrics = agent_metrics[agent]
                metrics["total_jobs"] += 1
                
                status = job["status"]
                if status == "completed":
                    metrics["completed_jobs"] += 1
                elif status == "failed":
                    metrics["failed_jobs"] += 1
                elif status == "pending":
                    metrics["pending_jobs"] += 1
                elif status == "running":
                    metrics["running_jobs"] += 1
                
                # Calculate execution time for completed/failed jobs
                if status in ["completed", "failed"]:
                    try:
                        created_at = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                        updated_at = datetime.fromisoformat(job["updated_at"].replace('Z', '+00:00'))
                        execution_time = (updated_at - created_at).total_seconds()
                        metrics["total_execution_time"] += execution_time
                        metrics["execution_count"] += 1
                    except:
                        pass  # Skip if date parsing fails
            
            # Calculate derived metrics
            for agent, metrics in agent_metrics.items():
                if metrics["total_jobs"] > 0:
                    metrics["success_rate"] = (metrics["completed_jobs"] / metrics["total_jobs"]) * 100
                
                if metrics["execution_count"] > 0:
                    metrics["average_execution_time"] = metrics["total_execution_time"] / metrics["execution_count"]
                
                # Round floating point values
                metrics["success_rate"] = round(metrics["success_rate"], 2)
                metrics["average_execution_time"] = round(metrics["average_execution_time"], 2)
                metrics["total_execution_time"] = round(metrics["total_execution_time"], 2)
            
            return {
                "success": True,
                "message": "Agent performance metrics retrieved successfully",
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "agents": list(agent_metrics.values())
            }
            
        except Exception as e:
            logger.error("Agent performance metrics retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve agent performance metrics: {str(e)}",
                    "error_code": "PERFORMANCE_METRICS_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

@router.get("/health")
async def get_jobs_health_status(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get overall health status of user's jobs.
    """
    with perf_logger.time_operation("get_jobs_health_status", user_id=user["id"]):
        try:
            db_ops = get_database_operations()
            
            # Get current job status counts
            status_counts = await db_ops.get_job_status_counts(user_id=user["id"])
            
            # Get recent failure rate
            recent_failure_rate = await db_ops.get_recent_failure_rate(
                user_id=user["id"],
                hours=24
            )
            
            # Determine overall health
            total_jobs = sum(status_counts.values())
            failed_jobs = status_counts.get("failed", 0)
            
            health_status = "healthy"
            if total_jobs > 0:
                failure_rate = failed_jobs / total_jobs
                if failure_rate > 0.5:
                    health_status = "critical"
                elif failure_rate > 0.2:
                    health_status = "warning"
            
            return {
                "success": True,
                "message": "Jobs health status retrieved successfully",
                "health": {
                    "status": health_status,
                    "total_jobs": total_jobs,
                    "status_breakdown": status_counts,
                    "recent_failure_rate": recent_failure_rate,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error("Jobs health status retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Failed to retrieve health status: {str(e)}",
                    "error_code": "HEALTH_STATUS_ERROR",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ) 