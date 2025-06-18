"""
Agent routes for the AI Agent Platform.

Contains endpoints for:
- Agent discovery and listing
- Agent health checks
- Agent schema information
- Agent configuration management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from auth import get_current_user, get_optional_user
from agent_discovery import get_agent_discovery_system
from agent_framework import get_registered_agents
from agent import get_agent_registry
from config.agent_config import get_agent_config_manager, get_agent_config, AgentProfile, AgentPerformanceMode
from logging_system import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

def log_agent_access(agent_identifier: str, action: str, user_id: Optional[str] = None, success: bool = True):
    """Log agent access for monitoring and analytics"""
    logger.info(
        f"Agent access: {action}",
        agent_identifier=agent_identifier,
        user_id=user_id,
        action=action,
        success=success
    )

def _infer_form_field_type(prop_schema: Dict[str, Any]) -> str:
    """Infer appropriate form field type from property schema - DEPRECATED"""
    # This function is no longer used - frontend now does pure Pydantic inference
    return "text"

@router.get("")
async def get_agents(user: Dict[str, Any] = Depends(get_optional_user)):
    """Get list of available agents with comprehensive information"""
    logger.info("Agent list requested", user_id=user["id"] if user else None)
    
    try:
        # Get discovery system
        discovery_system = get_agent_discovery_system()
        
        # Get all discovered agents
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
            
            # Add instance-specific information if available
            if agent_instance:
                try:
                    instance_info = await agent_instance.get_agent_info()
                    agent_info.update({
                        "execution_count": instance_info.get("execution_count", 0),
                        "last_execution_time": instance_info.get("last_execution_time"),
                        "status": instance_info.get("status", "unknown"),
                        "endpoints": instance_info.get("endpoints", []) if hasattr(agent_instance, 'get_endpoints') else [],
                        "models": instance_info.get("models", []) if hasattr(agent_instance, 'get_models') else []
                    })
                except Exception as e:
                    logger.warning(f"Failed to get instance info for agent {agent_id}", exception=e)
                    agent_info.update({
                        "execution_count": 0,
                        "last_execution_time": None,
                        "status": "error",
                        "error": str(e)
                    })
            
            agent_list.append(agent_info)
        
        return {
            "success": True,
            "agents": agent_list,
            "total_count": len(agent_list),
            "loaded_count": len(registered_agents),
            "discovery_info": {
                "last_scan": discovery_system.last_scan_time.isoformat() if discovery_system.last_scan_time else None,
                "scan_count": getattr(discovery_system, 'scan_count', 0)
            },
            "message": f"Found {len(agent_list)} agents ({len(registered_agents)} loaded)"
        }
        
    except Exception as e:
        logger.error("Agent listing failed", exception=e, user_id=user["id"] if user else None)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {str(e)}")

@router.get("/{agent_name}")
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
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
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
            except Exception as e:
                logger.warning(f"Failed to get detailed info for agent {agent_name}", exception=e)
                agent_info["status"] = "error"
                agent_info["error"] = str(e)
        else:
            agent_info["status"] = "not_loaded"
            agent_info["message"] = "Agent discovered but not currently loaded"
        
        log_agent_access(agent_name, "info_request", user_id=user["id"] if user else None)
        agent_info["success"] = True
        return agent_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Agent info retrieval failed", exception=e, agent_name=agent_name, user_id=user["id"] if user else None)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent info: {str(e)}")

@router.get("/{agent_name}/health")
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
                return {
                    "agent_name": agent_name,
                    "status": "not_loaded",
                    "message": "Agent discovered but not currently loaded",
                    "is_available": False
                }
            else:
                log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None, success=False)
                raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Get health status from agent
        health_status = await agent_instance.health_check()
        
        log_agent_access(agent_name, "health_check", user_id=user["id"] if user else None)
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Agent health check failed", exception=e, agent_name=agent_name, user_id=user["id"] if user else None)
        raise HTTPException(status_code=500, detail=f"Failed to check agent health: {str(e)}")

@router.get("/{agent_id}/schema")
async def get_agent_schema(agent_id: str):
    """Get job data schema for an agent to enable dynamic form generation - public endpoint"""
    log_agent_access(agent_id, "schema_request")
    
    try:
        # Get discovery system and check if agent exists
        discovery_system = get_agent_discovery_system()
        discovered_agents = discovery_system.get_discovered_agents()
        
        if agent_id not in discovered_agents:
            log_agent_access(agent_id, "schema_request", success=False)
            raise HTTPException(status_code=404, detail={
                "message": f"Agent '{agent_id}' not found in discovered agents",
                "agent_id": agent_id,
                "agent_found": False,
                "suggestion": "Check available agents using GET /agents endpoint"
            })
        
        metadata = discovered_agents[agent_id]
        
        # Try to get the registered instance
        registered_agents = get_registered_agents()
        agent_instance = registered_agents.get(agent_id)
        
        if not agent_instance:
            return {
                "status": "success",
                "message": f"Agent '{agent_id}' found but not currently loaded - schema unavailable",
                "agent_id": agent_id,
                "agent_name": metadata.name,
                "description": metadata.description,
                "agent_found": True,
                "instance_available": False,
                "available_models": [],
                "schemas": {}
            }
        
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
        
        log_agent_access(agent_id, "schema_request")
        return {
            "status": "success",
            "message": f"Schema retrieved for agent: {agent_id}",
            "agent_found": True,
            "instance_available": True,
            **schema_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Agent schema retrieval failed", exception=e, agent_id=agent_id)
        log_agent_access(agent_id, "schema_request", success=False)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent schema: {str(e)}")

@router.get("/config/agents")
async def get_all_agent_configs(user: Dict[str, Any] = Depends(get_current_user)):
    """Get configuration for all agents"""
    logger.info("All agent configs requested", user_id=user["id"])
    
    try:
        config_manager = get_agent_config_manager()
        all_configs = config_manager.get_all_configs()
        
        return {
            "success": True,
            "message": "All agent configurations retrieved",
            "configs": {name: config.to_dict() for name, config in all_configs.items()},
            "total_count": len(all_configs)
        }
        
    except Exception as e:
        logger.error("All agent configs retrieval failed", exception=e, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent configs: {str(e)}")

@router.get("/config/agents/{agent_name}")
async def get_agent_config_endpoint(
    agent_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get configuration for a specific agent"""
    logger.info("Agent config requested", agent_name=agent_name, user_id=user["id"])
    
    try:
        config = get_agent_config(agent_name)
        
        return {
            "success": True,
            "message": f"Configuration retrieved for agent: {agent_name}",
            "agent_name": agent_name,
            "config": config.to_dict()
        }
        
    except Exception as e:
        logger.error("Agent config retrieval failed", exception=e, agent_name=agent_name, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config for {agent_name}: {str(e)}")

@router.put("/config/agents/{agent_name}")
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
            return {
                "success": False,
                "message": "Configuration validation failed",
                "errors": validation_errors
            }
        
        # Apply the updates
        success = config_manager.update_config(agent_name, config_updates)
        
        if success:
            return {
                "success": True,
                "message": f"Configuration updated for agent: {agent_name}",
                "config": config_manager.get_config(agent_name).to_dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
        
    except Exception as e:
        logger.error("Agent config update failed", exception=e, agent_name=agent_name, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to update config for {agent_name}: {str(e)}")

@router.post("/config/agents/{agent_name}/save")
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
            return {
                "success": True,
                "message": f"Configuration saved for agent: {agent_name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
    except Exception as e:
        logger.error("Agent config save failed", exception=e, agent_name=agent_name, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to save config for {agent_name}: {str(e)}")

@router.get("/config/profiles")
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
        
        return {
            "success": True,
            "message": "Available profiles and performance modes retrieved",
            "profiles": profiles
        }
        
    except Exception as e:
        logger.error("Available profiles retrieval failed", exception=e, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to retrieve available profiles: {str(e)}")

@router.post("/config/agents/{agent_name}/profile")
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
            raise HTTPException(status_code=400, detail=f"Invalid profile: {profile}")
        
        if performance_mode and performance_mode not in [m.value for m in AgentPerformanceMode]:
            raise HTTPException(status_code=400, detail=f"Invalid performance mode: {performance_mode}")
        
        # Update config
        updates = {}
        if profile:
            updates["profile"] = profile
        if performance_mode:
            updates["performance_mode"] = performance_mode
        
        success = config_manager.update_config(agent_name, updates)
        
        if success:
            return {
                "success": True,
                "message": f"Profile updated for agent: {agent_name}",
                "config": config_manager.get_config(agent_name).to_dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Agent profile update failed", exception=e, agent_name=agent_name, user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Failed to update profile for {agent_name}: {str(e)}") 