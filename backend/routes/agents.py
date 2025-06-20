"""
Agent routes for the AI Agent Platform.

Contains endpoints for:
- Agent discovery and listing
- Agent health checks
- Agent schema information
- Agent configuration management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from auth import get_current_user, get_optional_user
from agent_discovery import get_agent_discovery_system
from agent_framework import get_registered_agents
from agent import get_agent_registry
from config.agent_config import get_agent_config_manager, get_agent_config, AgentProfile, AgentPerformanceMode
from logging_system import get_logger
from models import ApiResponse
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Agent Response Types
AgentListResponse = Dict[str, Union[List[Dict[str, Any]], int, str, Dict[str, Any]]]
AgentInfoResponse = Dict[str, Any]
AgentHealthResponse = Dict[str, Any]
AgentSchemaResponse = Dict[str, Any]
AgentConfigListResponse = Dict[str, Union[Dict[str, Any], int]]
AgentConfigResponse = Dict[str, Any]
AgentConfigUpdateResponse = Dict[str, Any]
AgentConfigSaveResponse = Dict[str, Any]
AgentProfilesResponse = Dict[str, Any]
AgentProfileUpdateResponse = Dict[str, Any]

def log_agent_access(agent_identifier: str, action: str, user_id: Optional[str] = None, success: bool = True):
    """Log agent access for monitoring and analytics"""
    logger.info(
        f"Agent access: {action}",
        agent_identifier=agent_identifier,
        user_id=user_id,
        action=action,
        success=success
    )

@router.get("", response_model=ApiResponse[AgentListResponse])
@api_response_validator(result_type=AgentListResponse)
async def get_agents(user: Dict[str, Any] = Depends(get_optional_user)):
    """Get list of available agents with comprehensive information"""
    logger.info("Agent list requested", user_id=user["id"] if user else None)
    
    try:
        # Get discovery system
        discovery_system = get_agent_discovery_system()
        discovered_agents = discovery_system.get_discovered_agents()
        
        # Get registered agent instances
        registered_agents = get_registered_agents()
        
        agent_list = []
        for agent_id, metadata in discovered_agents.items():
            # Get the registered instance if available
            agent_instance = registered_agents.get(agent_id)
            
            agent_info = {
                "identifier": agent_id,
                "name": metadata.name,
                "description": metadata.description,
                "class_name": metadata.class_name,
                "version": metadata.version,
                "lifecycle_state": metadata.lifecycle_state.value,
                "supported_environments": [env.value for env in metadata.supported_environments],
                "created_at": metadata.created_at.isoformat(),
                "last_updated": metadata.last_updated.isoformat(),
                "metadata_extras": metadata.metadata_extras,
                "is_loaded": agent_instance is not None,
                "framework_version": "1.0"
            }
            
            # Temporarily removed agent instance information retrieval to isolate the issue
            # TODO: Fix underlying AttributeError in agent_instance.get_agent_info() before re-enabling
            # The issue is that some AttributeError objects are not JSON serializable
            # if agent_instance:
            #     try:
            #         instance_info = await agent_instance.get_agent_info()
            #         agent_info.update({
            #             "execution_count": instance_info.get("execution_count", 0),
            #             "last_execution_time": instance_info.get("last_execution_time"),
            #             "status": instance_info.get("status", "available"),
            #             "endpoints": instance_info.get("endpoints", []) if hasattr(agent_instance, 'get_endpoints') else [],
            #             "models": instance_info.get("models", []) if hasattr(agent_instance, 'get_models') else []
            #         })
            #         agent_info["has_error"] = False
            #     except Exception as e:
            #         logger.warning(f"Failed to get instance info for agent {agent_id}", exception=e)
            #         # Safely convert exception to string to avoid JSON serialization issues
            #         try:
            #             error_str = str(e)
            #         except:
            #             error_str = f"Error occurred in agent {agent_id}: {type(e).__name__}"
            #         
            #         agent_info.update({
            #             "execution_count": 0,
            #             "last_execution_time": None,
            #             "status": "error",
            #             "error": error_str,
            #             "has_error": True,
            #             "endpoints": [],
            #             "models": []
            #         })
            # elif metadata.load_error:
            if metadata.load_error:
                # Agent had a load error during discovery
                agent_info.update({
                    "status": "error",
                    "has_error": True,
                    "error_message": metadata.load_error,
                    "execution_count": 0,
                    "last_execution_time": None,
                    "endpoints": [],
                    "models": []
                })
            elif agent_instance is not None:
                # Agent is loaded and available - basic info without calling get_agent_info()
                agent_info.update({
                    "status": "available",
                    "has_error": False,
                    "execution_count": 0,
                    "last_execution_time": None,
                    "endpoints": [],
                    "models": []
                })
            else:
                # Agent is discovered but not loaded
                agent_info.update({
                    "status": "not_loaded",
                    "has_error": False,
                    "execution_count": 0,
                    "last_execution_time": None,
                    "endpoints": [],
                    "models": []
                })
            
            agent_list.append(agent_info)
        
        # Build result data with defensive error handling
        try:
            last_scan_time = None
            if hasattr(discovery_system, 'last_scan_time') and discovery_system.last_scan_time:
                if hasattr(discovery_system.last_scan_time, 'isoformat'):
                    last_scan_time = discovery_system.last_scan_time.isoformat()
                else:
                    last_scan_time = str(discovery_system.last_scan_time)
        except Exception as scan_time_error:
            logger.warning(f"Error getting last_scan_time: {scan_time_error}")
            last_scan_time = None
        
        try:
            scan_count = getattr(discovery_system, 'scan_count', 0)
        except Exception as scan_count_error:
            logger.warning(f"Error getting scan_count: {scan_count_error}")
            scan_count = 0
        
        result_data = {
            "agents": agent_list,
            "total_count": len(agent_list),
            "loaded_count": len(registered_agents),
            "discovery_info": {
                "last_scan": last_scan_time,
                "scan_count": scan_count
            }
        }
        
        return create_success_response(
            result=result_data,
            message=f"Found {len(agent_list)} agents ({len(registered_agents)} loaded)",
            metadata={
                "endpoint": "agents_list",
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        # Ensure the exception is properly converted to string to avoid JSON serialization issues
        error_message = str(e) if e else "Unknown error occurred"
        
        logger.error("Agent listing failed", exception=e, user_id=user["id"] if user else None)
        return create_error_response(
            error_message=error_message,
            message="Failed to retrieve agents",
            metadata={
                "error_code": "AGENTS_LIST_ERROR",
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_type": type(e).__name__ if e else "UnknownError"
            }
        )

@router.get("/{agent_name}", response_model=ApiResponse[AgentInfoResponse])
@api_response_validator(result_type=AgentInfoResponse)
async def get_agent_info(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get detailed information about a specific agent"""
    log_agent_access(agent_name, "info_request", user_id=user["id"] if user else None)
    
    try:
        # Get discovery system and check if agent exists
        discovery_system = get_agent_discovery_system()
        discovered_agents = discovery_system.get_discovered_agents()
        
        if agent_name not in discovered_agents:
            log_agent_access(agent_name, "info_request", user_id=user["id"] if user else None, success=False)
            return create_error_response(
                error_message=f"Agent '{agent_name}' not found",
                message="Agent not found in discovered agents",
                metadata={
                    "error_code": "AGENT_NOT_FOUND",
                    "agent_name": agent_name,
                    "user_id": user["id"] if user else None,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        metadata = discovered_agents[agent_name]
        
        # Get registered instance if available
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_name)
        
        # Build response with metadata
        agent_info = {
            "identifier": agent_name,
            "name": metadata.name,
            "description": metadata.description,
            "class_name": metadata.class_name,
            "version": metadata.version,
            "lifecycle_state": metadata.lifecycle_state.value,
            "supported_environments": [env.value for env in metadata.supported_environments],
            "created_at": metadata.created_at.isoformat(),
            "last_updated": metadata.last_updated.isoformat(),
            "metadata_extras": metadata.metadata_extras,
            "is_loaded": agent_instance is not None,
            "framework_version": "1.0"
        }
        
        # Add instance-specific information if loaded
        if agent_instance:
            try:
                instance_info = await agent_instance.get_agent_info()
                agent_info.update(instance_info)
                # Ensure status is set to available if no error occurred
                if "status" not in agent_info:
                    agent_info["status"] = "available"
            except Exception as e:
                logger.warning(f"Failed to get detailed info for agent {agent_name}", exception=e)
                agent_info["status"] = "error"
                agent_info["error"] = str(e)
        else:
            agent_info["status"] = "not_loaded"
            agent_info["message"] = "Agent discovered but not currently loaded"
        
        log_agent_access(agent_name, "info_request", user_id=user["id"] if user else None)
        
        return create_success_response(
            result=agent_info,
            message=f"Agent information retrieved for {agent_name}",
            metadata={
                "endpoint": "agent_info",
                "agent_name": agent_name,
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Agent info retrieval failed", exception=e, agent_name=agent_name, user_id=user["id"] if user else None)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve agent information",
            metadata={
                "error_code": "AGENT_INFO_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/{agent_name}/health", response_model=ApiResponse[AgentHealthResponse])
@api_response_validator(result_type=AgentHealthResponse)
async def get_agent_health(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get health status of a specific agent"""
    log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None)
    
    try:
        # Check if agent exists in registry
        registry = get_agent_registry()
        agent_instance = registry.get_agent(agent_name)
        
        if not agent_instance:
            # Check if agent is discovered but not loaded
            discovery_system = get_agent_discovery_system()
            discovered_agents = discovery_system.get_discovered_agents()
            
            if agent_name in discovered_agents:
                log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None, success=False)
                health_data = {
                    "agent_name": agent_name,
                    "status": "not_loaded",
                    "message": "Agent discovered but not currently loaded",
                    "is_available": False
                }
                return create_success_response(
                    result=health_data,
                    message="Agent not loaded",
                    metadata={
                        "endpoint": "agent_health",
                        "agent_name": agent_name,
                        "user_id": user["id"] if user else None,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            else:
                log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None, success=False)
                return create_error_response(
                    error_message=f"Agent '{agent_name}' not found",
                    message="Agent not found",
                    metadata={
                        "error_code": "AGENT_NOT_FOUND",
                        "agent_name": agent_name,
                        "user_id": user["id"] if user else None,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        
        # Get health status from agent
        health_status = await agent_instance.health_check()
        
        log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None)
        
        return create_success_response(
            result=health_status,
            message=f"Health check completed for {agent_name}",
            metadata={
                "endpoint": "agent_health",
                "agent_name": agent_name,
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Agent health check failed", exception=e, agent_name=agent_name, user_id=user["id"] if user else None)
        return create_error_response(
            error_message=str(e),
            message="Failed to check agent health",
            metadata={
                "error_code": "AGENT_HEALTH_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"] if user else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/{agent_id}/schema", response_model=ApiResponse[AgentSchemaResponse])
@api_response_validator(result_type=AgentSchemaResponse)
async def get_agent_schema(agent_id: str):
    """Get job data schema for an agent to enable dynamic form generation - public endpoint"""
    log_agent_access(agent_id, "schema_request")
    
    try:
        # Get discovery system and check if agent exists
        discovery_system = get_agent_discovery_system()
        discovered_agents = discovery_system.get_discovered_agents()
        
        if agent_id not in discovered_agents:
            log_agent_access(agent_id, "schema_request", success=False)
            return create_error_response(
                error_message=f"Agent '{agent_id}' not found in discovered agents",
                message="Agent not found",
                metadata={
                    "error_code": "AGENT_NOT_FOUND",
                    "agent_id": agent_id,
                    "suggestion": "Check available agents using GET /agents endpoint",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        metadata = discovered_agents[agent_id]
        
        # Try to get the registered instance
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_id)
        
        if not agent_instance:
            schema_data = {
                "agent_id": agent_id,
                "agent_name": metadata.name,
                "description": metadata.description,
                "agent_found": True,
                "instance_available": False,
                "available_models": [],
                "schemas": {}
            }
            return create_success_response(
                result=schema_data,
                message=f"Agent '{agent_id}' found but not currently loaded - schema unavailable",
                metadata={
                    "endpoint": "agent_schema",
                    "agent_id": agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Extract job data models from the agent
        models = agent_instance.get_models() if hasattr(agent_instance, 'get_models') else {}
        
        schema_info = {
            "agent_id": agent_id,
            "agent_name": metadata.name,
            "description": metadata.description,
            "available_models": list(models.keys()),
            "schemas": {}
        }
        
        # Generate JSON schemas for each model
        for model_name, model_class in models.items():
            try:
                # Generate Pydantic JSON schema
                schema = model_class.model_json_schema()
                
                # Enhance schema with additional metadata for form generation
                enhanced_schema = {
                    "model_name": model_name,
                    "model_class": model_class.__name__,
                    "title": schema.get("title", model_name),
                    "description": schema.get("description", f"Job data schema for {model_name}"),
                    "type": schema.get("type", "object"),
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                    "definitions": schema.get("$defs", schema.get("definitions", {}))
                }
                
                # Add form generation hints
                for prop_name, prop_schema in enhanced_schema["properties"].items():
                    # REMOVED: Automatic form_field_type inference to enable pure Pydantic inference
                    # Frontend will now infer field types from Pydantic constraints and types
                    pass
                
                schema_info["schemas"][model_name] = enhanced_schema
                
            except Exception as e:
                logger.warning(f"Failed to generate schema for model {model_name}", exception=e)
                schema_info["schemas"][model_name] = {
                    "error": f"Failed to generate schema: {str(e)}",
                    "model_name": model_name
                }
        
        schema_info["agent_found"] = True
        schema_info["instance_available"] = True
        
        log_agent_access(agent_id, "schema_request")
        
        return create_success_response(
            result=schema_info,
            message=f"Schema retrieved for agent: {agent_id}",
            metadata={
                "endpoint": "agent_schema",
                "agent_id": agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Agent schema retrieval failed", exception=e, agent_id=agent_id)
        log_agent_access(agent_id, "schema_request", success=False)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve agent schema",
            metadata={
                "error_code": "AGENT_SCHEMA_ERROR",
                "agent_id": agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/config/agents", response_model=ApiResponse[AgentConfigListResponse])
@api_response_validator(result_type=AgentConfigListResponse)
async def get_all_agent_configs(user: Dict[str, Any] = Depends(get_current_user)):
    """Get configuration for all agents"""
    logger.info("All agent configs requested", user_id=user["id"])
    
    try:
        config_manager = get_agent_config_manager()
        all_configs = config_manager.get_all_configs()
        
        result_data = {
            "configs": {name: config.to_dict() for name, config in all_configs.items()},
            "total_count": len(all_configs)
        }
        
        return create_success_response(
            result=result_data,
            message="All agent configurations retrieved",
            metadata={
                "endpoint": "agent_configs_list",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("All agent configs retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve agent configs",
            metadata={
                "error_code": "AGENT_CONFIGS_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/config/agents/{agent_name}", response_model=ApiResponse[AgentConfigResponse])
@api_response_validator(result_type=AgentConfigResponse)
async def get_agent_config_endpoint(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get configuration for a specific agent"""
    logger.info("Agent config requested", agent_name=agent_name, user_id=user["id"])
    
    try:
        config = get_agent_config(agent_name)
        
        result_data = {
            "agent_name": agent_name,
            "config": config.to_dict()
        }
        
        return create_success_response(
            result=result_data,
            message=f"Configuration retrieved for agent: {agent_name}",
            metadata={
                "endpoint": "agent_config",
                "agent_name": agent_name,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Agent config retrieval failed", exception=e, agent_name=agent_name, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message=f"Failed to retrieve config for {agent_name}",
            metadata={
                "error_code": "AGENT_CONFIG_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.put("/config/agents/{agent_name}", response_model=ApiResponse[AgentConfigUpdateResponse])
@api_response_validator(result_type=AgentConfigUpdateResponse)
async def update_agent_config_endpoint(
    agent_name: str,
    config_updates: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update configuration for a specific agent"""
    logger.info("Agent configuration update requested", agent_name=agent_name, user_id=user["id"])
    
    try:
        config_manager = get_agent_config_manager()
        
        # Validate the current config first
        current_config = config_manager.get_config(agent_name)
        
        # Apply updates temporarily for validation
        temp_config = current_config.from_dict({**current_config.to_dict(), **config_updates})
        validation_errors = config_manager.validate_config(temp_config)
        
        if validation_errors:
            result_data = {
                "success": False,
                "errors": validation_errors
            }
            return create_success_response(
                result=result_data,
                message="Configuration validation failed",
                metadata={
                    "endpoint": "agent_config_update",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "validation_failed": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Apply the updates
        success = config_manager.update_config(agent_name, config_updates)
        
        if success:
            result_data = {
                "success": True,
                "config": config_manager.get_config(agent_name).to_dict()
            }
            return create_success_response(
                result=result_data,
                message=f"Configuration updated for agent: {agent_name}",
                metadata={
                    "endpoint": "agent_config_update",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            return create_error_response(
                error_message="Failed to update configuration",
                message="Configuration update failed",
                metadata={
                    "error_code": "CONFIG_UPDATE_FAILED",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
    except Exception as e:
        logger.error("Agent config update failed", exception=e, agent_name=agent_name, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message=f"Failed to update config for {agent_name}",
            metadata={
                "error_code": "AGENT_CONFIG_UPDATE_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/config/agents/{agent_name}/save", response_model=ApiResponse[AgentConfigSaveResponse])
@api_response_validator(result_type=AgentConfigSaveResponse)
async def save_agent_config_endpoint(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Save current agent configuration to persistent storage"""
    logger.info("Agent config save requested", agent_name=agent_name, user_id=user["id"])
    
    try:
        config_manager = get_agent_config_manager()
        success = config_manager.save_config(agent_name)
        
        if success:
            result_data = {
                "success": True
            }
            return create_success_response(
                result=result_data,
                message=f"Configuration saved for agent: {agent_name}",
                metadata={
                    "endpoint": "agent_config_save",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            return create_error_response(
                error_message="Failed to save configuration",
                message="Configuration save failed",
                metadata={
                    "error_code": "CONFIG_SAVE_FAILED",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
    except Exception as e:
        logger.error("Agent config save failed", exception=e, agent_name=agent_name, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message=f"Failed to save config for {agent_name}",
            metadata={
                "error_code": "AGENT_CONFIG_SAVE_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/config/profiles", response_model=ApiResponse[AgentProfilesResponse])
@api_response_validator(result_type=AgentProfilesResponse)
async def get_available_profiles(user: Dict[str, Any] = Depends(get_current_user)):
    """Get available agent profiles and performance modes"""
    logger.info("Available profiles requested", user_id=user["id"])
    
    try:
        profiles = {
            "agent_profiles": [
                {"value": profile.value, "name": profile.name, "description": f"Agent profile: {profile.value}"}
                for profile in AgentProfile
            ],
            "performance_modes": [
                {"value": mode.value, "name": mode.name, "description": f"Performance mode: {mode.value}"}
                for mode in AgentPerformanceMode
            ]
        }
        
        return create_success_response(
            result={"profiles": profiles},
            message="Available profiles and performance modes retrieved",
            metadata={
                "endpoint": "agent_profiles",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Available profiles retrieval failed", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve available profiles",
            metadata={
                "error_code": "AGENT_PROFILES_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.post("/config/agents/{agent_name}/profile", response_model=ApiResponse[AgentProfileUpdateResponse])
@api_response_validator(result_type=AgentProfileUpdateResponse)
async def set_agent_profile(
    agent_name: str,
    profile_data: Dict[str, str],
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Set agent profile and performance mode"""
    logger.info("Agent profile update requested", agent_name=agent_name, user_id=user["id"])
    
    try:
        config_manager = get_agent_config_manager()
        
        # Validate profile and performance mode
        profile = profile_data.get("profile")
        performance_mode = profile_data.get("performance_mode")
        
        if profile and profile not in [p.value for p in AgentProfile]:
            return create_error_response(
                error_message=f"Invalid profile: {profile}",
                message="Invalid profile specified",
                metadata={
                    "error_code": "INVALID_PROFILE",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        if performance_mode and performance_mode not in [m.value for m in AgentPerformanceMode]:
            return create_error_response(
                error_message=f"Invalid performance mode: {performance_mode}",
                message="Invalid performance mode specified",
                metadata={
                    "error_code": "INVALID_PERFORMANCE_MODE",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Update config
        updates = {}
        if profile:
            updates["profile"] = profile
        if performance_mode:
            updates["performance_mode"] = performance_mode
        
        success = config_manager.update_config(agent_name, updates)
        
        if success:
            result_data = {
                "success": True,
                "config": config_manager.get_config(agent_name).to_dict()
            }
            return create_success_response(
                result=result_data,
                message=f"Profile updated for agent: {agent_name}",
                metadata={
                    "endpoint": "agent_profile_update",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            return create_error_response(
                error_message="Failed to update profile",
                message="Profile update failed",
                metadata={
                    "error_code": "PROFILE_UPDATE_FAILED",
                    "agent_name": agent_name,
                    "user_id": user["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
    except Exception as e:
        logger.error("Agent profile update failed", exception=e, agent_name=agent_name, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message=f"Failed to update profile for {agent_name}",
            metadata={
                "error_code": "AGENT_PROFILE_UPDATE_ERROR",
                "agent_name": agent_name,
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 