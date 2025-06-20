"""
Job creation endpoints for the AI Agent Platform.

Handles:
- Job creation with validation
- Job data validation against agent schemas
- Agent availability checking
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Union, List
from datetime import datetime, timezone
import uuid

from auth import get_current_user
from database import get_database_operations
from job_pipeline import get_job_pipeline
from agent_discovery import get_agent_discovery_system
from agent_framework import get_registered_agents
from agent import get_agent_registry, AgentError, AgentNotFoundError, AgentDisabledError, AgentNotLoadedError
from models import JobCreateRequest, ApiResponse
from logging_system import get_logger
from utils.responses import (
    create_success_response,
    create_error_response,
    create_validation_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["job-creation"])

# Job Creation Response Types
CreateJobResponse = Dict[str, Union[str, bool, Dict[str, Any]]]
ValidationResult = Dict[str, Union[bool, str, Dict[str, Any], List[Dict[str, Any]]]]

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
                "warnings": [f"Agent '{agent_identifier}' has no defined job data models"],
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
        logger.error(f"Error validating job data against agent schema for '{agent_identifier}'", exception=e)
        return {
            "valid": False,
            "errors": [{
                "field": "general",
                "message": f"Schema validation failed: {str(e)}",
                "type": "validation_error"
            }],
            "model_used": None
        }

@router.post("/create", response_model=ApiResponse[CreateJobResponse])
@api_response_validator(result_type=CreateJobResponse)
async def create_job(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new job for processing.
    
    Validates agent availability and job data before creation.
    """
    logger.info(
        "Job creation requested",
        agent_identifier=request.agent_identifier,
        user_id=user["id"],
        data_size=len(str(request.data)),
        priority=request.priority
    )
    
    try:
        # Validate agent exists and is enabled
        agent_validation = validate_agent_exists_and_enabled(request.agent_identifier)
        log_agent_access(request.agent_identifier, "job_creation_request", user["id"], True)
        
        # Validate job data against agent schema
        schema_validation = await _validate_job_data_against_agent_schema(
            request.agent_identifier, 
            request.data
        )
        
        if not schema_validation["valid"]:
            logger.warning(
                "Job data validation failed",
                agent_identifier=request.agent_identifier,
                user_id=user["id"],
                errors=schema_validation["errors"]
            )
            
            # Convert validation errors to proper format for create_validation_error_response
            validation_errors = []
            for error in schema_validation["errors"]:
                validation_errors.append({
                    "loc": [error["field"]],
                    "msg": error["message"],
                    "type": error["type"]
                })
            
            return create_validation_error_response(
                validation_errors=validation_errors,
                message="Job data validation failed"
            )
        
        # Create job record
        db_ops = get_database_operations()
        job_data = {
            "user_id": user["id"],
            "agent_identifier": request.agent_identifier,
            "data": request.data,
            "title": request.title,
            "priority": request.priority,
            "tags": request.tags,
            "status": "pending"
        }
        
        job = await db_ops.create_job(job_data)
        
        if not job:
            return create_error_response(
                error_message="Failed to create job record",
                message="Job creation failed",
                metadata={
                    "error_code": "JOB_CREATION_FAILED",
                    "agent_identifier": request.agent_identifier,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Submit job to processing pipeline
        pipeline = get_job_pipeline()
        pipeline_submitted = await pipeline.submit_job(
            job_id=job["id"],
            user_id=user["id"],
            agent_name=request.agent_identifier,
            job_data=request.data,
            priority=request.priority or 5,
            tags=request.tags
        )
        
        if not pipeline_submitted:
            logger.warning(
                "Job created but failed to submit to pipeline",
                job_id=job["id"],
                agent_identifier=request.agent_identifier,
                user_id=user["id"]
            )
        
        logger.info(
            "Job created successfully",
            job_id=job["id"],
            agent_identifier=request.agent_identifier,
            user_id=user["id"],
            status="pending",
            pipeline_submitted=pipeline_submitted
        )
        
        result_data = {
            "job_id": job["id"],
            "job": job,
            "pipeline_submitted": pipeline_submitted
        }
        
        return create_success_response(
            result=result_data,
            message="Job created successfully",
            metadata={
                "endpoint": "create_job",
                "job_id": job["id"],
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except (AgentNotFoundError, AgentDisabledError, AgentNotLoadedError) as e:
        log_agent_access(request.agent_identifier, "job_creation_failed", user["id"], False)
        logger.warning(
            "Agent validation failed for job creation",
            agent_identifier=request.agent_identifier,
            user_id=user["id"],
            error=str(e)
        )
        return create_error_response(
            error_message=str(e),
            message="Agent validation failed",
            metadata={
                "error_code": "AGENT_ERROR",
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error(
            "Job creation failed",
            exception=e,
            agent_identifier=request.agent_identifier,
            user_id=user["id"]
        )
        return create_error_response(
            error_message=str(e),
            message="Failed to create job",
            metadata={
                "error_code": "JOB_CREATION_ERROR",
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/validate", response_model=ApiResponse[ValidationResult])
@api_response_validator(result_type=ValidationResult)
async def validate_job_data(
    request: JobCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate job data against agent schema without creating the job.
    
    Useful for form validation and pre-flight checks.
    """
    logger.info(
        "Job data validation requested",
        agent_identifier=request.agent_identifier,
        user_id=user["id"]
    )
    
    try:
        # Validate agent exists and is enabled
        agent_validation = validate_agent_exists_and_enabled(request.agent_identifier)
        
        # Validate job data against agent schema
        schema_validation = await _validate_job_data_against_agent_schema(
            request.agent_identifier, 
            request.data
        )
        
        result_data = {
            "validation_result": {
                "agent_valid": agent_validation["valid"],
                "data_valid": schema_validation["valid"],
                "errors": schema_validation.get("errors", []),
                "warnings": schema_validation.get("warnings", []),
                "schema_info": schema_validation.get("schema_info"),
                "model_used": schema_validation.get("model_used")
            },
            "agent_metadata": agent_validation["metadata"]
        }
        
        return create_success_response(
            result=result_data,
            message="Validation completed",
            metadata={
                "endpoint": "validate_job_data",
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except (AgentNotFoundError, AgentDisabledError, AgentNotLoadedError) as e:
        logger.warning(
            "Agent validation failed",
            agent_identifier=request.agent_identifier,
            user_id=user["id"],
            error=str(e)
        )
        
        result_data = {
            "validation_result": {
                "agent_valid": False,
                "data_valid": False,
                "errors": [{"field": "agent", "message": str(e), "type": "agent_error"}]
            }
        }
        
        return create_success_response(
            result=result_data,
            message=str(e),
            metadata={
                "endpoint": "validate_job_data",
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "agent_validation_failed": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error(
            "Job data validation failed",
            exception=e,
            agent_identifier=request.agent_identifier,
            user_id=user["id"]
        )
        return create_error_response(
            error_message=str(e),
            message="Validation failed",
            metadata={
                "error_code": "VALIDATION_ERROR",
                "agent_identifier": request.agent_identifier,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 