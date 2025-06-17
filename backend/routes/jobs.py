"""
Job routes for the AI Agent Platform.

Contains endpoints for:
- Job creation and validation
- Job listing and retrieval
- Job status management
- Job operations (retry, rerun, delete)
- Job logging and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from auth import get_current_user
from database import get_database_operations
from job_pipeline import get_job_pipeline
from agent_discovery import get_agent_discovery_system
from agent_framework import get_registered_agents
from agent import get_agent_registry, AgentError, AgentNotFoundError, AgentDisabledError, AgentNotLoadedError
from models import (
    JobCreateRequest, JobCreateResponse, JobListResponse, 
    JobDetailResponse, JobResponse
)
from logging_system import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()

router = APIRouter(prefix="/jobs", tags=["jobs"])

def log_agent_access(agent_identifier: str, operation: str, user_id: str = None, success: bool = True):
    """Log agent access for monitoring and analytics"""
    logger.info(
        f"Agent access: {operation}",
        agent_identifier=agent_identifier,
        user_id=user_id,
        operation=operation,
        success=success
    )

def validate_agent_exists_and_enabled(agent_identifier: str, require_loaded: bool = False) -> Dict[str, Any]:
    """
    Validate that an agent exists and is enabled for use.
    
    Args:
        agent_identifier: The agent identifier to validate
        require_loaded: Whether to require the agent to be loaded in memory
        
    Returns:
        dict: Validation result with metadata
        
    Raises:
        AgentNotFoundError: If agent doesn't exist
        AgentDisabledError: If agent is disabled
        AgentNotLoadedError: If agent is not loaded and require_loaded=True
    """
    try:
        # Get discovery system and check if agent exists
        discovery_system = get_agent_discovery_system()
        discovered_agents = discovery_system.get_discovered_agents()
        
        if agent_identifier not in discovered_agents:
            raise AgentNotFoundError(
                agent_identifier,
                f"Agent '{agent_identifier}' not found in discovered agents"
            )
        
        metadata = discovered_agents[agent_identifier]
        
        # Check if agent is enabled (based on lifecycle state)
        if metadata.lifecycle_state.value in ['disabled', 'deprecated']:
            raise AgentDisabledError(
                agent_identifier, 
                metadata.lifecycle_state.value,
                f"Agent '{agent_identifier}' is {metadata.lifecycle_state.value}"
            )
        
        # Check if agent is loaded if required
        if require_loaded:
            registered_agents = get_registered_agents()
            if agent_identifier not in registered_agents:
                raise AgentNotLoadedError(
                    agent_identifier,
                    f"Agent '{agent_identifier}' is not currently loaded"
                )
        
        return {
            "valid": True,
            "metadata": {
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "lifecycle_state": metadata.lifecycle_state.value,
                "class_name": metadata.class_name
            }
        }
        
    except (AgentNotFoundError, AgentDisabledError, AgentNotLoadedError):
        # Re-raise agent-specific errors
        raise
    except Exception as e:
        logger.error(f"Error validating agent '{agent_identifier}'", exception=e)
        raise AgentError(
            status_code=500,
            detail=f"Error validating agent '{agent_identifier}': {str(e)}"
        )

async def _validate_job_data_against_agent_schema(agent_identifier: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate job data against agent's defined schema requirements.
    
    Returns:
        dict: Validation result with 'valid', 'errors', 'model_used', and 'schema_info' fields
    """
    try:
        # Get registered agents to access schema information
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_identifier)
        
        if not agent_instance:
            # Try to get from registry as fallback
            registry = get_agent_registry()
            agent_instance = registry.get_agent(agent_identifier)
        
        if not agent_instance:
            # Agent not loaded - allow but log warning
            logger.warning(f"Agent '{agent_identifier}' not loaded for validation - allowing job creation")
            return {
                "valid": True,
                "warnings": [f"Agent '{agent_identifier}' not loaded - schema validation skipped"],
                "model_used": None
            }
        
        # Extract job data models from the agent
        models = agent_instance.get_models() if hasattr(agent_instance, 'get_models') else {}
        
        if not models:
            # No models defined - allow generic data
            logger.info(f"Agent '{agent_identifier}' has no defined models - allowing generic job data")
            return {
                "valid": True,
                "warnings": [f"Agent '{agent_identifier}' has no defined job data models"],
                "model_used": None
            }
        
        # Try to find the most appropriate model for validation
        # Priority: exact match by model name, single model, first available model
        model_to_use = None
        model_name = None
        
        # If only one model, use it
        if len(models) == 1:
            model_name, model_to_use = next(iter(models.items()))
        else:
            # Use the first model available (agents should typically define one primary model)
            model_name, model_to_use = next(iter(models.items()))
        
        # Validate the job data against the selected model
        try:
            # Create an instance of the model to validate the data
            validated_data = model_to_use(**job_data)
            
            return {
                "valid": True,
                "model_used": model_name,
                "validated_data": validated_data.dict(),
                "schema_info": {
                    "model_name": model_name,
                    "available_models": list(models.keys())
                }
            }
            
        except Exception as validation_error:
            # Extract meaningful validation errors
            errors = []
            if hasattr(validation_error, 'errors'):
                # Pydantic validation errors
                for error in validation_error.errors():
                    field_path = " -> ".join(str(loc) for loc in error['loc'])
                    errors.append({
                        "field": field_path,
                        "message": error['msg'],
                        "type": error['type'],
                        "input": error.get('input')
                    })
            else:
                errors.append({
                    "field": "general",
                    "message": str(validation_error),
                    "type": "validation_error"
                })
            
            # Get schema information for helpful error response
            schema_info = {
                "model_name": model_name,
                "available_models": list(models.keys()),
                "schema": model_to_use.model_json_schema() if hasattr(model_to_use, 'model_json_schema') else None
            }
            
            return {
                "valid": False,
                "errors": errors,
                "model_used": model_name,
                "schema_info": schema_info
            }
        
    except Exception as e:
        logger.error(f"Error during job data validation for agent '{agent_identifier}'", exception=e)
        return {
            "valid": True,  # Allow on system errors
            "warnings": [f"Validation system error: {str(e)}"],
            "model_used": None
        }

@router.post("", response_model=JobCreateResponse)
async def create_job(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new job for processing"""
    with perf_logger.time_operation("create_job", user_id=user["id"]):
        log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"])
        
        try:
            # Use centralized validation - job creation requires enabled agents
            validation_result = validate_agent_exists_and_enabled(request.agent_identifier)
            agent_metadata = validation_result["metadata"]
            
            # Validate job data against agent schema requirements
            schema_validation_result = await _validate_job_data_against_agent_schema(
                request.agent_identifier, 
                request.data
            )
            
            if not schema_validation_result["valid"]:
                log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
                logger.warning(
                    "Job data validation failed",
                    agent_identifier=request.agent_identifier,
                    user_id=user["id"],
                    validation_errors=schema_validation_result["errors"]
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Job data validation failed",
                        "agent_identifier": request.agent_identifier,
                        "validation_errors": schema_validation_result["errors"],
                        "expected_schema": schema_validation_result.get("schema_info")
                    }
                )
            
            # Generate job ID as proper UUID
            job_id = str(uuid.uuid4())
            
            # Get database operations
            db_ops = get_database_operations()
            
            # Create job in database with agent_identifier
            job_data = {
                "id": job_id,
                "user_id": user["id"],
                "agent_identifier": request.agent_identifier,
                "status": "pending",
                "data": request.data,
                "priority": request.priority or 0,
                "tags": request.tags or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            created_job = await db_ops.create_job(job_data)
            
            # Submit job to pipeline for processing
            pipeline = get_job_pipeline()
            if pipeline and pipeline.is_running:
                await pipeline.submit_job(
                    job_id=created_job["id"],
                    user_id=created_job["user_id"],
                    agent_name=created_job["agent_identifier"],
                    job_data=created_job["data"],
                    priority=created_job.get("priority", 5),
                    tags=created_job.get("tags", [])
                )
                logger.info("Job submitted to pipeline", job_id=job_id, user_id=user["id"], agent_identifier=request.agent_identifier)
            else:
                logger.warning("Job created but pipeline not running", job_id=job_id, user_id=user["id"])
            
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"])
            
            return JobCreateResponse(
                success=True,
                message="Job created successfully",
                job_id=job_id,
                job=created_job
            )
            
        except AgentError:
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
            # Re-raise agent-specific errors as they have proper HTTP status codes
            raise
        except HTTPException:
            raise
        except Exception as e:
            log_agent_access(request.agent_identifier, "job_creation", user_id=user["id"], success=False)
            logger.error("Job creation failed", exception=e, user_id=user["id"], agent_identifier=getattr(request, 'agent_identifier', 'unknown'))
            raise HTTPException(status_code=500, detail=f"Job creation failed: {str(e)}")

@router.get("", response_model=JobListResponse)
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List jobs for the current user"""
    with perf_logger.time_operation("list_jobs", user_id=user["id"]):
        logger.info("Job list requested", user_id=user["id"], limit=limit, offset=offset)
        
        try:
            db_ops = get_database_operations()
            jobs = await db_ops.get_user_jobs(user["id"], limit=limit, offset=offset)
            
            job_responses = []
            for job in jobs:
                job_responses.append(JobResponse(
                    id=job["id"],
                    status=job["status"],
                    agent_identifier=job.get("agent_identifier", "unknown"),
                    data=job["data"],
                    result=job.get("result"),
                    error_message=job.get("error_message"),
                    created_at=job["created_at"],
                    updated_at=job["updated_at"]
                ))
            
            logger.info("Job list retrieved", user_id=user["id"], count=len(job_responses))
            
            return JobListResponse(
                success=True,
                message="Jobs retrieved successfully",
                jobs=job_responses,
                total_count=len(job_responses)
            )
            
        except Exception as e:
            logger.error("Job list retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve jobs: {str(e)}")

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific job"""
    with perf_logger.time_operation("get_job", user_id=user["id"]):
        logger.info("Job detail requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                logger.warning("Job not found or access denied", job_id=job_id, user_id=user["id"])
                raise HTTPException(status_code=404, detail="Job not found or access denied")
            
            logger.info("Job detail retrieved", job_id=job_id, user_id=user["id"], status=job.get("status"))
            
            return JobDetailResponse(
                success=True,
                message="Job retrieved successfully",
                job=job
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {str(e)}")

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific job"""
    with perf_logger.time_operation("delete_job", user_id=user["id"], job_id=job_id):
        logger.info("Job deletion requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            success = await db_ops.delete_job(job_id, user_id=user["id"])
            
            if not success:
                raise HTTPException(status_code=404, detail="Job not found")
            
            logger.info("Job deleted successfully", job_id=job_id, user_id=user["id"])
            
            return {
                "success": True,
                "message": "Job deleted successfully",
                "job_id": job_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job deletion failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get status of a specific job"""
    with perf_logger.time_operation("get_job_status", user_id=user["id"], job_id=job_id):
        logger.info("Job status requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            job = await db_ops.get_job(job_id, user_id=user["id"])
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return {
                "success": True,
                "message": "Job status retrieved",
                "data": {
                    "status": job["status"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job status retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.post("/batch/status")
async def get_batch_job_status(
    request: Dict[str, List[str]],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get status for multiple jobs in batch"""
    with perf_logger.time_operation("get_batch_job_status", user_id=user["id"]):
        job_ids = request.get("job_ids", [])
        logger.info("Batch job status requested", user_id=user["id"], job_count=len(job_ids))
        
        try:
            db_ops = get_database_operations()
            statuses = {}
            
            for job_id in job_ids:
                try:
                    job = await db_ops.get_job(job_id, user_id=user["id"])
                    if job:
                        statuses[job_id] = {
                            "status": job["status"],
                            "updated_at": job.get("updated_at")
                        }
                    else:
                        statuses[job_id] = {"status": "not_found"}
                except Exception as e:
                    logger.warning(f"Failed to get status for job {job_id}", exception=e)
                    statuses[job_id] = {"status": "error", "error": str(e)}
            
            return {
                "success": True,
                "message": f"Batch status retrieved for {len(statuses)} jobs",
                "statuses": statuses
            }
            
        except Exception as e:
            logger.error("Batch job status retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to get batch job status: {str(e)}")

@router.get("/minimal")
async def get_jobs_minimal(
    limit: int = 50,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get minimal job information for dashboard/overview purposes"""
    with perf_logger.time_operation("get_jobs_minimal", user_id=user["id"]):
        logger.info("Minimal job list requested", user_id=user["id"], limit=limit, offset=offset)
        
        try:
            db_ops = get_database_operations()
            jobs = await db_ops.get_user_jobs_minimal(user["id"], limit=limit, offset=offset)
            
            return {
                "success": True,
                "message": "Minimal jobs retrieved successfully",
                "jobs": jobs,
                "total_count": len(jobs)
            }
            
        except Exception as e:
            logger.error("Minimal job retrieval failed", exception=e, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve minimal jobs: {str(e)}")

@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Retry a failed job"""
    with perf_logger.time_operation("retry_job", user_id=user["id"], job_id=job_id):
        logger.info("Job retry requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # Get the job to verify ownership and status
            job = await db_ops.get_job(job_id, user_id=user["id"])
            if not job:
                raise HTTPException(status_code=404, detail="Job not found or access denied")
            
            # Check if job can be retried
            if job["status"] not in ["failed", "error"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Job cannot be retried. Current status: {job['status']}"
                )
            
            # Update job status to pending for retry
            await db_ops.update_job_status(job_id, "pending", None)
            
            # Resubmit to pipeline
            pipeline = get_job_pipeline()
            if pipeline and pipeline.is_running:
                await pipeline.submit_job(
                    job_id=job["id"],
                    user_id=job["user_id"],
                    agent_name=job["agent_identifier"],
                    job_data=job["data"],
                    priority=job.get("priority", 5),
                    tags=job.get("tags", [])
                )
                logger.info("Job resubmitted for retry", job_id=job_id, user_id=user["id"])
                
                return {
                    "success": True,
                    "message": "Job retry initiated successfully",
                    "job_id": job_id,
                    "new_status": "pending"
                }
            else:
                logger.warning("Job retry requested but pipeline not running", job_id=job_id, user_id=user["id"])
                return {
                    "success": False,
                    "message": "Job pipeline is not running - retry cannot be processed",
                    "job_id": job_id
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job retry failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")

@router.post("/{job_id}/rerun")
async def rerun_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Rerun a job (create new job with same parameters)"""
    with perf_logger.time_operation("rerun_job", user_id=user["id"], job_id=job_id):
        logger.info("Job rerun requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # Get the original job
            original_job = await db_ops.get_job(job_id, user_id=user["id"])
            if not original_job:
                raise HTTPException(status_code=404, detail="Original job not found or access denied")
            
            # Create new job with same parameters
            new_job_id = str(uuid.uuid4())
            new_job_data = {
                "id": new_job_id,
                "user_id": user["id"],
                "agent_identifier": original_job["agent_identifier"],
                "status": "pending",
                "data": original_job["data"],
                "priority": original_job.get("priority", 0),
                "tags": original_job.get("tags", []) + ["rerun"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "rerun_from": job_id,
                    "original_created_at": original_job.get("created_at")
                }
            }
            
            created_job = await db_ops.create_job(new_job_data)
            
            # Submit to pipeline
            pipeline = get_job_pipeline()
            if pipeline and pipeline.is_running:
                await pipeline.submit_job(
                    job_id=created_job["id"],
                    user_id=created_job["user_id"],
                    agent_name=created_job["agent_identifier"],
                    job_data=created_job["data"],
                    priority=created_job.get("priority", 5),
                    tags=created_job.get("tags", [])
                )
                logger.info("New job created and submitted for rerun", original_job_id=job_id, new_job_id=new_job_id, user_id=user["id"])
                
                return {
                    "success": True,
                    "message": "Job rerun initiated successfully",
                    "original_job_id": job_id,
                    "new_job_id": new_job_id,
                    "new_job": created_job
                }
            else:
                logger.warning("Job rerun requested but pipeline not running", job_id=job_id, user_id=user["id"])
                return {
                    "success": False,
                    "message": "Job pipeline is not running - rerun cannot be processed",
                    "job_id": job_id
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job rerun failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to rerun job: {str(e)}")

@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get logs for a specific job"""
    with perf_logger.time_operation("get_job_logs", user_id=user["id"], job_id=job_id):
        logger.info("Job logs requested", job_id=job_id, user_id=user["id"])
        
        try:
            db_ops = get_database_operations()
            
            # First verify the job exists and user has access
            job = await db_ops.get_job(job_id, user_id=user["id"])
            if not job:
                raise HTTPException(status_code=404, detail="Job not found or access denied")
            
            # Get job logs
            logs = await db_ops.get_job_logs(job_id)
            
            return {
                "success": True,
                "message": "Job logs retrieved successfully",
                "job_id": job_id,
                "logs": logs,
                "log_count": len(logs)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Job logs retrieval failed", exception=e, job_id=job_id, user_id=user["id"])
            raise HTTPException(status_code=500, detail=f"Failed to retrieve job logs: {str(e)}")

@router.post("/validate")
async def validate_job_data(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate job data without creating the job"""
    with perf_logger.time_operation("validate_job_data", user_id=user["id"]):
        logger.info("Job data validation requested", user_id=user["id"], agent_identifier=request.agent_identifier)
        
        try:
            # Validate agent exists and is enabled
            validation_result = validate_agent_exists_and_enabled(request.agent_identifier)
            agent_metadata = validation_result["metadata"]
            
            # Validate job data against agent schema
            schema_validation_result = await _validate_job_data_against_agent_schema(
                request.agent_identifier, 
                request.data
            )
            
            response = {
                "success": True,
                "message": "Job data validation completed",
                "agent_identifier": request.agent_identifier,
                "agent_metadata": agent_metadata,
                "validation_result": schema_validation_result
            }
            
            if not schema_validation_result["valid"]:
                response["success"] = False
                response["message"] = "Job data validation failed"
            
            return response
            
        except AgentError as e:
            logger.warning("Job validation failed due to agent error", exception=e, user_id=user["id"], agent_identifier=request.agent_identifier)
            return {
                "success": False,
                "message": "Agent validation failed",
                "agent_identifier": request.agent_identifier,
                "error": str(e),
                "error_type": type(e).__name__
            }
        except Exception as e:
            logger.error("Job data validation failed", exception=e, user_id=user["id"], agent_identifier=request.agent_identifier)
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}") 