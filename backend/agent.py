"""
Base Agent Module

This module provides the base agent interface and utilities for the AI Agent Platform.
Focused on clean, flexible agent development with unified LLM service integration.
"""

import uuid
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from fastapi import HTTPException
from config.agent import AgentConfig, PerformanceMode, AgentProfile
from models import JobStatus, JobDataBase
from database import DatabaseClient
from logging_system import get_logger

logger = get_logger(__name__)

class AgentError(HTTPException):
    """Base exception for agent-related errors"""
    pass

class AgentNotFoundError(AgentError):
    """Exception for when an agent is not found"""
    def __init__(self, agent_identifier: str, detail: str = None):
        self.agent_identifier = agent_identifier
        detail = detail or f"Agent '{agent_identifier}' not found"
        super().__init__(status_code=404, detail=detail)

class AgentDisabledError(AgentError):
    """Exception for when an agent is disabled"""
    def __init__(self, agent_identifier: str, lifecycle_state: str = None, detail: str = None):
        self.agent_identifier = agent_identifier
        self.lifecycle_state = lifecycle_state
        if not detail:
            if lifecycle_state:
                detail = f"Agent '{agent_identifier}' is {lifecycle_state} and not available for use"
            else:
                detail = f"Agent '{agent_identifier}' is not enabled"
        super().__init__(status_code=400, detail=detail)

class AgentNotLoadedError(AgentError):
    """Exception for when an agent exists but is not loaded"""
    def __init__(self, agent_identifier: str, detail: str = None):
        self.agent_identifier = agent_identifier
        detail = detail or f"Agent '{agent_identifier}' is not currently loaded or available"
        super().__init__(status_code=503, detail=detail)

class AgentExecutionResult:
    """
    Represents the result of an agent job execution.
    """
    
    def __init__(
        self,
        success: bool,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        result_format: Optional[str] = None
    ):
        self.success = success
        self.result = result
        self.error_message = error_message
        self.metadata = metadata or {}
        self.execution_time = execution_time
        self.result_format = result_format

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "result": self.result,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "result_format": self.result_format
        }

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Provides common functionality and enforces implementation of required methods.
    Uses the unified LLM service for provider-agnostic AI access across all supported providers.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        model: Optional[str] = None,
        result_format: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name (required - this is the primary identifier)
            description: Agent description
            model: Model name to use
            result_format: Default result format for this agent
            **kwargs: Additional agent configuration
        """
        self.name = name
        self.description = description
        self.model = model
        self.result_format = result_format
        
        # Create agent configuration
        profile = kwargs.get('profile', AgentProfile.BALANCED)
        performance_mode = kwargs.get('performance_mode', PerformanceMode.BALANCED)
        
        self.agent_config = AgentConfig(
            name=name,
            description=description,
            profile=profile,
            performance_mode=performance_mode,
            result_format=result_format
        )
        
        # Override with any explicit parameters
        if model:
            self.agent_config.model.model_name = model
        if description:
            self.agent_config.description = description
        if result_format:
            self.agent_config.result_format = result_format
        
        # Initialize unified LLM service for provider-agnostic access
        self._llm_service: Optional['UnifiedLLMService'] = None
        
        # Initialize database client
        self._db_client: Optional[DatabaseClient] = None
        
        # Agent state
        self.is_initialized = False
        self.execution_count = 0
        self.last_execution_time: Optional[datetime] = None
        
        logger.info(f"Created {self.__class__.__name__}: {name}", 
                   profile=self.agent_config.profile.value,
                   performance_mode=self.agent_config.performance_mode.value)
    
    async def initialize(self) -> None:
        """Initialize the agent with database connections."""
        if self.is_initialized:
            logger.warning(f"Agent {self.name} is already initialized")
            return
        
        try:
            # Initialize database client
            self._db_client = DatabaseClient()
            
            self.is_initialized = True
            logger.info(f"Successfully initialized agent: {self.name}",
                       timeout=self.agent_config.execution.timeout_seconds)
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.name}: {e}")
            raise
    
    def get_llm_service(self):
        """
        Get the unified LLM service for provider-agnostic AI access.
        
        Returns:
            UnifiedLLMService instance with access to all configured providers
        """
        if self._llm_service is None:
            from services.llm_service import get_unified_llm_service
            self._llm_service = get_unified_llm_service()
        return self._llm_service
    
    @abstractmethod
    def _get_system_instruction(self) -> str:
        """
        Get the system instruction for the agent.
        
        This method must be implemented by subclasses to provide
        specific instructions for their agent type.
        
        Returns:
            System instruction string
        """
        pass
    
    @abstractmethod
    async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
        """
        Execute the specific job logic for this agent type.
        
        This method must be implemented by subclasses to handle
        their specific job types and processing logic.
        
        Args:
            job_data: Job data containing the task information
            
        Returns:
            AgentExecutionResult with the execution outcome
        """
        pass
    
    async def execute_job(
        self,
        job_id: str,
        job_data: JobDataBase,
        user_id: Optional[str] = None
    ) -> AgentExecutionResult:
        """
        Execute a job with comprehensive error handling and monitoring.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data containing the task information
            user_id: Optional user ID for the job
            
        Returns:
            AgentExecutionResult with the execution outcome
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = datetime.now(timezone.utc)
        execution_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting job execution",
            job_id=job_id,
            execution_id=execution_id,
            agent_name=self.name,
            user_id=user_id
        )
        
        try:
            # Update job status to running
            if self._db_client:
                await self._update_job_status(job_id, JobStatus.running)
            
            # Execute job with performance monitoring
            result = await self._execute_job_logic(job_data)
            
            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Update agent state
            self.execution_count += 1
            self.last_execution_time = datetime.now(timezone.utc)
            
            # Update job status based on result
            if self._db_client:
                if result.success:
                    await self._update_job_status(job_id, JobStatus.completed, result.result, result_format=result.result_format)
                else:
                    await self._update_job_status(job_id, JobStatus.failed, error_message=result.error_message)
            
            logger.info(
                f"Job execution completed",
                job_id=job_id,
                execution_id=execution_id,
                success=result.success,
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_message = f"Unexpected error during job execution: {str(e)}"
            
            logger.error(
                error_message,
                job_id=job_id,
                execution_id=execution_id,
                exception=e,
                execution_time=execution_time
            )
            
            # Update job status to failed
            if self._db_client:
                try:
                    await self._update_job_status(job_id, JobStatus.failed, error_message=error_message)
                except Exception as db_error:
                    logger.error(f"Failed to update job status in database: {db_error}")
            
            return AgentExecutionResult(
                success=False,
                error_message=error_message,
                execution_time=execution_time
            )
    
    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        result_format: Optional[str] = None
    ) -> None:
        """
        Update job status in database.
        
        Args:
            job_id: Job identifier
            status: New job status
            result: Job result (if completed successfully)
            error_message: Error message (if failed)
            result_format: Format of the result data
        """
        if not self._db_client:
            logger.warning("Database client not initialized, cannot update job status")
            return
        
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if result is not None:
                update_data["result"] = result
            if error_message is not None:
                update_data["error_message"] = error_message
            if result_format is not None:
                update_data["result_format"] = result_format
            
            await self._db_client.update_job(job_id, update_data)
            logger.debug(f"Updated job {job_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get comprehensive agent information.
        
        Returns:
            Dictionary with agent information
        """
        from config.environment import get_settings
        settings = get_settings()
        
        agent_info = {
            "name": self.name,
            "description": self.description,
            "agent_identifier": self.name,
            "model": self.model,
            "result_format": self.result_format,
            "is_initialized": self.is_initialized,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "config": {
                "profile": self.agent_config.profile.value,
                "performance_mode": self.agent_config.performance_mode.value,
                "timeout_seconds": self.agent_config.execution.timeout_seconds,
                "max_retries": self.agent_config.execution.max_retries,
                "model_name": self.agent_config.model.model_name
            },
            "llm": {
                "default_provider": settings.default_llm_provider,
                "unified_service_available": True
            }
        }
        
        return agent_info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform agent health check.
        
        Returns:
            Health status information
        """
        health_status = {
            "agent_name": self.name,
            "status": "healthy",
            "is_initialized": self.is_initialized,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "checks": {}
        }
        
        # Check database connection
        if self._db_client:
            try:
                db_health = await self._db_client.health_check()
                health_status["checks"]["database"] = "healthy" if db_health else "unhealthy"
            except Exception as e:
                health_status["checks"]["database"] = f"error: {str(e)}"
        else:
            health_status["checks"]["database"] = "not_initialized"
        
        # Check LLM service (unified service that handles all providers)
        try:
            llm_service = self.get_llm_service()
            available_providers = llm_service.get_available_providers()
            if available_providers:
                health_status["checks"]["llm_service"] = {
                    "status": "healthy",
                    "default_provider": llm_service._default_provider,
                    "available_providers": available_providers,
                    "provider_count": len(available_providers)
                }
            else:
                health_status["checks"]["llm_service"] = {
                    "status": "error",
                    "error": "No LLM providers available"
                }
        except Exception as e:
            health_status["checks"]["llm_service"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check for any failed status
        failed_checks = []
        for check_name, check_result in health_status["checks"].items():
            if isinstance(check_result, str) and check_result not in ["healthy", "not_initialized"]:
                failed_checks.append(check_name)
            elif isinstance(check_result, dict) and check_result.get("status") != "healthy":
                failed_checks.append(check_name)
        
        if failed_checks:
            health_status["status"] = "degraded"
            health_status["failed_checks"] = failed_checks
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            if self._db_client:
                await self._db_client.close()
                self._db_client = None
            
            self.is_initialized = False
            logger.info(f"Cleaned up agent: {self.name}")
            
        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', model='{self.model}')>"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.__class__.__name__})"

class AgentRegistry:
    """Registry for managing agent instances"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: Agent instance to register
        """
        if agent.name in self._agents:
            logger.warning(f"Agent {agent.name} is already registered. Overriding.")
        
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def unregister_agent(self, name: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            name: Name of the agent to unregister
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if name in self._agents:
            agent = self._agents.pop(name)
            logger.info(f"Unregistered agent: {name}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent agent: {name}")
            return False
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent instance by name."""
        agent = self._agents.get(name)
        if not agent:
            logger.debug(f"Agent {name} not found in registry")
        return agent
    
    def list_agents(self) -> List[str]:
        """Get list of all registered agent names."""
        return list(self._agents.keys())
    
    def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        return [
            agent for agent in self._agents.values() 
            if agent.__class__.__name__ == agent_type
        ]
    
    async def cleanup_all(self) -> None:
        """Cleanup all registered agents."""
        logger.info("Cleaning up all agents in registry")
        
        cleanup_tasks = []
        for agent in self._agents.values():
            cleanup_tasks.append(agent.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._agents.clear()
        logger.info("All agents cleaned up")

# Global agent registry
_agent_registry = AgentRegistry()

def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    return _agent_registry 