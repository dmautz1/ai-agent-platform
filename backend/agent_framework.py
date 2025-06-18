"""
Agent Framework - Self-contained agent system with automatic registration

This framework allows agents to be completely self-contained with:
- Embedded job data models using @job_model decorator
- Embedded API endpoints using @endpoint decorator  
- Automatic agent discovery and registration
- Automatic endpoint registration with FastAPI
- Built-in authentication and error handling
- Clean service-based architecture
"""

import inspect
import json
from typing import Dict, List, Any, Optional, Callable, Type, get_type_hints
from functools import wraps
from abc import ABCMeta
from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel

from agent import BaseAgent, AgentExecutionResult
from auth import get_current_user
from logging_system import get_logger

logger = get_logger(__name__)

# Global registry for agent endpoints and models
_agent_endpoints = {}
_agent_models = {}
_registered_agents = {}

def job_model(cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    Decorator to register a model as a job data model for an agent.
    
    The model will be registered when the agent instance is created.
    
    Args:
        cls: The Pydantic model class to register
        
    Returns:
        The same model class (unchanged)
    """
    # Mark the class as a job model for later registration
    cls._is_job_model = True
    
    return cls

def endpoint(path: str, methods: List[str] = ["POST"], auth_required: bool = True, public: bool = False):
    """
    Decorator to register an endpoint for an agent.
    
    Usage:
        @endpoint("/my-agent/process", methods=["POST"], auth_required=True)
        async def process_data(self, request_data: dict, user: dict):
            return {"result": "processed"}
    """
    def decorator(func: Callable) -> Callable:
        # Store endpoint metadata on the function
        func._endpoint_info = {
            'path': path,
            'methods': methods,
            'auth_required': auth_required,
            'public': public,
            'function_name': func.__name__
        }
        logger.debug(f"Registered endpoint {path} for function {func.__name__}")
        return func
    return decorator

class AgentMeta(ABCMeta):
    """Metaclass to collect agent endpoints and models"""
    
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Only process classes that inherit from SelfContainedAgent
        if name != 'SelfContainedAgent' and any(
            hasattr(base, '__name__') and 'SelfContainedAgent' in base.__name__ 
            for base in bases
        ):
            # Store the agent class for later registration when instances are created
            logger.debug(f"Discovered agent class: {name}")
        
        return cls

class SelfContainedAgent(BaseAgent, metaclass=AgentMeta):
    """
    Base class for self-contained agents with automatic endpoint registration and LLM-agnostic AI access.
    
    Agents extending this class can define their own:
    - Job data models using @job_model decorator
    - API endpoints using @endpoint decorator
    - All business logic in the same file
    - Agents can use any AI provider via the unified LLM service
    """
    
    def __init__(self, name: str, description: str = None, **kwargs):
        if description is None:
            description = f"{name.title()} agent - self-contained agent with embedded endpoints"
        
        super().__init__(name=name, description=description, **kwargs)
        
        # Register this instance using the explicit name
        _registered_agents[self.name] = self
        _agent_endpoints[self.name] = self.__class__
        
        # Register job models defined in the same module
        self._register_job_models()
    
    def _register_job_models(self):
        """Register job models defined in the same module as this agent"""
        import sys
        import inspect
        
        # Get the module where this agent class is defined
        agent_module = sys.modules[self.__class__.__module__]
        
        # Initialize models dict for this agent if not exists
        if self.name not in _agent_models:
            _agent_models[self.name] = {}
        
        # Find all job models in the module
        for attr_name in dir(agent_module):
            attr = getattr(agent_module, attr_name)
            
            # Check if it's a job model
            if (isinstance(attr, type) and 
                issubclass(attr, BaseModel) and 
                hasattr(attr, '_is_job_model')):
                
                _agent_models[self.name][attr.__name__] = attr
                logger.debug(f"Registered job model {attr.__name__} for agent {self.name}")
        
        # Also look in the calling frame's locals (for test cases)
        try:
            frame = inspect.currentframe()
            # Go up the call stack to find job models
            for _ in range(5):  # Look up to 5 frames up
                frame = frame.f_back
                if frame is None:
                    break
                
                # Check locals and globals in this frame
                for name, obj in {**frame.f_locals, **frame.f_globals}.items():
                    if (isinstance(obj, type) and 
                        issubclass(obj, BaseModel) and 
                        hasattr(obj, '_is_job_model') and
                        obj.__name__ not in _agent_models[self.name]):
                        
                        _agent_models[self.name][obj.__name__] = obj
                        logger.debug(f"Registered job model {obj.__name__} for agent {self.name} (from frame)")
        except Exception as e:
            # If frame inspection fails, just continue
            logger.debug(f"Frame inspection failed: {e}")
        finally:
            # Clean up frame reference
            del frame
    
    @classmethod
    def get_endpoints(cls) -> List[Dict[str, Any]]:
        """Get all endpoints defined for this agent"""
        endpoints = []
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, '_endpoint_info'):
                endpoint_info = attr._endpoint_info.copy()
                endpoint_info['method_name'] = attr_name
                endpoint_info['method'] = attr
                endpoints.append(endpoint_info)
        return endpoints
    
    @classmethod
    def get_models(cls) -> Dict[str, Type[BaseModel]]:
        """Get all models defined for this agent"""
        # Find the agent instance to get its explicit name
        for agent_name, agent_instance in _registered_agents.items():
            if isinstance(agent_instance, cls):
                return _agent_models.get(agent_name, {})
        
        # Fallback: return empty dict if no models found
        return {}
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Extended agent info including endpoints and models"""
        base_info = await super().get_agent_info()
        base_info.update({
            'endpoints': [
                {
                    'path': ep['path'],
                    'methods': ep['methods'],
                    'auth_required': ep['auth_required'],
                    'public': ep['public']
                }
                for ep in self.get_endpoints()
            ],
            'models': list(self.get_models().keys()),
            'framework_version': '1.0',
            'self_contained': True,
        })
        return base_info

def create_endpoint_wrapper(agent_instance: SelfContainedAgent, method: Callable, endpoint_info: Dict[str, Any]):
    """Create a FastAPI endpoint wrapper for an agent method"""
    
    @wraps(method)
    async def wrapper(request: Request, request_data: dict = None, user: dict = None):
        agent_name = agent_instance.name
        operation_name = f"{agent_name}_{method.__name__}"
        
        try:
                logger.info(f"Executing {operation_name}", 
                           user_id=user.get('id') if user else None,
                           endpoint=endpoint_info['path'])
                
                # Get method signature to determine what parameters to pass
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())[1:]  # Skip 'self'
                
                # Prepare arguments based on method signature
                args = []
                kwargs = {}
                
                for param_name in params:
                    if param_name == 'request_data' and request_data is not None:
                        args.append(request_data)
                    elif param_name == 'user' and user is not None:
                        args.append(user)
                    elif param_name == 'request':
                        args.append(request)
                
                # Execute the method
                if inspect.iscoroutinefunction(method):
                    result = await method(agent_instance, *args, **kwargs)
                else:
                    result = method(agent_instance, *args, **kwargs)
                
                logger.info(f"Successfully executed {operation_name}",
                           user_id=user.get('id') if user else None)
                
                return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Endpoint {endpoint_info['path']} failed", 
                        exception=e, agent=agent_name,
                        user_id=user.get('id') if user else None)
            raise HTTPException(
                status_code=500, 
                detail=f"Agent operation failed: {str(e)}"
            )
    
    return wrapper

def register_agent_endpoints(app, agent_registry):
    """Automatically register all agent endpoints with FastAPI"""
    
    registered_count = 0
    
    for agent_name, agent_instance in _registered_agents.items():        
        # Register each endpoint
        agent_class = agent_instance.__class__
        endpoints = agent_class.get_endpoints()
        
        for endpoint_info in endpoints:
            path = endpoint_info['path']
            methods = endpoint_info['methods']
            auth_required = endpoint_info['auth_required']
            method = endpoint_info['method']
            
            # Create the wrapper
            wrapper = create_endpoint_wrapper(agent_instance, method, endpoint_info)
            
            # Prepare dependencies
            dependencies = []
            if auth_required:
                dependencies = [Depends(get_current_user)]
            
            # Determine if we need request_data parameter
            sig = inspect.signature(method)
            needs_request_data = 'request_data' in sig.parameters
            
            # Create the final endpoint function
            if auth_required and needs_request_data:
                async def final_endpoint(request_data: dict, user: dict = Depends(get_current_user)):
                    return await wrapper(None, request_data, user)
            elif auth_required and not needs_request_data:
                async def final_endpoint(user: dict = Depends(get_current_user)):
                    return await wrapper(None, None, user)
            elif not auth_required and needs_request_data:
                async def final_endpoint(request_data: dict):
                    return await wrapper(None, request_data, None)
            else:
                async def final_endpoint():
                    return await wrapper(None, None, None)
            
            # Update the wrapper name for better error messages
            final_endpoint.__name__ = f"{agent_name}_{method.__name__}_endpoint"
            
            # Register with FastAPI
            for http_method in methods:
                app.add_api_route(
                    path=path,
                    endpoint=final_endpoint,
                    methods=[http_method.upper()],
                    tags=[f"{agent_name}-agent"],
                    summary=f"{agent_name.title()} Agent - {method.__name__.replace('_', ' ').title()}",
                    description=method.__doc__ or f"{method.__name__} operation for {agent_name} agent"
                )
                registered_count += 1
            
            logger.info(f"Registered {methods} {path} for {agent_name} agent")
    
    logger.info(f"Registered {registered_count} endpoints total")
    return registered_count

def get_all_agent_info() -> Dict[str, Any]:
    """Get information about all registered agents"""
    info = {}
    for agent_name, agent_class in _agent_endpoints.items():
        info[agent_name] = {
            'class': agent_class.__name__,
            'endpoints': [
                {
                    'path': ep['path'],
                    'methods': ep['methods'],
                    'auth_required': ep['auth_required'],
                    'public': ep['public']
                }
                for ep in agent_class.get_endpoints()
            ],
            'models': list(agent_class.get_models().keys())
        }
    return info

# Utility functions for job execution
async def execute_agent_job(agent_instance: SelfContainedAgent, job_data: BaseModel, user_id: str) -> Dict[str, Any]:
    """Execute a job using the agent's execute_job method and format response"""
    import uuid
    
    job_id = str(uuid.uuid4())
    result = await agent_instance.execute_job(job_id, job_data, user_id)
    
    if result.success:
        logger.info(f"Job {job_id} completed successfully", 
                   agent=agent_instance.name, user_id=user_id)
        return {
            "status": "success",
            "job_id": job_id,
            "result": result.result,
            "metadata": result.metadata,
            "execution_time": result.execution_time
        }
    else:
        logger.warning(f"Job {job_id} failed", 
                      agent=agent_instance.name, user_id=user_id, 
                      error=result.error_message)
        return {
            "status": "error",
            "job_id": job_id,
            "message": "Job execution failed",
            "error": result.error_message,
            "execution_time": result.execution_time
        }

def validate_job_data(data: Dict[str, Any], model_class: Type[BaseModel]) -> BaseModel:
    """Validate job data against a Pydantic model"""
    try:
        return model_class(**data)
    except Exception as e:
        logger.error(f"Job data validation failed", error=str(e), data_keys=list(data.keys()))
        raise HTTPException(status_code=400, detail=f"Invalid job data: {str(e)}")

def get_registered_agents() -> Dict[str, SelfContainedAgent]:
    """Get all registered agent instances"""
    return _registered_agents.copy()

def get_agent_models() -> Dict[str, Dict[str, Type[BaseModel]]]:
    """Get all registered agent models"""
    return _agent_models.copy()

def get_agent_endpoints() -> Dict[str, Type[SelfContainedAgent]]:
    """Get all registered agent endpoint classes"""
    return _agent_endpoints.copy() 