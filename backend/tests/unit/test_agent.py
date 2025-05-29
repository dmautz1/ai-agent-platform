"""
Unit tests for base agent functionality.

Tests cover agent initialization, job execution, registry management,
error handling, and integration with Google ADK and database.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agent import (
    BaseAgent, AgentExecutionResult, AgentRegistry,
    get_agent_registry
)
from models import JobType, JobStatus, AgentType, TextProcessingJobData


class TestAgentExecutionResult:
    """Test cases for AgentExecutionResult class."""
    
    def test_successful_result_creation(self):
        """Test creating a successful execution result."""
        result = AgentExecutionResult(
            success=True,
            result="Task completed successfully",
            metadata={"processed_items": 5},
            execution_time=1.5
        )
        
        assert result.success is True
        assert result.result == "Task completed successfully"
        assert result.metadata == {"processed_items": 5}
        assert result.execution_time == 1.5
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)
    
    def test_failed_result_creation(self):
        """Test creating a failed execution result."""
        result = AgentExecutionResult(
            success=False,
            error_message="Task failed due to invalid input"
        )
        
        assert result.success is False
        assert result.error_message == "Task failed due to invalid input"
        assert result.result is None
        assert result.metadata == {}
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = AgentExecutionResult(
            success=True,
            result="Success",
            execution_time=2.0
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["result"] == "Success"
        assert result_dict["execution_time"] == 2.0
        assert "timestamp" in result_dict


class MockAgent(BaseAgent):
    """Mock agent implementation for testing."""
    
    def __init__(self, name: str = "test_agent", fail_execution: bool = False, **kwargs):
        super().__init__(
            name=name,
            description="Test agent for unit testing",
            **kwargs
        )
        self.fail_execution = fail_execution
    
    def _get_system_instruction(self) -> str:
        return "You are a test agent for unit testing purposes."
    
    def get_supported_job_types(self) -> list:
        return [JobType.text_processing]
    
    async def _execute_job_logic(self, job_data) -> AgentExecutionResult:
        if self.fail_execution:
            return AgentExecutionResult(
                success=False,
                error_message="Mock execution failure"
            )
        
        return AgentExecutionResult(
            success=True,
            result=f"Processed: {job_data.text if hasattr(job_data, 'text') else 'test data'}",
            metadata={"job_type": job_data.job_type.value}
        )


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = MockAgent()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.name == "test_agent"
        assert self.agent.description == "Test agent for unit testing"
        assert self.agent.agent_type == AgentType.google_adk
        assert not self.agent.is_initialized
        assert self.agent.execution_count == 0
        assert self.agent.last_execution_time is None
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_agent_initialize_success(self, mock_db_client, mock_create_agent):
        """Test successful agent initialization."""
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = MagicMock()
        mock_db_client.return_value = mock_db_instance
        
        await self.agent.initialize()
        
        assert self.agent.is_initialized
        mock_create_agent.assert_called_once()
        mock_db_client.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    async def test_agent_initialize_failure(self, mock_create_agent):
        """Test agent initialization failure."""
        mock_create_agent.side_effect = Exception("ADK initialization failed")
        
        with pytest.raises(Exception) as exc_info:
            await self.agent.initialize()
        
        assert "ADK initialization failed" in str(exc_info.value)
        assert not self.agent.is_initialized
    
    @pytest.mark.asyncio
    async def test_agent_double_initialization(self):
        """Test that double initialization is handled gracefully."""
        with patch('agent.create_agent') as mock_create_agent:
            with patch('agent.DatabaseClient') as mock_db_client:
                mock_create_agent.return_value = MagicMock()
                mock_db_client.return_value = MagicMock()
                
                await self.agent.initialize()
                await self.agent.initialize()  # Second call
                
                # Should only be called once
                mock_create_agent.assert_called_once()
                mock_db_client.assert_called_once()
    
    def test_job_data_validation(self):
        """Test job data validation."""
        # Valid job data
        valid_job_data = TextProcessingJobData(
            text="Test text",
            operation="analyze"
        )
        assert self.agent._validate_job_data(valid_job_data)
        
        # Invalid job data (unsupported job type)
        invalid_job_data = MagicMock()
        invalid_job_data.job_type = JobType.web_scraping
        assert not self.agent._validate_job_data(invalid_job_data)
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_successful_job_execution(self, mock_db_client, mock_create_agent):
        """Test successful job execution."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Initialize agent
        await self.agent.initialize()
        
        # Create job data
        job_data = TextProcessingJobData(
            text="Test text for processing",
            operation="analyze"
        )
        
        # Execute job
        result = await self.agent.execute_job("test-job-id", job_data, "test-user-id")
        
        # Verify result
        assert result.success
        assert "Processed: Test text for processing" in result.result
        assert result.execution_time is not None
        assert self.agent.execution_count == 1
        assert self.agent.last_execution_time is not None
        
        # Verify database calls
        assert mock_db_instance.update_job.call_count == 2  # running, then completed
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_failed_job_execution(self, mock_db_client, mock_create_agent):
        """Test failed job execution."""
        # Create agent that fails execution
        agent = MockAgent(fail_execution=True)
        
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Initialize agent
        await agent.initialize()
        
        # Create job data
        job_data = TextProcessingJobData(
            text="Test text",
            operation="analyze"
        )
        
        # Execute job
        result = await agent.execute_job("test-job-id", job_data)
        
        # Verify result
        assert not result.success
        assert result.error_message == "Mock execution failure"
        assert result.execution_time is not None
        
        # Verify database calls
        assert mock_db_instance.update_job.call_count == 2  # running, then failed
    
    @pytest.mark.asyncio
    async def test_invalid_job_type_execution(self):
        """Test execution with invalid job type."""
        # Create job data with unsupported type
        invalid_job_data = MagicMock()
        invalid_job_data.job_type = JobType.web_scraping
        
        result = await self.agent.execute_job("test-job-id", invalid_job_data)
        
        assert not result.success
        assert "not supported by MockAgent" in result.error_message
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_job_execution_exception_handling(self, mock_db_client, mock_create_agent):
        """Test job execution with unexpected exception."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Make execute_job_logic raise an exception
        agent = MockAgent()
        await agent.initialize()
        
        with patch.object(agent, '_execute_job_logic', side_effect=Exception("Unexpected error")):
            job_data = TextProcessingJobData(text="Test", operation="analyze")
            result = await agent.execute_job("test-job-id", job_data)
            
            assert not result.success
            assert "Unexpected error during job execution" in result.error_message
            assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_get_agent_info(self):
        """Test getting agent information."""
        info = await self.agent.get_agent_info()
        
        assert info["name"] == "test_agent"
        assert info["description"] == "Test agent for unit testing"
        assert info["agent_type"] == "google_adk"
        assert info["supported_job_types"] == ["text_processing"]
        assert info["is_initialized"] is False
        assert info["execution_count"] == 0
        assert info["last_execution_time"] is None
        assert info["tools_count"] == 0
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_health_check_healthy(self, mock_db_client, mock_create_agent):
        """Test health check for healthy agent."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_instance.test_connection = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        await self.agent.initialize()
        
        health = await self.agent.health_check()
        
        assert health["healthy"] is True
        assert health["agent_name"] == "test_agent"
        assert health["checks"]["adk_agent"] == "healthy"
        assert health["checks"]["database"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check for unhealthy agent."""
        health = await self.agent.health_check()
        
        assert health["healthy"] is False
        assert health["checks"]["adk_agent"] == "not_initialized"
        assert health["checks"]["database"] == "not_initialized"
    
    @pytest.mark.asyncio
    @patch('agent.create_agent')
    @patch('agent.DatabaseClient')
    async def test_agent_cleanup(self, mock_db_client, mock_create_agent):
        """Test agent cleanup."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        await self.agent.initialize()
        assert self.agent.is_initialized
        
        await self.agent.cleanup()
        
        assert not self.agent.is_initialized
        mock_db_instance.close.assert_called_once()
    
    def test_agent_string_representations(self):
        """Test agent string representations."""
        assert "test_agent" in str(self.agent)
        assert "MockAgent" in repr(self.agent)
        assert "google_adk" in repr(self.agent)


class TestAgentRegistry:
    """Test cases for AgentRegistry class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.registry = AgentRegistry()
        self.agent1 = MockAgent(name="agent1")
        self.agent2 = MockAgent(name="agent2")
    
    def test_register_agent(self):
        """Test registering an agent."""
        self.registry.register_agent(self.agent1)
        
        assert "agent1" in self.registry.list_agents()
        assert self.registry.get_agent("agent1") == self.agent1
    
    def test_register_duplicate_agent(self):
        """Test registering an agent with duplicate name."""
        self.registry.register_agent(self.agent1)
        
        # Register another agent with same name
        duplicate_agent = MockAgent(name="agent1")
        self.registry.register_agent(duplicate_agent)
        
        # Should overwrite the first one
        assert self.registry.get_agent("agent1") == duplicate_agent
        assert len(self.registry.list_agents()) == 1
    
    def test_get_nonexistent_agent(self):
        """Test getting a non-existent agent."""
        result = self.registry.get_agent("nonexistent")
        assert result is None
    
    def test_get_agents_for_job_type(self):
        """Test getting agents by job type."""
        self.registry.register_agent(self.agent1)
        self.registry.register_agent(self.agent2)
        
        agents = self.registry.get_agents_for_job_type(JobType.text_processing)
        
        assert len(agents) == 2
        assert self.agent1 in agents
        assert self.agent2 in agents
    
    def test_get_agents_for_unsupported_job_type(self):
        """Test getting agents for unsupported job type."""
        self.registry.register_agent(self.agent1)
        
        agents = self.registry.get_agents_for_job_type(JobType.web_scraping)
        
        assert len(agents) == 0
    
    def test_list_agents(self):
        """Test listing all agents."""
        assert len(self.registry.list_agents()) == 0
        
        self.registry.register_agent(self.agent1)
        self.registry.register_agent(self.agent2)
        
        agent_names = self.registry.list_agents()
        assert len(agent_names) == 2
        assert "agent1" in agent_names
        assert "agent2" in agent_names
    
    @pytest.mark.asyncio
    async def test_cleanup_all_agents(self):
        """Test cleaning up all agents."""
        # Register agents
        self.registry.register_agent(self.agent1)
        self.registry.register_agent(self.agent2)
        
        # Mock the cleanup method
        self.agent1.cleanup = AsyncMock()
        self.agent2.cleanup = AsyncMock()
        
        await self.registry.cleanup_all()
        
        # Verify cleanup was called
        self.agent1.cleanup.assert_called_once()
        self.agent2.cleanup.assert_called_once()
        
        # Verify registry is empty
        assert len(self.registry.list_agents()) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_with_failing_agent(self):
        """Test cleanup when one agent fails to cleanup."""
        self.registry.register_agent(self.agent1)
        self.registry.register_agent(self.agent2)
        
        # Make one agent fail during cleanup
        self.agent1.cleanup = AsyncMock(side_effect=Exception("Cleanup failed"))
        self.agent2.cleanup = AsyncMock()
        
        # Should not raise exception
        await self.registry.cleanup_all()
        
        # Both cleanup methods should be called
        self.agent1.cleanup.assert_called_once()
        self.agent2.cleanup.assert_called_once()
        
        # Registry should still be cleared
        assert len(self.registry.list_agents()) == 0


class TestGlobalRegistry:
    """Test cases for global registry functions."""
    
    def test_get_agent_registry(self):
        """Test getting global agent registry."""
        registry = get_agent_registry()
        assert isinstance(registry, AgentRegistry)
        
        # Should return same instance
        registry2 = get_agent_registry()
        assert registry is registry2


if __name__ == "__main__":
    pytest.main([__file__]) 