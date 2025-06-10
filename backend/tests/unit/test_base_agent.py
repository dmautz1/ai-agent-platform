"""
Unit tests for Base Agent Classes

Tests the base agent functionality with unified LLM service integration.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

from agent import (
    BaseAgent,
    AgentExecutionResult,
    AgentRegistry,
    get_agent_registry
)
from config.agent import AgentProfile, PerformanceMode
from models import JobStatus, JobDataBase


class TestAgentExecutionResult:
    """Test agent execution result data structure"""
    
    def test_execution_result_success(self):
        """Test successful execution result"""
        result = AgentExecutionResult(
            success=True,
            result="Task completed successfully",
            metadata={"duration": 1.5, "tokens": 100},
            execution_time=2.3
        )
        
        assert result.success == True
        assert result.result == "Task completed successfully"
        assert result.error_message is None
        assert result.metadata["duration"] == 1.5
        assert result.execution_time == 2.3
    
    def test_execution_result_failure(self):
        """Test failed execution result"""
        result = AgentExecutionResult(
            success=False,
            error_message="Task failed due to timeout",
            execution_time=5.0
        )
        
        assert result.success == False
        assert result.result is None
        assert result.error_message == "Task failed due to timeout"
        assert result.execution_time == 5.0
    
    def test_execution_result_to_dict(self):
        """Test converting execution result to dictionary"""
        result = AgentExecutionResult(
            success=True,
            result="Success",
            metadata={"key": "value"},
            execution_time=1.0,
            result_format="json"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] == True
        assert result_dict["result"] == "Success"
        assert result_dict["metadata"]["key"] == "value"
        assert result_dict["execution_time"] == 1.0
        assert result_dict["result_format"] == "json"
    
    def test_execution_result_without_format(self):
        """Test execution result without result_format specified"""
        result = AgentExecutionResult(
            success=True,
            result="Success"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] == True
        assert result_dict["result"] == "Success"
        assert result_dict["result_format"] is None


class TestBaseAgent:
    """Test base agent functionality"""
    
    @pytest.fixture
    def test_agent_class(self):
        """Create test agent class"""
        class TestAgent(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "You are a test agent."
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(
                    success=True,
                    result="Test job completed",
                    metadata={"test": True}
                )
        
        return TestAgent
    
    def test_base_agent_initialization(self, test_agent_class):
        """Test base agent initialization"""
        agent = test_agent_class(
            name="test_agent",
            description="Test agent description",
            model="gemini-1.5-pro"
        )
        
        assert agent.name == "test_agent"
        assert agent.description == "Test agent description"
        assert agent.model == "gemini-1.5-pro"
        assert not agent.is_initialized
    
    def test_agent_identifier_property(self, test_agent_class):
        """Test agent identifier derivation"""
        agent = test_agent_class(name="test", description="Test")
        
        # Should convert "TestAgent" to "test"
        assert agent.agent_identifier == "test"
    
    @pytest.mark.asyncio
    async def test_agent_initialization_method(self, test_agent_class):
        """Test agent initialization method"""
        with patch('agent.DatabaseClient') as mock_db_client:
            agent = test_agent_class(name="test", description="Test")
            
            await agent.initialize()
            
            assert agent.is_initialized == True
            assert agent._db_client is not None
            mock_db_client.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_initialization_already_initialized(self, test_agent_class):
        """Test agent initialization when already initialized"""
        agent = test_agent_class(name="test", description="Test")
        agent.is_initialized = True
        
        with patch('agent.DatabaseClient') as mock_db_client:
            await agent.initialize()
            
            # Should not create new database client
            mock_db_client.assert_not_called()


class TestBaseAgentJobExecution:
    """Test base agent job execution functionality"""
    
    @pytest.fixture
    def mock_job_data(self):
        """Mock job data"""
        job_data = Mock(spec=JobDataBase)
        job_data.task = "Test task"
        return job_data
    
    @pytest.fixture
    def test_agent(self):
        """Create test agent instance"""
        class TestAgent(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Test agent instruction"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(
                    success=True,
                    result="Job completed successfully",
                    metadata={"task": job_data.task}
                )
        
        agent = TestAgent(name="test_job_agent", description="Test")
        agent.is_initialized = True
        
        # Mock database client
        mock_db_client = Mock()
        mock_db_client.update_job = AsyncMock()
        agent._db_client = mock_db_client
        
        return agent
    
    @pytest.mark.asyncio
    async def test_execute_job_success(self, test_agent, mock_job_data):
        """Test successful job execution"""
        job_id = str(uuid.uuid4())
        user_id = "test_user"
        
        result = await test_agent.execute_job(job_id, mock_job_data, user_id)
        
        assert result.success == True
        assert result.result == "Job completed successfully"
        assert result.metadata["task"] == "Test task"
        assert result.execution_time is not None
        assert test_agent.execution_count == 1
        assert test_agent.last_execution_time is not None
    
    @pytest.mark.asyncio
    async def test_execute_job_initialization(self, mock_job_data):
        """Test job execution triggers initialization"""
        class TestAgent(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Test agent"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(success=True, result="Success")
        
        with patch.object(TestAgent, 'initialize') as mock_init:
            agent = TestAgent(name="uninit_test", description="Test")
            
            await agent.execute_job("test_job", mock_job_data)
            
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job_database_updates(self, test_agent, mock_job_data):
        """Test job execution database status updates"""
        job_id = str(uuid.uuid4())
        
        await test_agent.execute_job(job_id, mock_job_data)
        
        # Verify database update calls
        db_client = test_agent._db_client
        assert db_client.update_job.call_count == 2  # running + completed
    
    @pytest.mark.asyncio
    async def test_execute_job_error_handling(self, mock_job_data):
        """Test job execution error handling"""
        class FailingAgent(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Failing agent"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                raise Exception("Job logic failed")
        
        agent = FailingAgent(name="failing_test", description="Test")
        agent.is_initialized = True
        
        result = await agent.execute_job("test_job", mock_job_data)
        
        assert result.success == False
        assert "Unexpected error during job execution" in result.error_message
        assert result.execution_time is not None


class TestBaseAgentInfo:
    """Test base agent information and health check functionality"""
    
    @pytest.fixture
    def test_agent(self):
        """Create test agent"""
        class TestAgent(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Test agent"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(success=True, result="Success")
        
        agent = TestAgent(
            name="info_test",
            description="Information test agent",
            model="gemini-1.5-pro"
        )
        
        return agent
    
    @pytest.mark.asyncio
    async def test_get_agent_info(self, test_agent):
        """Test getting comprehensive agent information"""
        with patch('config.environment.get_settings') as mock_get_settings:
            # Mock settings to return a default provider
            mock_settings = Mock()
            mock_settings.default_llm_provider = "google"
            mock_get_settings.return_value = mock_settings
            
            info = await test_agent.get_agent_info()
            
            assert info["name"] == "info_test"
            assert info["description"] == "Information test agent"
            assert info["agent_identifier"] == "test"  # From TestAgent class name
            assert info["model"] == "gemini-1.5-pro"
            assert info["is_initialized"] == False
            assert info["execution_count"] == 0
            assert "llm" in info
            assert info["llm"]["default_provider"] == "google"
            assert info["llm"]["unified_service_available"] == True
            # Should not have google_ai info since BaseAgent no longer includes it
            assert "google_ai" not in info
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, test_agent):
        """Test health check when all systems healthy"""
        # Mock database health check
        mock_db_client = Mock()
        mock_db_client.health_check = AsyncMock(return_value=True)
        test_agent._db_client = mock_db_client
        
        # Mock LLM service
        mock_llm_service = Mock()
        mock_llm_service._default_provider = "google"
        mock_llm_service.get_available_providers = Mock(return_value=["google", "openai"])
        
        with patch.object(test_agent, 'get_llm_service', return_value=mock_llm_service):
            health = await test_agent.health_check()
            
            assert health["status"] == "healthy"
            assert health["agent_name"] == "info_test"
            assert health["checks"]["database"] == "healthy"
            assert health["checks"]["llm_service"]["status"] == "healthy"
            assert health["checks"]["llm_service"]["default_provider"] == "google"
            assert health["checks"]["llm_service"]["provider_count"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, test_agent):
        """Test health check when database unhealthy"""
        # Mock unhealthy database
        mock_db_client = Mock()
        mock_db_client.health_check = AsyncMock(return_value=False)
        test_agent._db_client = mock_db_client
        
        health = await test_agent.health_check()
        
        assert health["status"] == "degraded"
        assert health["checks"]["database"] == "unhealthy"
        assert "database" in health["failed_checks"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, test_agent):
        """Test agent cleanup"""
        # Setup agent with resources
        mock_db_client = Mock()
        mock_db_client.close = AsyncMock()
        test_agent._db_client = mock_db_client
        test_agent.is_initialized = True
        
        await test_agent.cleanup()
        
        mock_db_client.close.assert_called_once()
        assert test_agent._db_client is None
        assert test_agent.is_initialized == False


class TestAgentRegistry:
    """Test agent registry functionality"""
    
    @pytest.fixture
    def test_agents(self):
        """Create test agents for registry"""
        class TestAgent1(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Agent 1"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(success=True, result="Agent 1 result")
        
        class TestAgent2(BaseAgent):
            def _get_system_instruction(self) -> str:
                return "Agent 2"
            
            async def _execute_job_logic(self, job_data: JobDataBase) -> AgentExecutionResult:
                return AgentExecutionResult(success=True, result="Agent 2 result")
        
        agent1 = TestAgent1(name="agent1", description="First agent")
        agent2 = TestAgent2(name="agent2", description="Second agent")
        
        return agent1, agent2
    
    def test_registry_initialization(self):
        """Test agent registry initialization"""
        registry = AgentRegistry()
        
        assert len(registry._agents) == 0
        assert registry.list_agents() == []
    
    def test_register_agent(self, test_agents):
        """Test registering agents in registry"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        assert len(registry._agents) == 2
        assert "agent1" in registry._agents
        assert "agent2" in registry._agents
        assert registry.get_agent("agent1") == agent1
        assert registry.get_agent("agent2") == agent2
    
    def test_register_agent_replacement(self, test_agents):
        """Test replacing existing agent in registry"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        # Register first agent
        registry.register_agent(agent1)
        assert registry.get_agent("agent1") == agent1
        
        # Register second agent with same name
        agent2.name = "agent1"  # Same name as first agent
        registry.register_agent(agent2)
        
        # Should replace first agent
        assert registry.get_agent("agent1") == agent2
        assert len(registry._agents) == 1
    
    def test_unregister_agent(self, test_agents):
        """Test unregistering agents from registry"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Unregister existing agent
        result = registry.unregister_agent("agent1")
        
        assert result == True
        assert "agent1" not in registry._agents
        assert "agent2" in registry._agents
        
        # Try to unregister non-existent agent
        result = registry.unregister_agent("nonexistent")
        
        assert result == False
    
    def test_get_agent(self, test_agents):
        """Test getting agents from registry"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        
        # Get existing agent
        retrieved = registry.get_agent("agent1")
        assert retrieved == agent1
        
        # Get non-existent agent
        retrieved = registry.get_agent("nonexistent")
        assert retrieved is None
    
    def test_list_agents(self, test_agents):
        """Test listing all agent names"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        agent_names = registry.list_agents()
        
        assert set(agent_names) == {"agent1", "agent2"}
    
    @pytest.mark.asyncio
    async def test_cleanup_all_agents(self, test_agents):
        """Test cleaning up all agents in registry"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Mock cleanup methods
        agent1.cleanup = AsyncMock()
        agent2.cleanup = AsyncMock()
        
        await registry.cleanup_all()
        
        agent1.cleanup.assert_called_once()
        agent2.cleanup.assert_called_once()
        assert len(registry._agents) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_all_with_error(self, test_agents):
        """Test cleanup all agents when one agent cleanup fails"""
        agent1, agent2 = test_agents
        registry = AgentRegistry()
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Mock cleanup methods - one fails
        agent1.cleanup = AsyncMock(side_effect=Exception("Cleanup failed"))
        agent2.cleanup = AsyncMock()
        
        await registry.cleanup_all()
        
        # Should continue cleanup despite error
        agent1.cleanup.assert_called_once()
        agent2.cleanup.assert_called_once()
        assert len(registry._agents) == 0
    
    def test_global_registry_singleton(self):
        """Test global registry singleton pattern"""
        registry1 = get_agent_registry()
        registry2 = get_agent_registry()
        
        assert registry1 is registry2


if __name__ == "__main__":
    pytest.main([__file__]) 