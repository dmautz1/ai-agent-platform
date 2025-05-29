"""
Base Agent Implementation for AI Agent Template

This module provides the base agent class that integrates with Google ADK
and serves as the foundation for specific agent implementations.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from google.adk.agents import Agent
from config.adk import get_adk_config, create_agent
from models import JobType, JobStatus, AgentType, JobData
from database import DatabaseClient
from logging_system import get_logger, get_performance_logger
from config.agent_config import get_agent_config, AgentConfig

# Initialize loggers
logger = get_logger(__name__)
perf_logger = get_performance_logger()


class AgentExecutionResult:
    """Result of agent execution"""
    
    def __init__(
        self,
        success: bool,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ):
        self.success = success
        self.result = result
        self.error_message = error_message
        self.metadata = metadata or {}
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": self.success,
            "result": self.result,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """
    Base agent class that provides common functionality for all AI agents.
    
    This class integrates with Google ADK and provides:
    - Agent lifecycle management
    - Job execution with proper error handling
    - Database integration for job status updates
    - Logging and performance monitoring
    - Configuration management
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        agent_type: AgentType = AgentType.google_adk,
        model: Optional[str] = None,
        tools: Optional[List] = None,
        **kwargs
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's purpose
            agent_type: Type of agent (default: google_adk)
            model: Optional model override
            tools: List of tools/functions available to the agent
            **kwargs: Additional configuration options
        """
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.model = model
        self.tools = tools or []
        self.config = kwargs
        
        # Load agent configuration
        self.agent_config = get_agent_config(name)
        
        # Override with any explicit parameters
        if model:
            self.agent_config.model.model_name = model
        if description:
            self.agent_config.description = description
        
        # Initialize Google ADK agent
        self._adk_agent: Optional[Agent] = None
        self._db_client: Optional[DatabaseClient] = None
        
        # Agent state
        self.is_initialized = False
        self.execution_count = 0
        self.last_execution_time: Optional[datetime] = None
        
        logger.info(f"Created {self.__class__.__name__}: {name}", 
                   profile=self.agent_config.profile.value,
                   performance_mode=self.agent_config.performance_mode.value)
    
    async def initialize(self) -> None:
        """Initialize the agent with Google ADK and database connections."""
        if self.is_initialized:
            logger.warning(f"Agent {self.name} is already initialized")
            return
        
        try:
            # Use configuration for model selection
            model_name = self.agent_config.model.model_name or self.model
            
            # Initialize Google ADK agent
            instruction = self._get_system_instruction()
            self._adk_agent = create_agent(
                name=self.name,
                description=self.agent_config.description or self.description,
                instruction=instruction,
                tools=self.tools,
                model=model_name
            )
            
            # Initialize database client
            self._db_client = DatabaseClient()
            
            self.is_initialized = True
            logger.info(f"Successfully initialized agent: {self.name}",
                       model=model_name,
                       timeout=self.agent_config.execution.timeout_seconds)
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.name}: {e}")
            raise
    
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
    async def _execute_job_logic(self, job_data: JobData) -> AgentExecutionResult:
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
    
    def _validate_job_data(self, job_data: JobData) -> bool:
        """
        Validate that the job data is appropriate for this agent.
        
        Args:
            job_data: Job data to validate
            
        Returns:
            True if valid, False otherwise
        """
        supported_types = self.get_supported_job_types()
        return job_data.job_type in supported_types
    
    @abstractmethod
    def get_supported_job_types(self) -> List[JobType]:
        """
        Get the list of job types supported by this agent.
        
        Returns:
            List of supported JobType values
        """
        pass
    
    async def execute_job(
        self,
        job_id: str,
        job_data: JobData,
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
        
        # Validate job data
        if not self._validate_job_data(job_data):
            error_msg = f"Job type {job_data.job_type} not supported by {self.__class__.__name__}"
            logger.error(error_msg, job_id=job_id)
            return AgentExecutionResult(
                success=False,
                error_message=error_msg
            )
        
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting job execution",
            job_id=job_id,
            execution_id=execution_id,
            agent_name=self.name,
            job_type=job_data.job_type.value,
            user_id=user_id
        )
        
        try:
            # Update job status to running
            if self._db_client:
                await self._update_job_status(job_id, JobStatus.running)
            
            # Execute job with performance monitoring
            with perf_logger.time_operation(f"agent_execution_{self.name}", job_id=job_id):
                result = await self._execute_job_logic(job_data)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Update agent state
            self.execution_count += 1
            self.last_execution_time = datetime.utcnow()
            
            # Update job status based on result
            if self._db_client:
                if result.success:
                    await self._update_job_status(job_id, JobStatus.completed, result.result)
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
            execution_time = (datetime.utcnow() - start_time).total_seconds()
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
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job status in the database.
        
        Args:
            job_id: Job identifier
            status: New job status
            result: Optional result data
            error_message: Optional error message
        """
        if not self._db_client:
            logger.warning("Database client not initialized, cannot update job status")
            return
        
        try:
            update_data = {"status": status.value, "updated_at": datetime.utcnow().isoformat()}
            
            if result is not None:
                update_data["result"] = result
            
            if error_message is not None:
                update_data["error_message"] = error_message
            
            await self._db_client.update_job(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}", job_id=job_id, status=status.value)
            raise
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dictionary containing agent information including configuration
        """
        return {
            "name": self.name,
            "description": self.agent_config.description or self.description,
            "agent_type": self.agent_type.value,
            "model": self.agent_config.model.model_name or self.model,
            "supported_job_types": [jt.value for jt in self.get_supported_job_types()],
            "is_initialized": self.is_initialized,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "tools_count": len(self.tools),
            "configuration": {
                "profile": self.agent_config.profile.value,
                "performance_mode": self.agent_config.performance_mode.value,
                "enabled": self.agent_config.enabled,
                "timeout_seconds": self.agent_config.execution.timeout_seconds,
                "max_retries": self.agent_config.execution.max_retries,
                "enable_caching": self.agent_config.execution.enable_caching,
                "temperature": self.agent_config.model.temperature,
                "max_tokens": self.agent_config.model.max_tokens,
                "log_level": self.agent_config.logging.log_level,
                "rate_limit_per_minute": self.agent_config.security.rate_limit_per_minute
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the agent.
        
        Returns:
            Dictionary containing health status
        """
        health_status = {
            "healthy": True,
            "agent_name": self.name,
            "is_initialized": self.is_initialized,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "execution_count": self.execution_count,
            "checks": {}
        }
        
        # Check Google ADK agent
        try:
            if self._adk_agent:
                health_status["checks"]["adk_agent"] = "healthy"
            else:
                health_status["checks"]["adk_agent"] = "not_initialized"
                health_status["healthy"] = False
        except Exception as e:
            health_status["checks"]["adk_agent"] = f"error: {str(e)}"
            health_status["healthy"] = False
        
        # Check database connection
        try:
            if self._db_client:
                # Test database connectivity
                await self._db_client.test_connection()
                health_status["checks"]["database"] = "healthy"
            else:
                health_status["checks"]["database"] = "not_initialized"
                health_status["healthy"] = False
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["healthy"] = False
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        logger.info(f"Cleaning up agent: {self.name}")
        
        # Close database connection if exists
        if self._db_client:
            try:
                await self._db_client.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        
        self.is_initialized = False
        logger.info(f"Agent cleanup completed: {self.name}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.agent_type.value}')"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.__class__.__name__})"


class AgentRegistry:
    """Registry to manage multiple agent instances"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_types: Dict[JobType, List[str]] = {}
        logger.info("Initialized AgentRegistry")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: Agent instance to register
        """
        if agent.name in self._agents:
            logger.warning(f"Agent {agent.name} is already registered, overwriting")
        
        self._agents[agent.name] = agent
        
        # Update job type mappings
        for job_type in agent.get_supported_job_types():
            if job_type not in self._agent_types:
                self._agent_types[job_type] = []
            if agent.name not in self._agent_types[job_type]:
                self._agent_types[job_type].append(agent.name)
        
        logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)
    
    def get_agents_for_job_type(self, job_type: JobType) -> List[BaseAgent]:
        """
        Get all agents that support a specific job type.
        
        Args:
            job_type: Job type to search for
            
        Returns:
            List of agent instances supporting the job type
        """
        agent_names = self._agent_types.get(job_type, [])
        return [self._agents[name] for name in agent_names if name in self._agents]
    
    def list_agents(self) -> List[str]:
        """Get list of all registered agent names."""
        return list(self._agents.keys())
    
    async def cleanup_all(self) -> None:
        """Cleanup all registered agents."""
        logger.info("Cleaning up all agents in registry")
        
        for agent in self._agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent.name}: {e}")
        
        self._agents.clear()
        self._agent_types.clear()
        logger.info("Agent registry cleanup completed")


# Global agent registry instance
agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    return agent_registry 