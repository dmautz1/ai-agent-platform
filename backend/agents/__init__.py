"""
Agent Auto-Discovery System

This module automatically discovers and registers all agents in the agents/ directory.
Agents just need to inherit from SelfContainedAgent and they will be automatically
discovered and registered when the application starts.

Updated to work with the new genericized agent framework.
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
    
    This function works with the new genericized framework where agents
    are discovered based on their class definitions rather than hardcoded types.
    
    Returns:
        Dict with discovery statistics and any errors
    """
    agents_dir = Path(__file__).parent
    discovered_agents = []
    registration_errors = []
    
    logger.info("Starting agent auto-discovery process")
    
    # Find all *_agent.py files in the directory
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
                    # Skip agents that don't have explicit names in their constructor
                    # We'll handle agent instantiation elsewhere with proper names
                    
                    # Get endpoint and model information safely
                    try:
                        endpoints_count = len(agent_class.get_endpoints()) if hasattr(agent_class, 'get_endpoints') else 0
                    except:
                        endpoints_count = 0
                    
                    discovered_agents.append({
                        'class': agent_class.__name__,
                        'module': full_module_name,
                        'endpoints': endpoints_count,
                        'version': getattr(agent_class, '_version', '1.0.0'),
                        'status': 'discovered_class_only'
                    })
                    
                    logger.info(f"Discovered agent class: {agent_class.__name__} "
                               f"with {endpoints_count} endpoints")
                    
                except Exception as e:
                    error_msg = f"Failed to process {agent_class.__name__}: {str(e)}"
                    registration_errors.append(error_msg)
                    logger.error(error_msg, exception=e)
            
            if not agent_classes_found:
                logger.debug(f"No agent classes found in {module_name}")
                
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
    try:
        from agent_framework import get_registered_agents, get_agent_endpoints, get_agent_models
        
        registered_agents = get_registered_agents()
        agent_models = get_agent_models()
        
        status = {
            'total_agents': len(registered_agents),
            'total_models': sum(len(models) for models in agent_models.values()),
            'agents': {}
        }
        
        for agent_name, agent_instance in registered_agents.items():
            agent_class = agent_instance.__class__
            
            # Safely get endpoint and model counts
            try:
                endpoints_count = len(agent_class.get_endpoints()) if hasattr(agent_class, 'get_endpoints') else 0
                models_count = len(agent_class.get_models()) if hasattr(agent_class, 'get_models') else 0
            except:
                endpoints_count = 0
                models_count = 0
            
            status['agents'][agent_name] = {
                'class_name': agent_class.__name__,
                'endpoints': endpoints_count,
                'models': models_count,
                'version': getattr(agent_class, '_version', '1.0.0'),
                'status': 'registered'
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get discovery status: {e}")
        return {
            'total_agents': 0,
            'total_models': 0,
            'agents': {},
            'error': str(e)
        }

def reload_agents(agent_registry):
    """
    Reload all agents (useful for development).
    Warning: This will clear the current registry and re-discover all agents.
    """
    logger.warning("Reloading all agents - this will clear the current registry")
    
    try:
        # Clear current registrations
        from agent_framework import _agent_endpoints, _agent_models, _registered_agents
        _agent_endpoints.clear()
        _agent_models.clear()
        _registered_agents.clear()
        
        # Clear agent registry
        for agent_name in list(agent_registry._agents.keys()):
            agent_registry.unregister_agent(agent_name)
        
        # Re-discover and instantiate agents
        discovery_result = discover_and_register_agents(agent_registry)
        instantiation_result = instantiate_and_register_agents(agent_registry)
        
        return {
            'discovery': discovery_result,
            'instantiation': instantiation_result,
            'total_registered': instantiation_result['total_instantiated']
        }
        
    except Exception as e:
        logger.error(f"Failed to reload agents: {e}")
        return {
            'discovery': {'discovered_agents': [], 'total_registered': 0, 'total_errors': 1, 'errors': [str(e)]},
            'instantiation': {'instantiated_agents': [], 'total_instantiated': 0, 'total_errors': 1, 'errors': [str(e)]},
            'total_registered': 0
        }

def instantiate_and_register_agents(agent_registry) -> Dict[str, Any]:
    """
    Instantiate and register agents with their explicit names.
    This should be called after discover_and_register_agents.
    
    Returns:
        Dict with instantiation statistics and any errors
    """
    instantiated_agents = []
    instantiation_errors = []
    
    logger.info("Starting agent instantiation and registration")
    
    # We need to instantiate agents with their explicit names
    # This requires importing and checking each agent module for the proper instantiation
    
    try:
        # Import specific agents and instantiate them with their defined names
        from agents.simple_prompt_agent import SimplePromptAgent
        simple_agent = SimplePromptAgent()
        agent_registry.register_agent(simple_agent)
        instantiated_agents.append({
            'name': simple_agent.name,
            'class': simple_agent.__class__.__name__,
            'status': 'registered'
        })
        logger.info(f"Instantiated and registered: {simple_agent.name}")
        
    except Exception as e:
        error_msg = f"Failed to instantiate SimplePromptAgent: {str(e)}"
        instantiation_errors.append(error_msg)
        logger.error(error_msg)
    
    try:
        from agents.web_scraping_agent import WebScrapingAgent
        web_agent = WebScrapingAgent()
        agent_registry.register_agent(web_agent)
        instantiated_agents.append({
            'name': web_agent.name,
            'class': web_agent.__class__.__name__,
            'status': 'registered'
        })
        logger.info(f"Instantiated and registered: {web_agent.name}")
        
    except Exception as e:
        error_msg = f"Failed to instantiate WebScrapingAgent: {str(e)}"
        instantiation_errors.append(error_msg)
        logger.error(error_msg)
    
    logger.info(f"Agent instantiation completed: {len(instantiated_agents)} agents registered, "
               f"{len(instantiation_errors)} errors")
    
    return {
        'instantiated_agents': instantiated_agents,
        'total_instantiated': len(instantiated_agents),
        'total_errors': len(instantiation_errors),
        'errors': instantiation_errors
    } 