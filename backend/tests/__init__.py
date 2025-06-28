# Tests package for the AI Agent Platform backend 

"""
Test utilities and shared fixtures for the AI Agent Platform backend tests.

This module provides common utilities for creating mock objects and test data
that are consistent with the ApiResponse format used throughout the system.
"""

from typing import Any, Dict, Optional, List, Union
from models import ApiResponse
import json


def create_mock_api_success_response(result: Any, message: str = "Operation successful", **metadata) -> ApiResponse:
    """
    Create a mock ApiResponse object for successful operations.
    
    Args:
        result: The result data to include in the response
        message: Optional success message
        **metadata: Additional metadata to include
    
    Returns:
        ApiResponse object with success=True
    """
    return ApiResponse(
        success=True,
        result=result,
        message=message,
        error=None,
        metadata=metadata if metadata else None
    )


def create_mock_api_error_response(error_message: str, message: str = "Operation failed", **metadata) -> ApiResponse:
    """
    Create a mock ApiResponse object for failed operations.
    
    Args:
        error_message: The error message to include
        message: Optional general message
        **metadata: Additional metadata to include
    
    Returns:
        ApiResponse object with success=False
    """
    return ApiResponse(
        success=False,
        result=None,
        message=message,
        error=error_message,
        metadata=metadata if metadata else None
    )


def create_mock_api_validation_error_response(validation_errors: list, message: str = "Validation failed") -> ApiResponse:
    """
    Create a mock ApiResponse object for validation errors.
    
    Args:
        validation_errors: List of validation error details
        message: Optional validation error message
    
    Returns:
        ApiResponse object with success=False and validation errors
    """
    return ApiResponse(
        success=False,
        result=None,
        message=message,
        error="Validation failed",
        metadata={
            "validation_errors": validation_errors,
            "error_type": "VALIDATION_ERROR"
        }
    )


# ApiResponse Validation Utilities
def validate_api_response_structure(response: Union[dict, ApiResponse]) -> bool:
    """
    Validate that a response has the correct ApiResponse structure.
    
    Args:
        response: The response object to validate (dict or ApiResponse)
    
    Returns:
        bool: True if the structure is valid
    
    Raises:
        AssertionError: If the structure is invalid
    """
    if isinstance(response, ApiResponse):
        response_dict = response.model_dump()
    else:
        response_dict = response
    
    # Check required fields
    assert "success" in response_dict, "Response missing 'success' field"
    assert isinstance(response_dict["success"], bool), "'success' field must be boolean"
    
    # Check optional fields exist (can be None)
    assert "result" in response_dict, "Response missing 'result' field"
    assert "message" in response_dict, "Response missing 'message' field"
    assert "error" in response_dict, "Response missing 'error' field"
    assert "metadata" in response_dict, "Response missing 'metadata' field"
    
    # Validate success/error consistency
    if response_dict["success"]:
        assert response_dict["error"] is None, "Successful response should not have error field set"
    else:
        assert response_dict["error"] is not None, "Failed response must have error field set"
        assert isinstance(response_dict["error"], str), "Error field must be a string"
    
    return True


def assert_api_success_response(response: Union[dict, ApiResponse], expected_result: Any = None) -> None:
    """
    Assert that a response is a successful ApiResponse with optional result validation.
    
    Args:
        response: The response to validate
        expected_result: Optional expected result data
    """
    validate_api_response_structure(response)
    
    if isinstance(response, ApiResponse):
        response_dict = response.model_dump()
    else:
        response_dict = response
    
    assert response_dict["success"] is True, f"Expected success=True, got {response_dict['success']}"
    assert response_dict["error"] is None, f"Expected error=None, got {response_dict['error']}"
    
    if expected_result is not None:
        assert response_dict["result"] == expected_result, f"Expected result {expected_result}, got {response_dict['result']}"


def assert_api_error_response(response: Union[dict, ApiResponse], expected_error: str = None) -> None:
    """
    Assert that a response is a failed ApiResponse with optional error validation.
    
    Args:
        response: The response to validate
        expected_error: Optional expected error message
    """
    validate_api_response_structure(response)
    
    if isinstance(response, ApiResponse):
        response_dict = response.model_dump()
    else:
        response_dict = response
    
    assert response_dict["success"] is False, f"Expected success=False, got {response_dict['success']}"
    assert response_dict["error"] is not None, "Expected error field to be set"
    assert response_dict["result"] is None, f"Expected result=None, got {response_dict['result']}"
    
    if expected_error is not None:
        assert expected_error in response_dict["error"], f"Expected error to contain '{expected_error}', got '{response_dict['error']}'"


def assert_api_validation_error_response(response: Union[dict, ApiResponse]) -> None:
    """
    Assert that a response is a validation error ApiResponse.
    
    Args:
        response: The response to validate
    """
    assert_api_error_response(response, "Validation failed")
    
    if isinstance(response, ApiResponse):
        response_dict = response.model_dump()
    else:
        response_dict = response
    
    assert response_dict.get("metadata") is not None, "Validation error should have metadata"
    assert "validation_errors" in response_dict["metadata"], "Validation error should have validation_errors in metadata"


def extract_api_result(response: Union[dict, ApiResponse]) -> Any:
    """
    Extract the result field from an ApiResponse.
    
    Args:
        response: The response to extract from
    
    Returns:
        The result data
    """
    if isinstance(response, ApiResponse):
        return response.result
    else:
        return response.get("result")


def is_api_response_format(data: Any) -> bool:
    """
    Check if data matches ApiResponse format without raising exceptions.
    
    Args:
        data: The data to check
    
    Returns:
        bool: True if data matches ApiResponse format
    """
    try:
        validate_api_response_structure(data)
        return True
    except (AssertionError, KeyError, TypeError):
        return False


# Enhanced Mock Data Generators
def create_mock_job_list_response(jobs: List[Dict] = None, total_count: int = None) -> ApiResponse:
    """Create a mock job list response with multiple jobs."""
    if jobs is None:
        jobs = [
            {**MOCK_JOB_DATA, "id": f"job-{i}", "title": f"Test Job {i}"}
            for i in range(1, 4)
        ]
    
    if total_count is None:
        total_count = len(jobs)
    
    return create_mock_api_success_response({
        "jobs": jobs,
        "total_count": total_count
    }, "Jobs retrieved successfully")


def create_mock_agent_list_response(agents: Dict = None, total_count: int = None) -> ApiResponse:
    """Create a mock agent list response with multiple agents."""
    if agents is None:
        agents = {
            "simple_prompt": {**MOCK_AGENT_DATA, "identifier": "simple_prompt", "name": "Simple Prompt Agent"},
            "web_scraping": {**MOCK_AGENT_DATA, "identifier": "web_scraping", "name": "Web Scraping Agent"},
        }
    
    if total_count is None:
        total_count = len(agents)
    
    return create_mock_api_success_response({
        "agents": agents,
        "total_count": total_count
    }, "Agents retrieved successfully")


def create_mock_health_check_response(status: str = "healthy", **health_data) -> ApiResponse:
    """Create a mock health check response."""
    health_info = {
        "status": status,
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        **health_data
    }
    return create_mock_api_success_response(health_info, "Health check completed")


def create_mock_schema_response(schema: Dict = None) -> ApiResponse:
    """Create a mock schema response."""
    if schema is None:
        schema = {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt text"},
                "max_tokens": {"type": "integer", "description": "Maximum tokens", "default": 100}
            },
            "required": ["prompt"]
        }
    
    return create_mock_api_success_response({
        "schema": schema
    }, "Schema retrieved successfully")


# Common mock data patterns for different types of operations
MOCK_JOB_DATA = {
    "id": "test-job-123",
    "title": "Test Job",
    "status": "completed",
    "agent_identifier": "simple_prompt",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:01:00Z"
}

MOCK_AGENT_DATA = {
    "name": "test_agent",
    "description": "Test agent for unit testing",
    "status": "available",
    "capabilities": ["text_processing", "analysis"],
    "version": "1.0.0"
}

MOCK_USER_DATA = {
    "id": "test-user-123",
    "email": "test@example.com",
    "name": "Test User"
}


def create_mock_job_response(**overrides) -> ApiResponse:
    """Create a mock job response with default job data."""
    job_data = {**MOCK_JOB_DATA, **overrides}
    return create_mock_api_success_response(job_data, "Job retrieved successfully")


def create_mock_agent_response(**overrides) -> ApiResponse:
    """Create a mock agent response with default agent data."""
    agent_data = {**MOCK_AGENT_DATA, **overrides}
    return create_mock_api_success_response(agent_data, "Agent information retrieved successfully")


def create_mock_user_response(**overrides) -> ApiResponse:
    """Create a mock user response with default user data."""
    user_data = {**MOCK_USER_DATA, **overrides}
    return create_mock_api_success_response({"user": user_data}, "User information retrieved successfully")


# Test Data Validation Helpers
def validate_job_data_structure(job_data: Dict) -> bool:
    """Validate that job data has the expected structure."""
    required_fields = ["id", "title", "status", "agent_identifier", "created_at"]
    for field in required_fields:
        assert field in job_data, f"Job data missing required field: {field}"
    return True


def validate_agent_data_structure(agent_data: Dict) -> bool:
    """Validate that agent data has the expected structure."""
    required_fields = ["name", "description", "status"]
    for field in required_fields:
        assert field in agent_data, f"Agent data missing required field: {field}"
    return True


# Performance Testing Utilities
def benchmark_api_response_serialization(response: ApiResponse, iterations: int = 1000) -> float:
    """
    Benchmark ApiResponse serialization performance.
    
    Args:
        response: The ApiResponse to benchmark
        iterations: Number of iterations to run
    
    Returns:
        Average time per serialization in milliseconds
    """
    import time
    
    start_time = time.time()
    for _ in range(iterations):
        json.dumps(response.model_dump())
    end_time = time.time()
    
    return ((end_time - start_time) / iterations) * 1000  # Convert to milliseconds


def benchmark_api_response_deserialization(response_dict: Dict, iterations: int = 1000) -> float:
    """
    Benchmark ApiResponse deserialization performance.
    
    Args:
        response_dict: The response dictionary to deserialize
        iterations: Number of iterations to run
    
    Returns:
        Average time per deserialization in milliseconds
    """
    import time
    
    start_time = time.time()
    for _ in range(iterations):
        ApiResponse(**response_dict)
    end_time = time.time()
    
    return ((end_time - start_time) / iterations) * 1000  # Convert to milliseconds 