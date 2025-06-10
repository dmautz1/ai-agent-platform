"""
Unit tests for agent_framework.py - Self-contained agent system with automatic registration
"""

import pytest
import asyncio
import inspect
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Import modules to test
from agent_framework import (
    job_model, endpoint, AgentMeta, SelfContainedAgent,
    create_endpoint_wrapper, register_agent_endpoints,
    get_all_agent_info, execute_agent_job, validate_job_data,
    get_registered_agents, get_agent_models, get_agent_endpoints,
    _agent_endpoints, _agent_models, _registered_agents
)
from agent import AgentExecutionResult


class TestJobModelDecorator:
    """Test the @job_model decorator functionality"""
    
    def test_job_model_decorator_registration(self):
        """Test that @job_model decorator marks models correctly"""
        # Clear registry for clean test
        _agent_models.clear()
        
        @job_model
        class TestJobData(BaseModel):
            text: str
            operation: str
        
        # Check that model was marked as job model
        assert hasattr(TestJobData, '_is_job_model')
        assert TestJobData._is_job_model is True
    
    def test_job_model_decorator_agent_name_extraction(self):
        """Test that job models are registered when agents are created"""
        _agent_models.clear()
        _registered_agents.clear()
        
        # Create a job model in the test module
        @job_model
        class AnotherJobData(BaseModel):
            data: str
        
        # Create an agent that will register the job model
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        agent = TestAgent(name="test_agent")
        
        # Check that the job model was registered for this agent
        assert 'test_agent' in _agent_models
        assert 'AnotherJobData' in _agent_models['test_agent']


class TestEndpointDecorator:
    """Test the @endpoint decorator functionality"""
    
    def test_endpoint_decorator_basic(self):
        """Test basic endpoint decorator functionality"""
        
        @endpoint("/test-endpoint", methods=["GET", "POST"])
        def test_function():
            pass
        
        assert hasattr(test_function, '_endpoint_info')
        info = test_function._endpoint_info
        assert info['path'] == "/test-endpoint"
        assert info['methods'] == ["GET", "POST"]
        assert info['auth_required'] is True
        assert info['public'] is False
        assert info['function_name'] == 'test_function'
    
    def test_endpoint_decorator_with_options(self):
        """Test endpoint decorator with custom options"""
        
        @endpoint("/public-endpoint", methods=["GET"], auth_required=False, public=True)
        def public_function():
            pass
        
        info = public_function._endpoint_info
        assert info['path'] == "/public-endpoint"
        assert info['methods'] == ["GET"]
        assert info['auth_required'] is False
        assert info['public'] is True


class TestAgentMeta:
    """Test the AgentMeta metaclass functionality"""
    
    def test_agent_meta_registration(self):
        """Test that AgentMeta discovers agent classes and registers them when instantiated"""
        # Clear registry for clean test
        _agent_endpoints.clear()
        _registered_agents.clear()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        # Create agent instance with explicit name
        agent = TestAgent(name="test_agent")
        
        # Check that agent was registered with its explicit name
        assert 'test_agent' in _agent_endpoints
        assert _agent_endpoints['test_agent'] == TestAgent
        assert 'test_agent' in _registered_agents
        assert _registered_agents['test_agent'] == agent


class TestSelfContainedAgent:
    """Test the SelfContainedAgent base class"""
    
    def setup_method(self):
        """Set up test environment"""
        _agent_endpoints.clear()
        _agent_models.clear()
        _registered_agents.clear()
    
    def test_self_contained_agent_initialization(self):
        """Test SelfContainedAgent initialization"""
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        agent = TestAgent(name="test_agent")
        
        # Check that agent is registered with explicit name
        assert 'test_agent' in _registered_agents
        assert _registered_agents['test_agent'] == agent
        assert agent.name == 'test_agent'
    
    def test_self_contained_agent_custom_name(self):
        """Test SelfContainedAgent with custom name"""
        
        class CustomAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Custom system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="custom result")
        
        agent = CustomAgent(name="custom_name")
        
        assert agent.name == "custom_name"
        # Agent is registered using the explicit name provided
        assert 'custom_name' in _registered_agents
    
    def test_get_endpoints(self):
        """Test getting endpoints from agent class"""
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/test", methods=["POST"])
            def test_method(self):
                pass
            
            @endpoint("/another", methods=["GET"], auth_required=False)
            def another_method(self):
                pass
            
            def regular_method(self):
                pass
        
        endpoints = TestAgent.get_endpoints()
        
        # Should only include methods with endpoint decorator
        assert len(endpoints) == 2
        
        endpoint_paths = [ep['path'] for ep in endpoints]
        assert "/test" in endpoint_paths
        assert "/another" in endpoint_paths
    
    def test_get_models(self):
        """Test getting models from agent class"""
        
        # Create a job model in the test module
        @job_model
        class TestJobData(BaseModel):
            text: str
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        # Create agent instance to trigger model registration
        agent = TestAgent(name="test_agent")
        
        models = TestAgent.get_models()
        assert 'TestJobData' in models
    
    @pytest.mark.asyncio
    async def test_get_agent_info(self):
        """Test getting extended agent info"""
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/process", methods=["POST"])
            def process(self):
                pass
        
        agent = TestAgent(name="test_agent")
        info = await agent.get_agent_info()
        
        assert 'endpoints' in info
        assert 'models' in info
        assert 'framework_version' in info
        assert 'self_contained' in info
        assert info['framework_version'] == '1.0'
        assert info['self_contained'] is True


class TestEndpointWrapper:
    """Test the endpoint wrapper functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.mock_agent = Mock(spec=SelfContainedAgent)
        self.mock_agent.name = "test_agent"
        self.mock_request = Mock(spec=Request)
        self.mock_user = {"id": "user123", "email": "test@example.com"}
    
    @pytest.mark.asyncio
    async def test_create_endpoint_wrapper_sync_method(self):
        """Test endpoint wrapper with synchronous method"""
        
        def sync_method(self, request_data, user):
            return {"result": "success", "data": request_data}
        
        endpoint_info = {
            'path': '/test',
            'methods': ['POST'],
            'auth_required': True,
            'public': False
        }
        
        wrapper = create_endpoint_wrapper(self.mock_agent, sync_method, endpoint_info)
        
        request_data = {"input": "test"}
        result = await wrapper(self.mock_request, request_data, self.mock_user)
        
        assert result["result"] == "success"
        assert result["data"] == request_data
    
    @pytest.mark.asyncio
    async def test_create_endpoint_wrapper_async_method(self):
        """Test endpoint wrapper with asynchronous method"""
        
        async def async_method(self, request_data, user):
            return {"result": "async_success", "user_id": user["id"]}
        
        endpoint_info = {
            'path': '/async-test',
            'methods': ['POST'],
            'auth_required': True,
            'public': False
        }
        
        wrapper = create_endpoint_wrapper(self.mock_agent, async_method, endpoint_info)
        
        request_data = {"input": "test"}
        result = await wrapper(self.mock_request, request_data, self.mock_user)
        
        assert result["result"] == "async_success"
        assert result["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_create_endpoint_wrapper_method_signature_matching(self):
        """Test that wrapper correctly matches method signatures"""
        
        def method_with_request(self, request):
            return {"has_request": True}
        
        def method_with_user_only(self, user):
            return {"user_id": user["id"]}
        
        def method_no_params(self):
            return {"no_params": True}
        
        endpoint_info = {'path': '/test', 'methods': ['POST'], 'auth_required': True, 'public': False}
        
        # Test request parameter
        wrapper1 = create_endpoint_wrapper(self.mock_agent, method_with_request, endpoint_info)
        result1 = await wrapper1(self.mock_request, None, self.mock_user)
        assert result1["has_request"] is True
        
        # Test user parameter only
        wrapper2 = create_endpoint_wrapper(self.mock_agent, method_with_user_only, endpoint_info)
        result2 = await wrapper2(self.mock_request, None, self.mock_user)
        assert result2["user_id"] == "user123"
        
        # Test no parameters
        wrapper3 = create_endpoint_wrapper(self.mock_agent, method_no_params, endpoint_info)
        result3 = await wrapper3(self.mock_request, None, self.mock_user)
        assert result3["no_params"] is True
    
    @pytest.mark.asyncio
    async def test_create_endpoint_wrapper_error_handling(self):
        """Test that wrapper handles errors correctly"""
        
        def failing_method(self, request_data, user):
            raise ValueError("Something went wrong")
        
        endpoint_info = {'path': '/test', 'methods': ['POST'], 'auth_required': True, 'public': False}
        wrapper = create_endpoint_wrapper(self.mock_agent, failing_method, endpoint_info)
        
        with pytest.raises(HTTPException) as exc_info:
            await wrapper(self.mock_request, {}, self.mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Agent operation failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_endpoint_wrapper_http_exception_passthrough(self):
        """Test that HTTPExceptions are passed through unchanged"""
        
        def method_with_http_error(self, request_data, user):
            raise HTTPException(status_code=400, detail="Bad request")
        
        endpoint_info = {'path': '/test', 'methods': ['POST'], 'auth_required': True, 'public': False}
        wrapper = create_endpoint_wrapper(self.mock_agent, method_with_http_error, endpoint_info)
        
        with pytest.raises(HTTPException) as exc_info:
            await wrapper(self.mock_request, {}, self.mock_user)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad request"


class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.mark.asyncio
    async def test_execute_agent_job_success(self):
        """Test successful job execution"""
        
        mock_agent = Mock(spec=SelfContainedAgent)
        mock_agent.name = "test_agent"
        
        # Create successful result
        success_result = AgentExecutionResult(
            success=True,
            result={"output": "processed data"},
            metadata={"tokens": 150},
            execution_time=2.5
        )
        
        mock_agent.execute_job = AsyncMock(return_value=success_result)
        
        job_data = Mock(spec=BaseModel)
        user_id = "user123"
        
        result = await execute_agent_job(mock_agent, job_data, user_id)
        
        assert result["status"] == "success"
        assert result["result"] == {"output": "processed data"}
        assert result["metadata"] == {"tokens": 150}
        assert result["execution_time"] == 2.5
        assert "job_id" in result
    
    @pytest.mark.asyncio
    async def test_execute_agent_job_failure(self):
        """Test failed job execution"""
        
        mock_agent = Mock(spec=SelfContainedAgent)
        mock_agent.name = "test_agent"
        
        # Create failed result
        failed_result = AgentExecutionResult(
            success=False,
            result=None,
            error_message="Processing failed",
            execution_time=1.0
        )
        
        mock_agent.execute_job = AsyncMock(return_value=failed_result)
        
        job_data = Mock(spec=BaseModel)
        user_id = "user123"
        
        result = await execute_agent_job(mock_agent, job_data, user_id)
        
        assert result["status"] == "error"
        assert result["error"] == "Processing failed"
        assert result["execution_time"] == 1.0
        assert "job_id" in result
    
    def test_validate_job_data_success(self):
        """Test successful job data validation"""
        
        class TestJobData(BaseModel):
            text: str
            count: int
        
        data = {"text": "hello", "count": 5}
        result = validate_job_data(data, TestJobData)
        
        assert isinstance(result, TestJobData)
        assert result.text == "hello"
        assert result.count == 5
    
    def test_validate_job_data_failure(self):
        """Test failed job data validation"""
        
        class TestJobData(BaseModel):
            text: str
            count: int
        
        data = {"text": "hello"}  # missing 'count'
        
        with pytest.raises(HTTPException) as exc_info:
            validate_job_data(data, TestJobData)
        
        assert exc_info.value.status_code == 400
        assert "Invalid job data" in str(exc_info.value.detail)
    
    def test_get_all_agent_info(self):
        """Test getting information about all registered agents"""
        
        # Clear and set up test data
        _agent_endpoints.clear()
        _registered_agents.clear()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/process", methods=["POST"])
            def process(self):
                pass
        
        # Create agent instance to register it
        agent = TestAgent(name="test_agent")
        
        info = get_all_agent_info()
        
        assert 'test_agent' in info
    
    def test_get_registered_agents(self):
        """Test getting registered agent instances"""
        
        _registered_agents.clear()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        agent = TestAgent(name="test_agent")
        
        agents = get_registered_agents()
        assert 'test_agent' in agents
        assert agents['test_agent'] == agent
    
    def test_get_agent_models(self):
        """Test getting registered agent models"""
        
        _agent_models.clear()
        _registered_agents.clear()
        
        @job_model
        class TestModel(BaseModel):
            data: str
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        # Create agent instance to register models
        agent = TestAgent(name="test_agent")
        
        models = get_agent_models()
        assert len(models) > 0
        assert 'test_agent' in models
        assert 'TestModel' in models['test_agent']
    
    def test_get_agent_endpoints(self):
        """Test getting registered agent endpoint classes"""
        
        _agent_endpoints.clear()
        _registered_agents.clear()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
        
        # Create agent instance to register it
        agent = TestAgent(name="test_agent")
        
        endpoints = get_agent_endpoints()
        assert 'test_agent' in endpoints


class TestRegisterAgentEndpoints:
    """Test the register_agent_endpoints function"""
    
    def setup_method(self):
        """Set up test environment"""
        _agent_endpoints.clear()
        _registered_agents.clear()
    
    def test_register_agent_endpoints_basic(self):
        """Test basic endpoint registration with FastAPI"""
        
        # Create mock FastAPI app
        mock_app = Mock()
        mock_app.add_api_route = Mock()
        
        # Create mock agent registry
        mock_registry = Mock()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/test-endpoint", methods=["POST"])
            def test_method(self, request_data, user):
                return {"success": True}
        
        # Create agent instance
        agent_instance = TestAgent(name="test_agent")
        
        # Register endpoints
        count = register_agent_endpoints(mock_app, mock_registry)
        
        # Verify endpoint was registered
        assert count == 1
        mock_app.add_api_route.assert_called_once()
        
        # Check the call arguments
        call_args = mock_app.add_api_route.call_args
        assert call_args[1]['path'] == "/test-endpoint"
        assert call_args[1]['methods'] == ["POST"]
    
    def test_register_agent_endpoints_no_agent_instance(self):
        """Test registration when agent instance is not found"""
        
        mock_app = Mock()
        mock_app.add_api_route = Mock()
        
        mock_registry = Mock()
        mock_registry.get_agent = Mock(return_value=None)
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/test", methods=["GET"])
            def test_method(self):
                pass
        
        count = register_agent_endpoints(mock_app, mock_registry)
        
        # Should not register any endpoints
        assert count == 0
        assert not mock_app.add_api_route.called
    
    def test_register_agent_endpoints_multiple_methods(self):
        """Test registration with multiple HTTP methods"""
        
        mock_app = Mock()
        mock_app.add_api_route = Mock()
        
        mock_registry = Mock()
        
        class TestAgent(SelfContainedAgent):
            def _get_system_instruction(self) -> str:
                return "Test system instruction"
            
            async def _execute_job_logic(self, job_data):
                return AgentExecutionResult(success=True, result="test result")
            
            @endpoint("/multi", methods=["GET", "POST", "PUT"])
            def multi_method(self):
                return {"multi": True}
        
        agent_instance = TestAgent(name="test_agent")
        
        count = register_agent_endpoints(mock_app, mock_registry)
        
        # Should register 3 endpoints (one for each method)
        assert count == 3
        assert mock_app.add_api_route.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__]) 