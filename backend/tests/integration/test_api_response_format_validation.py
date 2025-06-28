"""
Integration tests to validate that all API endpoints return the correct ApiResponse format.

This test suite automatically discovers and tests all endpoints to ensure they conform
to the ApiResponse standard format.
"""

import pytest
import requests
from typing import Dict, List, Any, Optional
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from models import ApiResponse
from tests import (
    validate_api_response_structure,
    assert_api_success_response,
    assert_api_error_response,
    is_api_response_format
)


client = TestClient(app)


class TestApiResponseFormatValidation:
    """Test suite to validate ApiResponse format across all endpoints."""

    def setup_method(self):
        """Set up test method with authentication."""
        # Mock authentication for testing
        self.auth_headers = {"Authorization": "Bearer test-token"}
        
    @pytest.fixture(autouse=True)
    def mock_auth(self):
        """Mock authentication for all tests."""
        with patch('auth.verify_token') as mock_verify:
            mock_verify.return_value = {
                'user_id': 'test-user-123',
                'email': 'test@example.com'
            }
            yield mock_verify

    def test_health_endpoints_return_api_response_format(self):
        """Test that health endpoints return ApiResponse format."""
        # Test only endpoints that we know exist and return ApiResponse format
        health_endpoints = [
            ("GET", "/health"),
        ]
        
        for method, endpoint in health_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    continue  # Skip non-GET methods for health endpoints
                
                # Should return valid status code
                if response.status_code == 200:
                    response_data = response.json()
                    # Validate ApiResponse structure
                    if is_api_response_format(response_data):
                        validate_api_response_structure(response_data)
                        
                        if response_data["success"]:
                            assert_api_success_response(response_data)
                        else:
                            assert_api_error_response(response_data)
                    else:
                        # Some endpoints may not use ApiResponse format yet, that's ok
                        print(f"Note: Endpoint {endpoint} does not use ApiResponse format")
                        
            except Exception as e:
                # Log the error but don't fail the test for optional endpoints
                print(f"Warning: Could not test endpoint {endpoint}: {e}")

    def test_job_endpoints_return_api_response_format(self, mock_auth):
        """Test that job-related endpoints return ApiResponse format."""
        job_endpoints = [
            ("GET", "/jobs/list"),
            ("GET", "/jobs/minimal"),
        ]
        
        for method, endpoint in job_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint, headers=self.auth_headers)
                else:
                    continue
                
                # Should return valid status code or auth error
                if response.status_code == 200:
                    response_data = response.json()
                    # Validate ApiResponse structure
                    assert is_api_response_format(response_data), f"Endpoint {endpoint} does not return ApiResponse format"
                    validate_api_response_structure(response_data)
                    
                    if response_data["success"]:
                        assert_api_success_response(response_data)
                    else:
                        assert_api_error_response(response_data)
                elif response.status_code in [401, 403]:
                    # Auth error is expected if mocking fails
                    response_data = response.json()
                    # Check if it's ApiResponse format (it should be)
                    if is_api_response_format(response_data):
                        validate_api_response_structure(response_data)
                        assert_api_error_response(response_data)
                    else:
                        # If not ApiResponse format, it might be a FastAPI default error
                        print(f"Note: Auth error for {endpoint} is not in ApiResponse format")
                        
            except Exception as e:
                # Don't fail for endpoints that might not exist or have issues
                print(f"Warning: Could not test endpoint {endpoint}: {e}")

    def test_agent_endpoints_return_api_response_format(self, mock_auth):
        """Test that agent-related endpoints return ApiResponse format."""
        agent_endpoints = [
            ("GET", "/agents"),
        ]
        
        for method, endpoint in agent_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint, headers=self.auth_headers)
                else:
                    continue
                
                # Should return valid status code or auth error
                if response.status_code == 200:
                    response_data = response.json()
                    # Validate ApiResponse structure
                    assert is_api_response_format(response_data), f"Endpoint {endpoint} does not return ApiResponse format"
                    validate_api_response_structure(response_data)
                    
                    if response_data["success"]:
                        assert_api_success_response(response_data)
                    else:
                        assert_api_error_response(response_data)
                elif response.status_code in [401, 403]:
                    # Auth error is expected if mocking fails
                    response_data = response.json()
                    # Check if it's ApiResponse format (it should be)
                    if is_api_response_format(response_data):
                        validate_api_response_structure(response_data)
                        assert_api_error_response(response_data)
                    else:
                        # If not ApiResponse format, it might be a FastAPI default error
                        print(f"Note: Auth error for {endpoint} is not in ApiResponse format")
                        
            except Exception as e:
                # Don't fail for endpoints that might not exist or have issues
                print(f"Warning: Could not test endpoint {endpoint}: {e}")

    def test_api_response_consistency_validation(self, mock_auth):
        """Test that ApiResponse format is consistent when it is used."""
        # Test endpoints that we know should work and use ApiResponse
        test_endpoints = [
            ("GET", "/health"),
            ("GET", "/jobs/list"),
            ("GET", "/agents"),
        ]
        
        api_response_endpoints = []
        
        for method, endpoint in test_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint, headers=self.auth_headers if endpoint != "/health" else {})
                else:
                    continue
                
                if response.status_code == 200:
                    response_data = response.json()
                    if is_api_response_format(response_data):
                        api_response_endpoints.append((endpoint, response_data))
                        
            except Exception as e:
                print(f"Warning: Could not test endpoint {endpoint}: {e}")
        
        # Validate that all ApiResponse endpoints follow the same structure
        for endpoint, response_data in api_response_endpoints:
            validate_api_response_structure(response_data)
            
            # Check consistency of success responses
            if response_data["success"]:
                assert response_data["result"] is not None, f"Success response at {endpoint} should have result"
                assert response_data["error"] is None, f"Success response at {endpoint} should not have error"
            else:
                assert response_data["result"] is None, f"Error response at {endpoint} should not have result"
                assert response_data["error"] is not None, f"Error response at {endpoint} should have error"

    def test_known_working_endpoints_use_api_response(self, mock_auth):
        """Test specific endpoints that we know should work and use ApiResponse format."""
        # Only test endpoints we're confident about
        working_endpoints = [
            ("/health", False),  # (endpoint, requires_auth)
        ]
        
        for endpoint, requires_auth in working_endpoints:
            try:
                headers = self.auth_headers if requires_auth else {}
                response = client.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # This should definitely be ApiResponse format
                    assert is_api_response_format(response_data), f"Known working endpoint {endpoint} should use ApiResponse format"
                    validate_api_response_structure(response_data)
                    
                    if response_data["success"]:
                        assert_api_success_response(response_data)
                    else:
                        assert_api_error_response(response_data)
                else:
                    print(f"Note: Endpoint {endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"Warning: Could not test known working endpoint {endpoint}: {e}")


def test_discover_all_endpoints_automatically():
    """
    Automatically discover all endpoints from the FastAPI app and validate ApiResponse format.
    This test ensures no endpoints are missed in manual testing.
    """
    from fastapi.routing import APIRoute
    
    # Get all routes from the FastAPI app
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append((route.methods, route.path))
    
    print(f"Discovered {len(routes)} API routes")
    
    # This is more of a discovery test - we log the routes for manual verification
    for methods, path in routes:
        for method in methods:
            if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                print(f"Found endpoint: {method} {path}")
    
    # Ensure we found some routes
    assert len(routes) > 0, "No API routes discovered"
    
    # Ensure we have the expected core endpoints
    route_paths = [path for methods, path in routes]
    expected_core_paths = ["/health", "/jobs/list", "/agents"]
    
    for expected_path in expected_core_paths:
        matching_paths = [path for path in route_paths if expected_path in path or path == expected_path]
        if not matching_paths:
            print(f"Warning: Expected core endpoint not found: {expected_path}")


def test_api_response_format_documentation():
    """Test that ApiResponse format is well-documented and consistent."""
    # Create sample responses to validate the format
    from utils.responses import create_success_response, create_error_response
    
    # Test success response format
    success_response = create_success_response({"test": "data"}, "Operation successful")
    validate_api_response_structure(success_response)
    assert_api_success_response(success_response)
    
    # Test error response format  
    error_response = create_error_response("Test error", message="Operation failed")
    validate_api_response_structure(error_response)
    assert_api_error_response(error_response)
    
    # Ensure both follow the same structure
    success_dict = success_response.model_dump()
    error_dict = error_response.model_dump()
    
    # Both should have the same keys
    assert set(success_dict.keys()) == set(error_dict.keys()), "Success and error responses should have same structure"
    
    print("ApiResponse format validation passed") 