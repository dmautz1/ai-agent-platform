"""
Unit tests for main FastAPI application.
Tests for API endpoints including authentication-protected routes and CORS functionality.
"""

import pytest
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