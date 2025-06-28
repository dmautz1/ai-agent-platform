"""
Performance tests for ApiResponse serialization and deserialization.

These tests ensure that the ApiResponse pattern doesn't introduce significant
performance overhead compared to direct JSON responses.
"""

import pytest
import time
import json
import statistics
from typing import Dict, List, Any
from models import ApiResponse
from utils.responses import create_success_response, create_error_response
from tests import (
    benchmark_api_response_serialization,
    benchmark_api_response_deserialization,
    create_mock_api_success_response,
    create_mock_api_error_response,
    MOCK_JOB_DATA,
    MOCK_AGENT_DATA
)


class TestApiResponsePerformance:
    """Performance tests for ApiResponse operations."""

    def test_simple_response_serialization_performance(self):
        """Test serialization performance of simple ApiResponse objects."""
        # Create a simple success response
        simple_response = create_success_response("test result", "Operation successful")
        
        # Benchmark serialization
        avg_time = benchmark_api_response_serialization(simple_response, iterations=1000)
        
        # Should serialize quickly (less than 0.1ms per operation)
        assert avg_time < 0.1, f"Simple response serialization too slow: {avg_time}ms"
        
        print(f"Simple response serialization: {avg_time:.4f}ms per operation")

    def test_complex_response_serialization_performance(self):
        """Test serialization performance of complex ApiResponse objects with large data."""
        # Create a complex response with large data
        large_job_list = [
            {**MOCK_JOB_DATA, "id": f"job-{i}", "title": f"Test Job {i}"}
            for i in range(100)
        ]
        
        complex_response = create_success_response({
            "jobs": large_job_list,
            "total_count": len(large_job_list),
            "metadata": {
                "query_time": 0.045,
                "filters_applied": ["status", "priority"],
                "sort_order": "created_at_desc"
            }
        }, "Jobs retrieved successfully")
        
        # Benchmark serialization
        avg_time = benchmark_api_response_serialization(complex_response, iterations=100)
        
        # Should still serialize reasonably quickly (less than 5ms per operation)
        assert avg_time < 5.0, f"Complex response serialization too slow: {avg_time}ms"
        
        print(f"Complex response serialization: {avg_time:.4f}ms per operation")

    def test_error_response_serialization_performance(self):
        """Test serialization performance of error ApiResponse objects."""
        # Create an error response with detailed error information
        error_response = create_error_response(
            "Validation failed",
            message="Operation failed",
            metadata={
                "validation_errors": [
                    {"field": "prompt", "error": "Field is required"},
                    {"field": "max_tokens", "error": "Must be a positive integer"}
                ],
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        
        # Benchmark serialization
        avg_time = benchmark_api_response_serialization(error_response, iterations=1000)
        
        # Should serialize quickly (less than 0.2ms per operation)
        assert avg_time < 0.2, f"Error response serialization too slow: {avg_time}ms"
        
        print(f"Error response serialization: {avg_time:.4f}ms per operation")

    def test_response_deserialization_performance(self):
        """Test deserialization performance of ApiResponse objects."""
        # Create test responses
        responses = [
            create_success_response(MOCK_JOB_DATA, "Job retrieved"),
            create_success_response({"agents": [MOCK_AGENT_DATA] * 50}, "Agents retrieved"),
            create_error_response("Test error", message="Test operation failed", metadata={"error_code": "TEST_ERROR"})
        ]
        
        # Convert to dictionaries for deserialization testing
        response_dicts = [response.model_dump() for response in responses]
        
        # Benchmark deserialization for each type
        for i, response_dict in enumerate(response_dicts):
            avg_time = benchmark_api_response_deserialization(response_dict, iterations=1000)
            
            # Should deserialize quickly (less than 0.5ms per operation)
            assert avg_time < 0.5, f"Response {i} deserialization too slow: {avg_time}ms"
            
            print(f"Response {i} deserialization: {avg_time:.4f}ms per operation")

    def test_pydantic_model_creation_performance(self):
        """Test performance of creating ApiResponse Pydantic models."""
        # Test data for model creation
        test_data = {
            "success": True,
            "result": {"test": "data", "items": list(range(100))},
            "message": "Test successful",
            "error": None,
            "metadata": {"timestamp": "2024-01-01T00:00:00Z"}
        }
        
        # Benchmark model creation
        start_time = time.perf_counter()
        for _ in range(1000):
            ApiResponse(**test_data)
        end_time = time.perf_counter()
        
        avg_time = ((end_time - start_time) / 1000) * 1000  # Convert to milliseconds
        
        # Should create models quickly (less than 0.1ms per operation)
        assert avg_time < 0.1, f"Pydantic model creation too slow: {avg_time}ms"
        
        print(f"Pydantic model creation: {avg_time:.4f}ms per operation")

    def test_model_validation_performance(self):
        """Test performance of Pydantic model validation."""
        # Test various validation scenarios
        test_cases = [
            # Valid data
            {
                "success": True,
                "result": {"test": "data"},
                "message": "Success",
                "error": None,
                "metadata": None
            },
            # Invalid data (should still validate quickly before raising error)
            {
                "success": "not_boolean",  # Invalid type
                "result": {"test": "data"},
                "message": "Success",
                "error": None,
                "metadata": None
            }
        ]
        
        for i, test_data in enumerate(test_cases):
            start_time = time.perf_counter()
            
            for _ in range(1000):
                try:
                    ApiResponse(**test_data)
                except Exception:
                    # Expected for invalid data
                    pass
            
            end_time = time.perf_counter()
            avg_time = ((end_time - start_time) / 1000) * 1000
            
            # Should validate quickly (less than 0.2ms per operation)
            assert avg_time < 0.2, f"Model validation case {i} too slow: {avg_time}ms"
            
            print(f"Model validation case {i}: {avg_time:.4f}ms per operation")

    def test_helper_functions_performance(self):
        """Test performance of ApiResponse helper functions."""
        # Test create_success_response performance
        start_time = time.perf_counter()
        for i in range(1000):
            create_success_response(f"result_{i}", f"Message {i}")
        end_time = time.perf_counter()
        
        success_avg_time = ((end_time - start_time) / 1000) * 1000
        assert success_avg_time < 0.1, f"create_success_response too slow: {success_avg_time}ms"
        
        # Test create_error_response performance
        start_time = time.perf_counter()
        for i in range(1000):
            create_error_response(f"error_{i}", message=f"Error message {i}", metadata={"code": i})
        end_time = time.perf_counter()
        
        error_avg_time = ((end_time - start_time) / 1000) * 1000
        assert error_avg_time < 0.1, f"create_error_response too slow: {error_avg_time}ms"
        
        print(f"create_success_response: {success_avg_time:.4f}ms per operation")
        print(f"create_error_response: {error_avg_time:.4f}ms per operation")

    def test_memory_usage_estimation(self):
        """Test memory usage of ApiResponse objects."""
        import sys
        
        # Create different types of responses
        simple_response = create_success_response("simple", "Simple response")
        complex_response = create_success_response({
            "data": list(range(1000)),
            "metadata": {"key": "value"} 
        }, "Complex response")
        
        # Get approximate memory usage (this is rough estimation)
        simple_size = sys.getsizeof(simple_response.model_dump_json())
        complex_size = sys.getsizeof(complex_response.model_dump_json())
        
        print(f"Simple response approximate size: {simple_size} bytes")
        print(f"Complex response approximate size: {complex_size} bytes")
        
        # Ensure responses aren't unreasonably large
        assert simple_size < 1000, f"Simple response too large: {simple_size} bytes"
        assert complex_size < 50000, f"Complex response too large: {complex_size} bytes"

    def test_concurrent_serialization_performance(self):
        """Test serialization performance under concurrent load."""
        import threading
        import queue
        
        # Create test responses
        responses = [
            create_success_response({"data": i}, f"Response {i}")
            for i in range(100)
        ]
        
        results = queue.Queue()
        
        def serialize_responses():
            """Serialize responses and measure time."""
            start_time = time.perf_counter()
            for response in responses:
                json.dumps(response.model_dump())
            end_time = time.perf_counter()
            results.put(end_time - start_time)
        
        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=serialize_responses)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        times = []
        while not results.empty():
            times.append(results.get())
        
        avg_time = statistics.mean(times) * 1000  # Convert to milliseconds
        max_time = max(times) * 1000
        
        print(f"Concurrent serialization average: {avg_time:.4f}ms")
        print(f"Concurrent serialization max: {max_time:.4f}ms")
        
        # Should handle concurrent load reasonably well
        assert avg_time < 100, f"Concurrent serialization too slow: {avg_time}ms"
        assert max_time < 200, f"Concurrent serialization max too slow: {max_time}ms"

    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        # Create a response with a large dataset (simulating a large job list)
        large_dataset = [
            {
                **MOCK_JOB_DATA,
                "id": f"job-{i:06d}",
                "title": f"Large Dataset Job {i}",
                "data": {
                    "agent_identifier": "test_agent",
                    "parameters": {f"param_{j}": f"value_{j}" for j in range(10)}
                },
                "result": {
                    "output": f"Result for job {i}",
                    "metrics": {f"metric_{k}": k * i for k in range(5)}
                }
            }
            for i in range(1000)  # 1000 jobs
        ]
        
        large_response = create_success_response({
            "jobs": large_dataset,
            "total_count": len(large_dataset),
            "pagination": {
                "page": 1,
                "per_page": 1000,
                "total_pages": 1
            }
        }, "Large dataset retrieved successfully")
        
        # Test serialization performance
        start_time = time.perf_counter()
        json_str = json.dumps(large_response.model_dump())
        end_time = time.perf_counter()
        
        serialization_time = (end_time - start_time) * 1000
        
        # Test deserialization performance
        start_time = time.perf_counter()
        parsed_data = json.loads(json_str)
        ApiResponse(**parsed_data)
        end_time = time.perf_counter()
        
        deserialization_time = (end_time - start_time) * 1000
        
        print(f"Large dataset serialization: {serialization_time:.4f}ms")
        print(f"Large dataset deserialization: {deserialization_time:.4f}ms")
        print(f"Large dataset JSON size: {len(json_str)} bytes")
        
        # Should handle large datasets within reasonable time
        assert serialization_time < 100, f"Large dataset serialization too slow: {serialization_time}ms"
        assert deserialization_time < 100, f"Large dataset deserialization too slow: {deserialization_time}ms"

    def test_performance_regression_baseline(self):
        """Establish performance baselines for regression testing."""
        # This test establishes baseline performance metrics
        # In CI/CD, these can be compared against previous runs
        
        test_cases = [
            ("simple_success", create_success_response("test", "message")),
            ("simple_error", create_error_response("test error")),
            ("job_response", create_success_response(MOCK_JOB_DATA, "Job retrieved")),
            ("agent_list", create_success_response({"agents": [MOCK_AGENT_DATA] * 10}, "Agents retrieved"))
        ]
        
        baselines = {}
        
        for name, response in test_cases:
            # Measure serialization
            start_time = time.perf_counter()
            for _ in range(1000):
                json.dumps(response.model_dump())
            end_time = time.perf_counter()
            
            serialization_time = ((end_time - start_time) / 1000) * 1000
            baselines[f"{name}_serialization"] = serialization_time
            
            # Measure model creation
            response_dict = response.model_dump()
            start_time = time.perf_counter()
            for _ in range(1000):
                ApiResponse(**response_dict)
            end_time = time.perf_counter()
            
            creation_time = ((end_time - start_time) / 1000) * 1000
            baselines[f"{name}_creation"] = creation_time
        
        # Log baselines for CI/CD tracking
        print("Performance Baselines:")
        for metric, time_ms in baselines.items():
            print(f"  {metric}: {time_ms:.4f}ms")
        
        # Ensure all operations are reasonably fast
        for metric, time_ms in baselines.items():
            assert time_ms < 1.0, f"Performance baseline too slow for {metric}: {time_ms}ms" 