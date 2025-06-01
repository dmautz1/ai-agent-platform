"""
Integration tests for Supabase database operations.

These tests verify actual database connectivity and data persistence.
They require a real Supabase instance configured in the environment.
"""

import pytest
import asyncio
import uuid
import time
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from database import DatabaseOperations, get_database_operations, check_database_health
from config.environment import get_settings, validate_required_settings
from logging_system import get_logger

logger = get_logger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def verify_environment():
    """Verify that required environment variables are set for integration tests."""
    try:
        validate_required_settings()
        settings = get_settings()
        
        # Verify we're not in production (safety check)
        if settings.is_production():
            pytest.skip("Integration tests should not run against production database")
        
        # Test basic connectivity
        health = await check_database_health()
        if health["status"] != "healthy":
            pytest.skip(f"Database is not healthy: {health.get('error', 'Unknown error')}")
            
        logger.info("Environment verification passed for integration tests")
        
    except Exception as e:
        pytest.skip(f"Environment setup failed: {e}")

@pytest.fixture
async def db_operations():
    """Get database operations instance."""
    return get_database_operations()

@pytest.fixture
async def test_user_id():
    """Generate a test user ID."""
    return str(uuid.uuid4())

@pytest.fixture
async def cleanup_test_jobs(db_operations: DatabaseOperations):
    """Clean up test jobs after each test."""
    test_job_ids = []
    
    def add_job_id(job_id: str):
        test_job_ids.append(job_id)
    
    yield add_job_id
    
    # Cleanup after test
    for job_id in test_job_ids:
        try:
            await db_operations.delete_job(job_id)
        except Exception as e:
            logger.warning(f"Failed to cleanup test job {job_id}: {e}")

class TestSupabaseConnectivity:
    """Test basic Supabase connectivity and health checks."""
    
    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test that database health check returns healthy status."""
        health = await check_database_health()
        
        assert health["status"] == "healthy"
        assert "connection_time_ms" in health
        assert "timestamp" in health
        assert health["connection_time_ms"] > 0
        
        logger.info(f"Database health check passed in {health['connection_time_ms']}ms")
    
    @pytest.mark.asyncio
    async def test_database_operations_initialization(self, db_operations: DatabaseOperations):
        """Test that database operations can be initialized."""
        assert db_operations is not None
        assert db_operations.client is not None
        
        # Test that we get the same instance (singleton pattern)
        db_ops2 = get_database_operations()
        assert db_operations is db_ops2

class TestJobCRUDOperations:
    """Test Create, Read, Update, Delete operations for jobs."""
    
    @pytest.mark.asyncio
    async def test_create_job_success(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test successful job creation with all required fields."""
        job_data = {
            "user_id": test_user_id,
            "type": "text_processing",
            "status": "pending",
            "data": {
                "input_text": "Test input for processing",
                "operation": "summarize"
            }
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        assert created_job is not None
        assert "id" in created_job
        assert created_job["user_id"] == test_user_id
        assert created_job["type"] == "text_processing"
        assert created_job["status"] == "pending"
        assert created_job["data"] == job_data["data"]
        assert "created_at" in created_job
        assert "updated_at" in created_job
        
        logger.info(f"Successfully created job {created_job['id']}")
    
    @pytest.mark.asyncio
    async def test_create_job_minimal_data(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test job creation with minimal required data."""
        job_data = {
            "status": "pending"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        assert created_job is not None
        assert "id" in created_job
        assert created_job["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_job_success(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test successful job retrieval."""
        # Create a test job first
        job_data = {
            "user_id": test_user_id,
            "type": "web_scraping",
            "status": "pending",
            "data": {"url": "https://example.com"}
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Retrieve the job
        retrieved_job = await db_operations.get_job(created_job["id"])
        
        assert retrieved_job is not None
        assert retrieved_job["id"] == created_job["id"]
        assert retrieved_job["user_id"] == test_user_id
        assert retrieved_job["type"] == "web_scraping"
        assert retrieved_job["data"] == job_data["data"]
    
    @pytest.mark.asyncio
    async def test_get_job_with_user_filter(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test job retrieval with user ID filtering."""
        other_user_id = str(uuid.uuid4())
        
        # Create a job for the test user
        job_data = {
            "user_id": test_user_id,
            "type": "summarization",
            "status": "pending"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Should retrieve job when correct user ID is provided
        retrieved_job = await db_operations.get_job(created_job["id"], test_user_id)
        assert retrieved_job is not None
        assert retrieved_job["id"] == created_job["id"]
        
        # Should return None when wrong user ID is provided
        retrieved_job = await db_operations.get_job(created_job["id"], other_user_id)
        assert retrieved_job is None
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, db_operations: DatabaseOperations):
        """Test job retrieval when job doesn't exist."""
        nonexistent_id = str(uuid.uuid4())
        
        retrieved_job = await db_operations.get_job(nonexistent_id)
        assert retrieved_job is None
    
    @pytest.mark.asyncio
    async def test_get_user_jobs(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test retrieving all jobs for a specific user."""
        # Create multiple jobs for the user
        job_types = ["text_processing", "web_scraping", "summarization"]
        created_jobs = []
        
        for job_type in job_types:
            job_data = {
                "user_id": test_user_id,
                "type": job_type,
                "status": "pending"
            }
            created_job = await db_operations.create_job(job_data)
            created_jobs.append(created_job)
            cleanup_test_jobs(created_job["id"])
        
        # Retrieve user jobs
        user_jobs = await db_operations.get_user_jobs(test_user_id)
        
        assert len(user_jobs) >= len(job_types)
        
        # Verify all created jobs are in the results
        created_job_ids = {job["id"] for job in created_jobs}
        retrieved_job_ids = {job["id"] for job in user_jobs}
        
        assert created_job_ids.issubset(retrieved_job_ids)
        
        # Verify all jobs belong to the correct user
        for job in user_jobs:
            if job["user_id"]:  # Some test jobs might not have user_id
                assert job["user_id"] == test_user_id
    
    @pytest.mark.asyncio
    async def test_get_user_jobs_pagination(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test pagination in user jobs retrieval."""
        # Create multiple jobs
        num_jobs = 5
        created_jobs = []
        
        for i in range(num_jobs):
            job_data = {
                "user_id": test_user_id,
                "type": f"test_job_{i}",
                "status": "pending"
            }
            created_job = await db_operations.create_job(job_data)
            created_jobs.append(created_job)
            cleanup_test_jobs(created_job["id"])
        
        # Test pagination
        page1 = await db_operations.get_user_jobs(test_user_id, limit=3, offset=0)
        page2 = await db_operations.get_user_jobs(test_user_id, limit=3, offset=3)
        
        assert len(page1) <= 3
        assert len(page2) <= 3
        
        # Verify no overlap between pages
        page1_ids = {job["id"] for job in page1}
        page2_ids = {job["id"] for job in page2}
        assert page1_ids.isdisjoint(page2_ids)

class TestJobStatusUpdates:
    """Test job status update operations."""
    
    @pytest.mark.asyncio
    async def test_update_job_status_to_running(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test updating job status to running."""
        # Create a pending job
        job_data = {
            "user_id": test_user_id,
            "type": "text_processing",
            "status": "pending"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Update status to running
        updated_job = await db_operations.update_job_status(created_job["id"], "running")
        
        assert updated_job["status"] == "running"
        assert updated_job["updated_at"] != created_job["updated_at"]
    
    @pytest.mark.asyncio
    async def test_update_job_status_to_completed(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test updating job status to completed with result."""
        # Create a running job
        job_data = {
            "user_id": test_user_id,
            "type": "summarization",
            "status": "running"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Update status to completed with result
        result_data = {
            "summary": "This is a test summary",
            "word_count": 25,
            "processing_time": 2.5
        }
        
        updated_job = await db_operations.update_job_status(
            created_job["id"], 
            "completed", 
            result=result_data
        )
        
        assert updated_job["status"] == "completed"
        assert updated_job["result"] == result_data
        assert "completed_at" in updated_job
        assert updated_job["completed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_update_job_status_to_failed(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test updating job status to failed with error message."""
        # Create a running job
        job_data = {
            "user_id": test_user_id,
            "type": "web_scraping",
            "status": "running"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Update status to failed with error
        error_message = "Connection timeout after 30 seconds"
        
        updated_job = await db_operations.update_job_status(
            created_job["id"], 
            "failed", 
            error_message=error_message
        )
        
        assert updated_job["status"] == "failed"
        assert updated_job["error_message"] == error_message
        assert "failed_at" in updated_job
        assert updated_job["failed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_job_status(self, db_operations: DatabaseOperations):
        """Test updating status of non-existent job."""
        nonexistent_id = str(uuid.uuid4())
        
        with pytest.raises(Exception, match="not found"):
            await db_operations.update_job_status(nonexistent_id, "completed")

class TestJobDeletion:
    """Test job deletion operations."""
    
    @pytest.mark.asyncio
    async def test_delete_job_success(self, db_operations: DatabaseOperations, test_user_id: str):
        """Test successful job deletion."""
        # Create a job
        job_data = {
            "user_id": test_user_id,
            "type": "text_processing",
            "status": "completed"
        }
        
        created_job = await db_operations.create_job(job_data)
        
        # Delete the job
        deleted = await db_operations.delete_job(created_job["id"])
        assert deleted is True
        
        # Verify job is deleted
        retrieved_job = await db_operations.get_job(created_job["id"])
        assert retrieved_job is None
    
    @pytest.mark.asyncio
    async def test_delete_job_with_user_filter(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test job deletion with user ID filtering."""
        other_user_id = str(uuid.uuid4())
        
        # Create a job
        job_data = {
            "user_id": test_user_id,
            "type": "summarization",
            "status": "completed"
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])  # Backup cleanup
        
        # Try to delete with wrong user ID
        deleted = await db_operations.delete_job(created_job["id"], other_user_id)
        assert deleted is False
        
        # Verify job still exists
        retrieved_job = await db_operations.get_job(created_job["id"])
        assert retrieved_job is not None
        
        # Delete with correct user ID
        deleted = await db_operations.delete_job(created_job["id"], test_user_id)
        assert deleted is True
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_job(self, db_operations: DatabaseOperations):
        """Test deleting non-existent job."""
        nonexistent_id = str(uuid.uuid4())
        
        deleted = await db_operations.delete_job(nonexistent_id)
        assert deleted is False

class TestJobStatistics:
    """Test job statistics operations."""
    
    @pytest.mark.asyncio
    async def test_get_job_statistics(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test retrieving job statistics."""
        # Create jobs with different statuses
        test_jobs = [
            {"status": "pending", "type": "text_processing"},
            {"status": "running", "type": "web_scraping"}, 
            {"status": "completed", "type": "summarization"},
            {"status": "completed", "type": "text_processing"},
            {"status": "failed", "type": "web_scraping"}
        ]
        
        created_jobs = []
        for job_data in test_jobs:
            job_data["user_id"] = test_user_id
            created_job = await db_operations.create_job(job_data)
            created_jobs.append(created_job)
            cleanup_test_jobs(created_job["id"])
        
        # Get statistics
        stats = await db_operations.get_job_statistics(test_user_id)
        
        assert "total_jobs" in stats
        assert "pending_jobs" in stats
        assert "running_jobs" in stats
        assert "completed_jobs" in stats
        assert "failed_jobs" in stats
        assert "status_breakdown" in stats
        
        assert stats["total_jobs"] >= len(test_jobs)
        assert stats["pending_jobs"] >= 1
        assert stats["running_jobs"] >= 1
        assert stats["completed_jobs"] >= 2
        assert stats["failed_jobs"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_global_job_statistics(self, db_operations: DatabaseOperations):
        """Test retrieving global job statistics (all users)."""
        stats = await db_operations.get_job_statistics()
        
        assert "total_jobs" in stats
        assert "status_breakdown" in stats
        assert isinstance(stats["total_jobs"], int)
        assert stats["total_jobs"] >= 0

class TestDataPersistence:
    """Test data persistence and consistency."""
    
    @pytest.mark.asyncio
    async def test_job_data_persistence_complex_json(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test persistence of complex JSON data."""
        complex_data = {
            "nested_object": {
                "settings": {
                    "timeout": 30,
                    "retries": 3
                },
                "parameters": ["param1", "param2", "param3"]
            },
            "array_data": [1, 2, 3, 4, 5],
            "mixed_types": {
                "string": "test",
                "number": 42,
                "boolean": True,
                "null_value": None
            }
        }
        
        job_data = {
            "user_id": test_user_id,
            "type": "complex_processing",
            "status": "pending",
            "data": complex_data
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        # Retrieve and verify complex data persistence
        retrieved_job = await db_operations.get_job(created_job["id"])
        
        assert retrieved_job["data"] == complex_data
        assert retrieved_job["data"]["nested_object"]["settings"]["timeout"] == 30
        assert retrieved_job["data"]["mixed_types"]["boolean"] is True
        assert retrieved_job["data"]["mixed_types"]["null_value"] is None
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test persistence of Unicode and special characters."""
        special_data = {
            "unicode_text": "Hello 世界! 🌍 Testing émojis and spéciàl chars",
            "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "multiline": "Line 1\nLine 2\nLine 3",
            "json_string": '{"nested": "json", "array": [1, 2, 3]}'
        }
        
        job_data = {
            "user_id": test_user_id,
            "type": "unicode_test",
            "status": "pending",
            "data": special_data
        }
        
        created_job = await db_operations.create_job(job_data)
        cleanup_test_jobs(created_job["id"])
        
        retrieved_job = await db_operations.get_job(created_job["id"])
        
        assert retrieved_job["data"] == special_data
        assert "🌍" in retrieved_job["data"]["unicode_text"]
        assert "世界" in retrieved_job["data"]["unicode_text"]

class TestPerformanceAndLimits:
    """Test performance characteristics and limits."""
    
    @pytest.mark.asyncio
    async def test_large_job_data_persistence(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test persistence of large job data."""
        # Create large data (but reasonable for testing)
        large_text = "x" * 10000  # 10KB of text
        large_array = list(range(1000))  # Array with 1000 elements
        
        large_data = {
            "large_text": large_text,
            "large_array": large_array,
            "repeated_data": {f"key_{i}": f"value_{i}" for i in range(100)}
        }
        
        job_data = {
            "user_id": test_user_id,
            "type": "large_data_test",
            "status": "pending",
            "data": large_data
        }
        
        start_time = time.time()
        created_job = await db_operations.create_job(job_data)
        create_time = time.time() - start_time
        cleanup_test_jobs(created_job["id"])
        
        start_time = time.time()
        retrieved_job = await db_operations.get_job(created_job["id"])
        retrieve_time = time.time() - start_time
        
        assert retrieved_job["data"] == large_data
        assert len(retrieved_job["data"]["large_text"]) == 10000
        assert len(retrieved_job["data"]["large_array"]) == 1000
        
        # Log performance metrics
        logger.info(f"Large data create time: {create_time:.3f}s, retrieve time: {retrieve_time:.3f}s")
        
        # Basic performance assertion (should complete within reasonable time)
        assert create_time < 5.0  # Should create within 5 seconds
        assert retrieve_time < 5.0  # Should retrieve within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_job_operations(self, db_operations: DatabaseOperations, test_user_id: str, cleanup_test_jobs):
        """Test concurrent job creation and updates."""
        # Create multiple jobs concurrently
        async def create_test_job(index: int):
            job_data = {
                "user_id": test_user_id,
                "type": f"concurrent_test_{index}",
                "status": "pending",
                "data": {"index": index}
            }
            return await db_operations.create_job(job_data)
        
        # Create 10 jobs concurrently
        tasks = [create_test_job(i) for i in range(10)]
        created_jobs = await asyncio.gather(*tasks)
        
        # Clean up all created jobs
        for job in created_jobs:
            cleanup_test_jobs(job["id"])
        
        assert len(created_jobs) == 10
        
        # Verify all jobs were created with unique IDs
        job_ids = {job["id"] for job in created_jobs}
        assert len(job_ids) == 10
        
        # Test concurrent status updates
        async def update_job_status(job):
            return await db_operations.update_job_status(job["id"], "completed")
        
        update_tasks = [update_job_status(job) for job in created_jobs]
        updated_jobs = await asyncio.gather(*update_tasks)
        
        assert len(updated_jobs) == 10
        for job in updated_jobs:
            assert job["status"] == "completed"

if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        test_category = sys.argv[1]
        pytest.main([f"-v", f"test_{test_category}"])
    else:
        pytest.main(["-v", __file__]) 