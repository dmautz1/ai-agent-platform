"""
Agent Auto-Discovery System

This module automatically discovers and registers all agents in the agents/ directory.
Agents just need to inherit from SelfContainedAgent and they will be automatically
discovered and registered when the application starts.
"""

import importlib
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from logging_system import get_logger

logger = get_logger(__name__)

def discover_and_register_agents(agent_registry) -> Dict[str, Any]:
    """
    Automatically discover and register all agents in the agents/ directory.
    
    Returns:
        Dict with discovery statistics and any errors
    """
    agents_dir = Path(__file__).parent
    discovered_agents = []
    registration_errors = []
    
    logger.info("Starting agent auto-discovery process")
    
    # Find all *_agent.py files
    agent_files = list(agents_dir.glob("*_agent.py"))
    logger.info(f"Found {len(agent_files)} potential agent files")
    
    for agent_file in agent_files:
        module_name = agent_file.stem
        
        try:
            # Import the agent module
            full_module_name = f"agents.{module_name}"
            
            # Ensure the module path is in sys.path
            if str(agents_dir.parent) not in sys.path:
                sys.path.insert(0, str(agents_dir.parent))
            
            logger.debug(f"Importing module: {full_module_name}")
            module = importlib.import_module(full_module_name)
            
            # Find agent classes in the module
            agent_classes_found = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a class that inherits from SelfContainedAgent
                if (isinstance(attr, type) and 
                    hasattr(attr, '__mro__') and 
                    any('SelfContainedAgent' in str(cls) for cls in attr.__mro__) and
                    attr.__name__ != 'SelfContainedAgent'):
                    
                    agent_classes_found.append(attr)
            
            # Register each agent class found
            for agent_class in agent_classes_found:
                try:
                    # Create agent instance
                    agent_instance = agent_class()
                    
                    # Register with the agent registry
                    agent_registry.register_agent(agent_instance)
                    
                    discovered_agents.append({
                        'name': agent_instance.name,
                        'class': agent_class.__name__,
                        'module': full_module_name,
                        'endpoints': len(agent_class.get_endpoints()),
                        'models': len(agent_class.get_models())
                    })
                    
                    logger.info(f"Auto-registered agent: {agent_instance.name} "
                               f"({agent_class.__name__}) with {len(agent_class.get_endpoints())} endpoints")
                    
                except Exception as e:
                    error_msg = f"Failed to instantiate/register {agent_class.__name__}: {str(e)}"
                    registration_errors.append(error_msg)
                    logger.error(error_msg, exception=e)
            
            if not agent_classes_found:
                logger.warning(f"No agent classes found in {module_name}")
                
        except Exception as e:
            error_msg = f"Failed to load agent module {module_name}: {str(e)}"
            registration_errors.append(error_msg)
            logger.error(error_msg, exception=e)
    
    logger.info(f"Agent auto-discovery completed: {len(discovered_agents)} agents registered, "
               f"{len(registration_errors)} errors")
    
    return {
        'discovered_agents': discovered_agents,
        'total_registered': len(discovered_agents),
        'total_errors': len(registration_errors),
        'errors': registration_errors,
        'agent_files_found': len(agent_files)
    }

def get_discovery_status() -> Dict[str, Any]:
    """Get the current status of agent discovery"""
    from agent_framework import get_registered_agents, get_agent_endpoints, get_agent_models
    
    registered_agents = get_registered_agents()
    endpoint_classes = get_agent_endpoints()
    agent_models = get_agent_models()
    
    status = {
        'total_agents': len(registered_agents),
        'total_endpoint_classes': len(endpoint_classes),
        'total_models': sum(len(models) for models in agent_models.values()),
        'agents': {}
    }
    
    for agent_name, agent_instance in registered_agents.items():
        agent_class = agent_instance.__class__
        status['agents'][agent_name] = {
            'class_name': agent_class.__name__,
            'endpoints': len(agent_class.get_endpoints()) if hasattr(agent_class, 'get_endpoints') else 0,
            'models': len(agent_class.get_models()) if hasattr(agent_class, 'get_models') else 0,
            'status': 'registered'
        }
    
    return status

def reload_agents(agent_registry):
    """
    Reload all agents (useful for development).
    Warning: This will clear the current registry and re-discover all agents.
    """
    logger.warning("Reloading all agents - this will clear the current registry")
    
    # Clear current registrations
    from agent_framework import _agent_endpoints, _agent_models, _registered_agents
    _agent_endpoints.clear()
    _agent_models.clear()
    _registered_agents.clear()
    
    # Clear agent registry
    for agent_name in list(agent_registry._agents.keys()):
        agent_registry.unregister_agent(agent_name)
    
    # Re-discover and register
    return discover_and_register_agents(agent_registry) 