"""
Unit tests for Simple Prompt Agent

Tests the SimplePromptAgent class functionality including LLM provider integration,
error handling, and configuration validation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pydantic import ValidationError

from agents.simple_prompt_agent import SimplePromptAgent, PromptJobData
from agent import AgentExecutionResult
from services.llm_service import LLMProvider


class TestPromptJobData:
    """Test PromptJobData model validation"""
    
    def test_prompt_job_data_valid(self):
        """Test valid PromptJobData creation"""
        data = PromptJobData(
            prompt="Test prompt",
            temperature=0.8
        )
        assert data.prompt == "Test prompt"
        assert data.temperature == 0.8
        assert data.system_instruction is None
        assert data.max_tokens == 1000  # Default value
    
    def test_prompt_job_data_defaults(self):
        """Test PromptJobData with default values"""
        data = PromptJobData(prompt="Test prompt")
        assert data.prompt == "Test prompt"
        assert data.temperature == 0.8  # Default value
        assert data.system_instruction is None
        assert data.max_tokens == 1000  # Default value
    
    def test_prompt_job_data_all_fields(self):
        """Test PromptJobData with all fields specified"""
        data = PromptJobData(
            prompt="Test prompt",
            temperature=0.9,
            system_instruction="You are a helpful assistant",
            max_tokens=500
        )
        assert data.prompt == "Test prompt"
        assert data.temperature == 0.9
        assert data.system_instruction == "You are a helpful assistant"
        assert data.max_tokens == 500
    
    def test_prompt_job_data_invalid_temperature(self):
        """Test validation for invalid temperature"""
        with pytest.raises(ValidationError):
            PromptJobData(
                prompt="Test",
                temperature=3.0  # > 2.0, should be invalid
            )


class TestSimplePromptAgent:
    """Test SimplePromptAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = SimplePromptAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        assert self.agent.name == "simple_prompt"
        assert "simple agent" in self.agent.description.lower()
        assert self.agent.result_format == "markdown"
        assert self.agent.llm_service is not None
    
    def test_get_system_instruction(self):
        """Test system instruction method"""
        instruction = self.agent._get_system_instruction()
        assert isinstance(instruction, str)
        assert len(instruction) > 0
        assert "helpful assistant" in instruction.lower()
    
    @pytest.mark.asyncio
    async def test_get_agent_info(self):
        """Test get_agent_info method"""
        with patch.object(self.agent.llm_service, 'get_available_providers') as mock_providers:
            mock_providers.return_value = ['openai', 'anthropic']
            
            info = await self.agent.get_agent_info()
            
            assert info['name'] == 'simple_prompt'
            assert 'description' in info
            assert 'available_providers' in info
            assert 'default_provider' in info
    
    @pytest.mark.asyncio
    async def test_get_providers_info(self):
        """Test get_providers_info method"""
        with patch.object(self.agent.llm_service, 'get_all_providers_info') as mock_providers:
            mock_providers.return_value = {
                'available_providers': ['openai', 'anthropic', 'google'],
                'default_provider': 'google'
            }
            
            info = await self.agent.get_providers_info()
            
            assert info['available_providers'] == ['openai', 'anthropic', 'google']
            assert info['default_provider'] == 'google'
            mock_providers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """Test get_health_status method"""
        with patch.object(self.agent.llm_service, 'get_connection_health_status') as mock_health:
            mock_health.return_value = {
                'overall_status': 'healthy',
                'loaded_services': 3,
                'total_services': 5
            }
            
            health = await self.agent.get_health_status()
            
            assert health['overall_status'] == 'healthy'
            assert health['loaded_services'] == 3
            assert health['total_services'] == 5
            mock_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_success(self):
        """Test successful job execution"""
        job_data = PromptJobData(
            prompt="Hello, world!",
            temperature=0.7
        )

        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "Hello! How can I help you today?"

            result = await self.agent._execute_job_logic(job_data)

            assert result.success is True
            assert result.result == "Hello! How can I help you today?"
            assert result.metadata['agent'] == 'simple_prompt'
            # Provider will be the default provider (likely 'google')
            assert 'provider' in result.metadata
            assert result.metadata['model'] is None

    @pytest.mark.asyncio
    async def test_execute_job_logic_with_custom_system_instruction(self):
        """Test job execution with custom system instruction"""
        job_data = PromptJobData(
            prompt="Explain AI",
            system_instruction="You are an AI expert",
            temperature=0.8
        )

        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "AI is artificial intelligence..."

            result = await self.agent._execute_job_logic(job_data)

            assert result.success is True
            mock_query.assert_called_once_with(
                prompt="Explain AI",
                provider=None,
                model=None,
                temperature=0.8,
                system_instruction="You are an AI expert",
                max_tokens=1000  # Default value from model
            )

    @pytest.mark.asyncio
    async def test_execute_job_logic_with_all_parameters(self):
        """Test job execution with all parameters specified"""
        job_data = PromptJobData(
            prompt="Write a poem",
            temperature=0.9,
            system_instruction="You are a poet",
            max_tokens=200
        )

        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "Roses are red, violets are blue..."

            result = await self.agent._execute_job_logic(job_data)

            assert result.success is True
            # Provider will be the default provider (likely 'google')
            assert 'provider' in result.metadata
            assert result.metadata['model'] is None
            assert result.metadata['temperature'] == 0.9

    @pytest.mark.asyncio
    async def test_execute_job_logic_failure(self):
        """Test job execution failure handling"""
        job_data = PromptJobData(prompt="Test prompt")
        
        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.side_effect = Exception("LLM service error")
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is False
            assert "LLM service error" in result.error_message
            assert result.metadata['agent'] == 'simple_prompt'


class TestSimplePromptAgentEndpoints:
    """Test SimplePromptAgent endpoint functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = SimplePromptAgent()
        self.mock_user = {'id': 'user123', 'email': 'test@example.com'}
    
    @pytest.mark.asyncio
    async def test_process_prompt_endpoint_success(self):
        """Test successful prompt processing via endpoint"""
        request_data = {
            'prompt': 'Hello, world!',
            'temperature': 0.8
        }
        
        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "Hello! How can I help?"
            
            response = await self.agent.process_prompt(request_data, self.mock_user)
            
            assert response['status'] == 'success'
            assert response['result'] == "Hello! How can I help?"
            assert response['result_format'] == 'markdown'
            assert 'metadata' in response
    
    @pytest.mark.asyncio
    async def test_process_prompt_endpoint_failure(self):
        """Test failed prompt processing via endpoint"""
        request_data = {
            'prompt': 'Test prompt'
        }
        
        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.side_effect = Exception("Service unavailable")
            
            response = await self.agent.process_prompt(request_data, self.mock_user)
            
            assert response['status'] == 'error'
            assert "Service unavailable" in response['error']
    
    @pytest.mark.asyncio
    async def test_get_agent_info_endpoint(self):
        """Test get agent info endpoint"""
        with patch.object(self.agent.llm_service, 'get_available_providers') as mock_providers:
            mock_providers.return_value = ['openai']
            
            response = await self.agent.get_agent_info()
            
            assert response['name'] == 'simple_prompt'
            assert 'description' in response
            assert 'available_providers' in response
    
    @pytest.mark.asyncio
    async def test_get_providers_info_endpoint(self):
        """Test get providers info endpoint"""
        with patch.object(self.agent.llm_service, 'get_all_providers_info') as mock_providers:
            mock_providers.return_value = {
                'available_providers': ['openai', 'anthropic'],
                'default_provider': 'openai'
            }
            
            response = await self.agent.get_providers_info()
            
            assert response['available_providers'] == ['openai', 'anthropic']
            assert response['default_provider'] == 'openai'
    
    @pytest.mark.asyncio
    async def test_get_health_status_endpoint(self):
        """Test get health status endpoint"""
        with patch.object(self.agent.llm_service, 'get_connection_health_status') as mock_health:
            mock_health.return_value = {
                'overall_status': 'healthy',
                'loaded_services': 3
            }
            
            response = await self.agent.get_health_status()
            
            assert response['overall_status'] == 'healthy'
            assert response['loaded_services'] == 3
    
    @pytest.mark.asyncio
    async def test_test_all_connections_endpoint(self):
        """Test test all connections endpoint"""
        with patch.object(self.agent.llm_service, 'test_all_connections') as mock_test:
            mock_test.return_value = {
                'openai': {'status': 'connected', 'latency_ms': 150},
                'anthropic': {'status': 'connected', 'latency_ms': 200}
            }
            
            response = await self.agent.test_all_connections()
            
            assert response['openai']['status'] == 'connected'
            assert response['anthropic']['status'] == 'connected'


class TestSimplePromptAgentIntegration:
    """Integration tests for SimplePromptAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = SimplePromptAgent()
    
    @pytest.mark.asyncio
    async def test_agent_workflow_complete(self):
        """Test complete agent workflow from job data to result"""
        job_data = PromptJobData(
            prompt="What is 2+2?",
            temperature=0.1
        )

        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "2+2 equals 4."

            # Test job execution
            result = await self.agent._execute_job_logic(job_data)

            assert result.success is True
            assert "4" in result.result
            # Provider will be the default provider
            assert 'provider' in result.metadata
            assert result.metadata['temperature'] == 0.1
    
    @pytest.mark.asyncio
    async def test_agent_with_valid_provider(self):
        """Test agent with valid provider"""
        job_data = PromptJobData(
            prompt="Test prompt",
            provider="google"  # Valid provider
        )
        
        with patch.object(self.agent.llm_service, 'query') as mock_query:
            mock_query.return_value = "Test response"
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is True
            assert result.result == "Test response" 