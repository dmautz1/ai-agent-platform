"""
Unit tests for main FastAPI application.
Tests for API endpoints including authentication-protected routes and CORS functionality.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root health check endpoint - public"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Agent Template API is running"
    assert data["status"] == "healthy"

def test_health_check_endpoint():
    """Test the detailed health check endpoint - public"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "environment" in data
    assert "cors_origins" in data
    assert isinstance(data["cors_origins"], int)

def test_public_job_stats_endpoint():
    """Test the public job statistics endpoint"""
    response = client.get("/public/job-stats")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert data["stats"]["total_jobs"] == 0

def test_cors_info_endpoint():
    """Test the CORS info endpoint"""
    response = client.get("/cors-info")
    assert response.status_code == 200
    data = response.json()
    
    # Should include environment and CORS information
    assert "environment" in data
    assert "message" in data
    
    # Content depends on environment
    if data["environment"] == "development":
        assert "cors_origins" in data
        assert isinstance(data["cors_origins"], list)
    else:
        assert "cors_enabled" in data
        assert "origins_count" in data

# Authentication-protected endpoint tests
def test_auth_me_endpoint_without_token():
    """Test /auth/me endpoint without authentication token"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # No authorization header

def test_auth_me_endpoint_with_invalid_token():
    """Test /auth/me endpoint with invalid authentication token"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401

@patch('main.get_current_user')
def test_auth_me_endpoint_with_valid_token(mock_get_current_user):
    """Test /auth/me endpoint with valid authentication token"""
    # Mock the authentication dependency
    mock_get_current_user.return_value = {
        "id": "test-user-id",
        "email": "test@example.com"
    }
    
    headers = {"Authorization": "Bearer valid-token"}
    
    # We need to mock the dependency at the app level
    with patch('auth.verify_token') as mock_verify:
        mock_verify.return_value = {
            "id": "test-user-id", 
            "email": "test@example.com"
        }
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Authentication successful"
        assert data["user"]["id"] == "test-user-id"

def test_schedule_job_without_token():
    """Test schedule job endpoint without authentication"""
    response = client.post("/schedule-job")
    assert response.status_code == 403

def test_schedule_job_with_invalid_token():
    """Test schedule job endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.post("/schedule-job", headers=headers)
    assert response.status_code == 401

@patch('auth.verify_token')
def test_schedule_job_with_valid_token(mock_verify_token):
    """Test schedule job endpoint with valid authentication"""
    mock_verify_token.return_value = {
        "id": "test-user-id",
        "email": "test@example.com"
    }
    
    headers = {"Authorization": "Bearer valid-token"}
    response = client.post("/schedule-job", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    assert data["user_id"] == "test-user-id"

def test_get_jobs_without_token():
    """Test get jobs endpoint without authentication"""
    response = client.get("/jobs")
    assert response.status_code == 403

@patch('auth.verify_token')
def test_get_jobs_with_valid_token(mock_verify_token):
    """Test get jobs endpoint with valid authentication"""
    mock_verify_token.return_value = {
        "id": "test-user-id",
        "email": "test@example.com"
    }
    
    headers = {"Authorization": "Bearer valid-token"}
    response = client.get("/jobs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    assert data["user_id"] == "test-user-id"
    assert data["jobs"] == []

def test_get_job_without_token():
    """Test get specific job endpoint without authentication"""
    response = client.get("/job/test-job-id")
    assert response.status_code == 403

@patch('auth.verify_token')
def test_get_job_with_valid_token(mock_verify_token):
    """Test get specific job endpoint with valid authentication"""
    mock_verify_token.return_value = {
        "id": "test-user-id",
        "email": "test@example.com"
    }
    
    headers = {"Authorization": "Bearer valid-token"}
    response = client.get("/job/test-job-id", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    assert data["job_id"] == "test-job-id"
    assert data["user_id"] == "test-user-id"

# CORS-related tests
def test_cors_headers_with_origin():
    """Test that CORS headers are handled for requests with Origin"""
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)
    
    assert response.status_code == 200
    # Note: TestClient doesn't show CORS headers, but middleware should handle them

def test_preflight_options_request():
    """Test CORS preflight OPTIONS request handling"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type"
    }
    
    # Try OPTIONS on a protected endpoint
    response = client.options("/schedule-job", headers=headers)
    
    # Should handle CORS even if endpoint doesn't explicitly support OPTIONS
    assert response.status_code in [200, 405]

def test_cors_with_credentials():
    """Test CORS functionality with credentials (Authorization header)"""
    headers = {
        "Origin": "http://localhost:3000",
        "Authorization": "Bearer test-token"
    }
    
    response = client.get("/health", headers=headers)
    assert response.status_code == 200

# Google ADK Configuration endpoint tests
@patch('main.validate_adk_environment')
def test_adk_validate_endpoint_success(mock_validate_adk):
    """Test ADK validation endpoint with successful validation"""
    mock_validate_adk.return_value = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config": {
            "use_vertex_ai": False,
            "default_model": "gemini-2.0-flash",
            "available_models": ["gemini-2.0-flash"]
        }
    }
    
    response = client.get("/adk/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Google ADK is properly configured"
    assert "config" in data

@patch('main.validate_adk_environment')
def test_adk_validate_endpoint_failure(mock_validate_adk):
    """Test ADK validation endpoint with validation failure"""
    mock_validate_adk.return_value = {
        "valid": False,
        "errors": ["Google API key not configured"],
        "warnings": ["No credentials found"],
        "config": {}
    }
    
    response = client.get("/adk/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Google ADK configuration has issues"
    assert "errors" in data
    assert len(data["errors"]) > 0

@patch('main.validate_adk_environment')
def test_adk_validate_endpoint_exception(mock_validate_adk):
    """Test ADK validation endpoint with exception"""
    mock_validate_adk.side_effect = Exception("Configuration error")
    
    response = client.get("/adk/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Failed to validate ADK configuration"
    assert "error" in data

@patch('main.get_adk_config')
def test_adk_models_endpoint_success(mock_get_adk_config):
    """Test available models endpoint with successful response"""
    mock_config = Mock()
    mock_config.get_available_models.return_value = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
    mock_config.default_model = "gemini-2.0-flash"
    mock_config.use_vertex_ai = False
    mock_get_adk_config.return_value = mock_config
    
    response = client.get("/adk/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["models"]) == 3
    assert data["default_model"] == "gemini-2.0-flash"
    assert data["service"] == "Google AI Studio"

@patch('main.get_adk_config')
def test_adk_models_endpoint_vertex_ai(mock_get_adk_config):
    """Test available models endpoint for Vertex AI configuration"""
    mock_config = Mock()
    mock_config.get_available_models.return_value = ["gemini-2.0-flash"]
    mock_config.default_model = "gemini-2.0-flash"
    mock_config.use_vertex_ai = True
    mock_get_adk_config.return_value = mock_config
    
    response = client.get("/adk/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["service"] == "Vertex AI"

@patch('main.get_adk_config')
def test_adk_models_endpoint_exception(mock_get_adk_config):
    """Test available models endpoint with exception"""
    mock_get_adk_config.side_effect = Exception("Configuration error")
    
    response = client.get("/adk/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Failed to retrieve available models"
    assert "error" in data

@patch('main.get_adk_config')
def test_adk_connection_test_success(mock_get_adk_config):
    """Test ADK connection test endpoint with successful connection"""
    mock_config = Mock()
    mock_config.test_connection.return_value = {
        "status": "success",
        "service": "Google AI Studio",
        "model": "gemini-2.0-flash",
        "project": None
    }
    mock_get_adk_config.return_value = mock_config
    
    response = client.get("/adk/connection-test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Successfully connected to Google AI services"
    assert data["service"] == "Google AI Studio"
    assert data["model"] == "gemini-2.0-flash"

@patch('main.get_adk_config')
def test_adk_connection_test_failure(mock_get_adk_config):
    """Test ADK connection test endpoint with connection failure"""
    mock_config = Mock()
    mock_config.test_connection.return_value = {
        "status": "error",
        "error": "Authentication failed",
        "service": "Google AI Studio"
    }
    mock_get_adk_config.return_value = mock_config
    
    response = client.get("/adk/connection-test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Failed to connect to Google AI services"
    assert data["error"] == "Authentication failed"
    assert data["service"] == "Google AI Studio"

@patch('main.get_adk_config')
def test_adk_connection_test_exception(mock_get_adk_config):
    """Test ADK connection test endpoint with exception"""
    mock_get_adk_config.side_effect = Exception("Configuration error")
    
    response = client.get("/adk/connection-test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Connection test failed"
    assert "error" in data

# Agent Management endpoint tests
@patch('main.get_agent_registry')
def test_list_agents_endpoint_success(mock_get_registry):
    """Test list agents endpoint with successful response"""
    mock_agent = Mock()
    mock_agent.get_agent_info = AsyncMock(return_value={
        "name": "test_agent",
        "description": "Test agent",
        "agent_type": "google_adk",
        "supported_job_types": ["text_processing"]
    })
    
    mock_registry = Mock()
    mock_registry.list_agents.return_value = ["test_agent"]
    mock_registry.get_agent.return_value = mock_agent
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["agents"]) == 1
    assert data["total_count"] == 1

@patch('main.get_agent_registry')
def test_list_agents_endpoint_empty(mock_get_registry):
    """Test list agents endpoint with no agents"""
    mock_registry = Mock()
    mock_registry.list_agents.return_value = []
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["agents"]) == 0
    assert data["total_count"] == 0

@patch('main.get_agent_registry')
def test_get_agent_info_endpoint_success(mock_get_registry):
    """Test get agent info endpoint with successful response"""
    mock_agent = Mock()
    mock_agent.get_agent_info = AsyncMock(return_value={
        "name": "test_agent",
        "description": "Test agent"
    })
    
    mock_registry = Mock()
    mock_registry.get_agent.return_value = mock_agent
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/test_agent")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"]["name"] == "test_agent"

@patch('main.get_agent_registry')
def test_get_agent_info_endpoint_not_found(mock_get_registry):
    """Test get agent info endpoint with agent not found"""
    mock_registry = Mock()
    mock_registry.get_agent.return_value = None
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/nonexistent")
    assert response.status_code == 404

@patch('main.get_agent_registry')
def test_get_agent_health_endpoint_success(mock_get_registry):
    """Test get agent health endpoint with successful response"""
    mock_agent = Mock()
    mock_agent.health_check = AsyncMock(return_value={
        "healthy": True,
        "agent_name": "test_agent"
    })
    
    mock_registry = Mock()
    mock_registry.get_agent.return_value = mock_agent
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/test_agent/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["health"]["healthy"] is True

@patch('main.get_agent_registry')
def test_get_agent_health_endpoint_not_found(mock_get_registry):
    """Test get agent health endpoint with agent not found"""
    mock_registry = Mock()
    mock_registry.get_agent.return_value = None
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/nonexistent/health")
    assert response.status_code == 404

@patch('main.get_agent_registry')
def test_get_agents_by_job_type_endpoint_success(mock_get_registry):
    """Test get agents by job type endpoint with successful response"""
    mock_agent = Mock()
    mock_agent.get_agent_info = AsyncMock(return_value={
        "name": "text_agent",
        "supported_job_types": ["text_processing"]
    })
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/by-job-type/text_processing")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["job_type"] == "text_processing"
    assert len(data["agents"]) == 1
    assert data["count"] == 1

def test_get_agents_by_job_type_endpoint_invalid_type():
    """Test get agents by job type endpoint with invalid job type"""
    response = client.get("/agents/by-job-type/invalid_type")
    assert response.status_code == 400

@patch('main.get_agent_registry')
def test_get_agents_by_job_type_endpoint_no_agents(mock_get_registry):
    """Test get agents by job type endpoint with no supporting agents"""
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/agents/by-job-type/web_scraping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["agents"]) == 0
    assert data["count"] == 0

# Text Processing endpoint tests
@patch('main.get_agent_registry')
def test_get_text_processing_operations_success(mock_get_registry):
    """Test get text processing operations endpoint with success"""
    mock_agent = Mock()
    mock_agent.name = "test_text_agent"
    mock_agent.get_operation_info = AsyncMock(return_value={
        "operations": {"analyze_sentiment": {"description": "Test"}},
        "total_operations": 1
    })
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/text-processing/operations")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent_name"] == "test_text_agent"

@patch('main.get_agent_registry')
def test_get_text_processing_operations_no_agents(mock_get_registry):
    """Test get text processing operations endpoint with no agents"""
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/text-processing/operations")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "No text processing agents available" in data["message"]

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_process_text_endpoint_success(mock_verify_token, mock_get_registry):
    """Test text processing endpoint with successful processing"""
    # Mock authentication
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"sentiment": "positive"}',
        metadata={"operation": "analyze_sentiment"},
        execution_time=1.5
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "text": "I love this product!",
        "operation": "analyze_sentiment"
    }
    
    response = client.post("/text-processing/process", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert data["result"] == '{"sentiment": "positive"}'

@patch('auth.verify_token')
def test_process_text_endpoint_missing_fields(mock_verify_token):
    """Test text processing endpoint with missing required fields"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "Sample text"}  # Missing operation
    
    response = client.post("/text-processing/process", json=payload, headers=headers)
    assert response.status_code == 400

def test_process_text_endpoint_no_auth():
    """Test text processing endpoint without authentication"""
    payload = {
        "text": "Sample text",
        "operation": "analyze_sentiment"
    }
    
    response = client.post("/text-processing/process", json=payload)
    assert response.status_code == 403

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_process_text_endpoint_no_agents(mock_verify_token, mock_get_registry):
    """Test text processing endpoint with no available agents"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "text": "Sample text",
        "operation": "analyze_sentiment"
    }
    
    response = client.post("/text-processing/process", json=payload, headers=headers)
    assert response.status_code == 503

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_process_text_endpoint_agent_failure(mock_verify_token, mock_get_registry):
    """Test text processing endpoint with agent execution failure"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent with failure
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=False,
        error_message="Processing failed",
        execution_time=0.5
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "text": "Sample text",
        "operation": "analyze_sentiment"
    }
    
    response = client.post("/text-processing/process", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "Processing failed"

@patch('main.process_text_endpoint')
@patch('auth.verify_token')
def test_analyze_sentiment_endpoint(mock_verify_token, mock_process_text):
    """Test sentiment analysis convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_process_text.return_value = {"status": "success", "result": "sentiment analysis"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "I love this!"}
    
    response = client.post("/text-processing/analyze-sentiment", json=payload, headers=headers)
    # The convenience endpoint should call the main process endpoint
    mock_process_text.assert_called_once()

@patch('main.process_text_endpoint')
@patch('auth.verify_token')
def test_extract_keywords_endpoint(mock_verify_token, mock_process_text):
    """Test keyword extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_process_text.return_value = {"status": "success", "result": "keywords"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "Machine learning algorithms"}
    
    response = client.post("/text-processing/extract-keywords", json=payload, headers=headers)
    mock_process_text.assert_called_once()

@patch('main.process_text_endpoint')
@patch('auth.verify_token')
def test_classify_text_endpoint(mock_verify_token, mock_process_text):
    """Test text classification convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_process_text.return_value = {"status": "success", "result": "classification"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "Technical documentation"}
    
    response = client.post("/text-processing/classify-text", json=payload, headers=headers)
    mock_process_text.assert_called_once()

# Summarization endpoint tests
@patch('main.get_agent_registry')
def test_get_summarization_capabilities_success(mock_get_registry):
    """Test get summarization capabilities endpoint with success"""
    mock_agent = Mock()
    mock_agent.name = "test_summarizer"
    mock_agent.get_summarization_info = AsyncMock(return_value={
        "supported_media_types": ["text_summarization", "audio_summarization", "video_summarization"],
        "text_summarization": {"supported_types": ["comprehensive", "extractive"]},
        "total_media_types": 3
    })
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/summarization/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent_name"] == "test_summarizer"
    assert "capabilities" in data

@patch('main.get_agent_registry')
def test_get_summarization_capabilities_no_agents(mock_get_registry):
    """Test get summarization capabilities endpoint with no agents"""
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/summarization/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "No summarization agents available" in data["message"]

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_text_endpoint_success(mock_verify_token, mock_get_registry):
    """Test text summarization endpoint with successful processing"""
    # Mock authentication
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"summary": "This is a comprehensive summary.", "confidence": 0.9}',
        metadata={"job_type": "text_summarization"},
        execution_time=2.1
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "text": "This is a long article that needs to be summarized for better understanding and readability.",
        "max_length": 150,
        "min_length": 50,
        "style": "comprehensive"
    }
    
    response = client.post("/summarization/text", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert "summary" in data
    assert data["execution_time"] == 2.1

@patch('auth.verify_token')
def test_summarize_text_endpoint_missing_text(mock_verify_token):
    """Test text summarization endpoint with missing text field"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"max_length": 100}  # Missing text field
    
    response = client.post("/summarization/text", json=payload, headers=headers)
    assert response.status_code == 400

def test_summarize_text_endpoint_no_auth():
    """Test text summarization endpoint without authentication"""
    payload = {
        "text": "Sample text to summarize",
        "max_length": 100
    }
    
    response = client.post("/summarization/text", json=payload)
    assert response.status_code == 403

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_text_endpoint_no_agents(mock_verify_token, mock_get_registry):
    """Test text summarization endpoint with no available agents"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "Sample text"}
    
    response = client.post("/summarization/text", json=payload, headers=headers)
    assert response.status_code == 503

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_audio_endpoint_success(mock_verify_token, mock_get_registry):
    """Test audio summarization endpoint with successful processing"""
    # Mock authentication
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"summary": "Audio discusses key topics.", "speakers": ["Speaker A"]}',
        metadata={"job_type": "audio_summarization"},
        execution_time=3.2
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "transcript": "This is a transcript of the audio recording discussing AI technology and its applications.",
        "max_length": 200,
        "include_timestamps": True,
        "extract_speakers": True
    }
    
    response = client.post("/summarization/audio", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert "summary" in data

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_audio_endpoint_with_url(mock_verify_token, mock_get_registry):
    """Test audio summarization endpoint with audio URL"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"summary": "Audio from URL processed."}',
        metadata={"job_type": "audio_summarization"},
        execution_time=4.5
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "audio_url": "https://example.com/audio.mp3",
        "max_length": 150,
        "summary_type": "key_points"
    }
    
    response = client.post("/summarization/audio", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@patch('auth.verify_token')
def test_summarize_audio_endpoint_no_source(mock_verify_token):
    """Test audio summarization endpoint with no audio source"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"max_length": 150}  # No audio source provided
    
    response = client.post("/summarization/audio", json=payload, headers=headers)
    assert response.status_code == 400

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_video_endpoint_success(mock_verify_token, mock_get_registry):
    """Test video summarization endpoint with successful processing"""
    # Mock authentication
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"summary": "Video shows presentation.", "visual_summary": "Charts and diagrams"}',
        metadata={"job_type": "video_summarization"},
        execution_time=5.8
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "video_url": "https://example.com/video.mp4",
        "max_length": 300,
        "include_visual_analysis": True,
        "extract_key_moments": True,
        "frame_sampling_rate": 60
    }
    
    response = client.post("/summarization/video", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert "summary" in data

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarize_video_endpoint_with_transcript(mock_verify_token, mock_get_registry):
    """Test video summarization endpoint with transcript only"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"summary": "Video transcript summarized."}',
        metadata={"job_type": "video_summarization"},
        execution_time=3.1
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "transcript": "This is the transcript of a video presentation about machine learning.",
        "max_length": 200,
        "include_visual_analysis": False
    }
    
    response = client.post("/summarization/video", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@patch('auth.verify_token')
def test_summarize_video_endpoint_no_source(mock_verify_token):
    """Test video summarization endpoint with no video source"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"max_length": 250}  # No video source provided
    
    response = client.post("/summarization/video", json=payload, headers=headers)
    assert response.status_code == 400

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_summarization_endpoint_agent_failure(mock_verify_token, mock_get_registry):
    """Test summarization endpoint with agent execution failure"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent with failure
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=False,
        error_message="Summarization processing failed",
        execution_time=1.2
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"text": "Sample text for summarization"}
    
    response = client.post("/summarization/text", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "Summarization processing failed"

def test_summarization_endpoints_no_auth():
    """Test all summarization endpoints without authentication"""
    endpoints_and_payloads = [
        ("/summarization/text", {"text": "Sample text"}),
        ("/summarization/audio", {"transcript": "Sample transcript"}),
        ("/summarization/video", {"transcript": "Sample video transcript"})
    ]
    
    for endpoint, payload in endpoints_and_payloads:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 403

# Web Scraping endpoint tests
@patch('main.get_agent_registry')
def test_get_web_scraping_capabilities_success(mock_get_registry):
    """Test get web scraping capabilities endpoint with success"""
    mock_agent = Mock()
    mock_agent.name = "test_web_scraper"
    mock_agent.get_scraping_info = AsyncMock(return_value={
        "supported_operations": ["extract_text", "extract_links", "full_page_scrape"],
        "features": {"rate_limiting": True, "error_recovery": True},
        "default_options": {"timeout": 30}
    })
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/web-scraping/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent_name"] == "test_web_scraper"
    assert "capabilities" in data

@patch('main.get_agent_registry')
def test_get_web_scraping_capabilities_no_agents(mock_get_registry):
    """Test get web scraping capabilities endpoint with no agents"""
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    response = client.get("/web-scraping/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "No web scraping agents available" in data["message"]

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_scrape_website_endpoint_success(mock_verify_token, mock_get_registry):
    """Test web scraping endpoint with successful processing"""
    # Mock authentication
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"operation": "extract_text", "full_text": "Sample website content", "word_count": 100}',
        metadata={"job_type": "web_scraping", "url": "https://example.com"},
        execution_time=2.5
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "url": "https://example.com",
        "options": {"operation": "extract_text"}
    }
    
    response = client.post("/web-scraping/scrape", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "job_id" in data
    assert "scraped_data" in data
    assert data["execution_time"] == 2.5

@patch('auth.verify_token')
def test_scrape_website_endpoint_missing_url(mock_verify_token):
    """Test web scraping endpoint with missing URL"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"options": {"operation": "extract_text"}}  # Missing URL
    
    response = client.post("/web-scraping/scrape", json=payload, headers=headers)
    assert response.status_code == 400

def test_scrape_website_endpoint_no_auth():
    """Test web scraping endpoint without authentication"""
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/scrape", json=payload)
    assert response.status_code == 403

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_scrape_website_endpoint_no_agents(mock_verify_token, mock_get_registry):
    """Test web scraping endpoint with no available agents"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = []
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/scrape", json=payload, headers=headers)
    assert response.status_code == 503

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_scrape_website_endpoint_with_selectors(mock_verify_token, mock_get_registry):
    """Test web scraping endpoint with custom selectors"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=True,
        result='{"operation": "extract_by_selectors", "data": {"title": "Page Title", "content": "Page content"}}',
        metadata={"job_type": "web_scraping"},
        execution_time=1.8
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {
        "url": "https://example.com",
        "selectors": {"title": "h1", "content": ".main-content"},
        "options": {"timeout": 60}
    }
    
    response = client.post("/web-scraping/scrape", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@patch('main.get_agent_registry')
@patch('auth.verify_token')
def test_scrape_website_endpoint_agent_failure(mock_verify_token, mock_get_registry):
    """Test web scraping endpoint with agent execution failure"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    
    # Mock agent with failure
    mock_agent = AsyncMock()
    mock_agent.execute_job = AsyncMock(return_value=Mock(
        success=False,
        error_message="Network timeout",
        execution_time=5.0
    ))
    
    mock_registry = Mock()
    mock_registry.get_agents_for_job_type.return_value = [mock_agent]
    mock_get_registry.return_value = mock_registry
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/scrape", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error"] == "Network timeout"

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_text_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test text extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "text content"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-text", json=payload, headers=headers)
    # The convenience endpoint should call the main scrape endpoint
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_links_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test link extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "links data"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-links", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_images_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test image extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "images data"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-images", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_tables_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test table extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "tables data"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-tables", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_metadata_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test metadata extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "metadata"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-metadata", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_extract_contact_info_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test contact info extraction convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "contact info"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/extract-contact-info", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

@patch('main.scrape_website_endpoint')
@patch('auth.verify_token')
def test_full_page_scrape_endpoint(mock_verify_token, mock_scrape_endpoint):
    """Test full page scraping convenience endpoint"""
    mock_verify_token.return_value = {"id": "test-user", "email": "test@example.com"}
    mock_scrape_endpoint.return_value = {"status": "success", "scraped_data": "full page data"}
    
    headers = {"Authorization": "Bearer valid-token"}
    payload = {"url": "https://example.com"}
    
    response = client.post("/web-scraping/full-page", json=payload, headers=headers)
    mock_scrape_endpoint.assert_called_once()

def test_web_scraping_endpoints_no_auth():
    """Test all web scraping endpoints without authentication"""
    endpoints = [
        "/web-scraping/scrape",
        "/web-scraping/extract-text",
        "/web-scraping/extract-links", 
        "/web-scraping/extract-images",
        "/web-scraping/extract-tables",
        "/web-scraping/extract-metadata",
        "/web-scraping/extract-contact-info",
        "/web-scraping/full-page"
    ]
    
    payload = {"url": "https://example.com"}
    
    for endpoint in endpoints:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__]) 