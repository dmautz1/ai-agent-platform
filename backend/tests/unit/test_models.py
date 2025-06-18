"""
Unit tests for models.py - Generic Agent Framework

Tests the new generic models that support any agent type without hardcoded enums.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from models import (
    JobStatus, JobResponse, UserInfo, JobDataBase,
    JobCreateRequest, JobStatusUpdate, JobStats,
    HealthResponse
)


class TestEnums:
    """Test enumeration values"""

    def test_job_status_enum(self):
        """Test JobStatus enumeration values"""
        assert JobStatus.pending == "pending"
        assert JobStatus.running == "running" 
        assert JobStatus.completed == "completed"
        assert JobStatus.failed == "failed"


class TestBaseModels:
    """Test base model classes"""

    def test_base_response_default(self):
        """Test JobResponse with valid required fields"""
        response = JobResponse(
            id="test-id",
            status=JobStatus.completed,
            agent_identifier="test_agent",
            data={"test": "data"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        # Test the fields that actually exist in JobResponse
        assert response.id == "test-id"
        assert response.status == JobStatus.completed
        assert response.agent_identifier == "test_agent"
        assert response.data == {"test": "data"}
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)

    def test_base_response_custom(self):
        """Test JobResponse with custom values"""
        custom_time = datetime.now()
        response = JobResponse(
            id="test-id",
            status=JobStatus.failed,
            agent_identifier="test_agent",
            data={"test": "data"},
            created_at=custom_time,
            updated_at=custom_time,
            title="Custom Job",
            error_message="Custom error message"
        )
        # Test the fields that actually exist in JobResponse
        assert response.id == "test-id"
        assert response.status == JobStatus.failed
        assert response.agent_identifier == "test_agent"
        assert response.data == {"test": "data"}
        assert response.title == "Custom Job"
        assert response.error_message == "Custom error message"
        assert response.created_at == custom_time
        assert response.updated_at == custom_time


class TestUserModels:
    """Test user-related models"""

    def test_user_info_valid(self):
        """Test UserInfo with valid data"""
        user = UserInfo(
            id="test-user-id",
            email="test@example.com",
            metadata={"name": "Test User"},
            app_metadata={"roles": ["user"]},
            created_at="2024-01-01T00:00:00Z"
        )
        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        assert user.metadata == {"name": "Test User"}
        assert user.app_metadata == {"roles": ["user"]}

    def test_user_info_invalid_email(self):
        """Test UserInfo with invalid email"""
        with pytest.raises(ValidationError) as exc_info:
            UserInfo(
                id="test-user-id",
                email="invalid-email"
            )
        assert "value is not a valid email address" in str(exc_info.value)

    def test_user_info_minimal(self):
        """Test UserInfo with minimal required fields"""
        user = UserInfo(
            id="test-user-id",
            email="test@example.com"
        )
        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        assert user.metadata is None
        assert user.app_metadata is None


class TestJobDataModels:
    """Test generic job data models"""

    def test_job_data_base_valid(self):
        """Test JobDataBase with valid data"""
        job_data = JobDataBase(
            agent_identifier="simple_prompt"
        )
        assert job_data.agent_identifier == "simple_prompt"
        assert job_data.metadata is None

    def test_job_data_base_with_metadata(self):
        """Test JobDataBase with metadata"""
        job_data = JobDataBase(
            agent_identifier="simple_prompt",
            metadata={"source": "test", "priority": 5}
        )
        assert job_data.agent_identifier == "simple_prompt"
        assert job_data.metadata == {"source": "test", "priority": 5}


class TestJobRequestResponseModels:
    """Test job request and response models"""

    def test_job_create_request_valid(self):
        """Test JobCreateRequest with valid data"""
        request = JobCreateRequest(
            agent_identifier="simple_prompt",
            title="Test Job",
            data={
                "prompt": "Hello world",
                "max_tokens": 100
            },
            priority=5,
            tags=["test", "prompt"]
        )
        assert request.agent_identifier == "simple_prompt"
        assert request.title == "Test Job"
        assert request.data == {"prompt": "Hello world", "max_tokens": 100}
        assert request.priority == 5
        assert request.tags == ["test", "prompt"]

    def test_job_create_request_invalid_priority(self):
        """Test JobCreateRequest with invalid priority"""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(
                agent_identifier="simple_prompt",
                title="Test Job",
                data={"prompt": "test"},
                priority=15  # Priority > 10
            )
        assert "less than or equal to 10" in str(exc_info.value)

    def test_job_create_request_minimal(self):
        """Test JobCreateRequest with minimal data"""
        request = JobCreateRequest(
            agent_identifier="simple_prompt",
            title="Test Job",
            data={"prompt": "test"}
        )
        assert request.agent_identifier == "simple_prompt"
        assert request.title == "Test Job"
        assert request.data == {"prompt": "test"}
        assert request.priority == 0  # default
        assert request.tags is None

    def test_job_response_valid(self):
        """Test JobResponse with valid data"""
        response = JobResponse(
            id="job_123",
            status=JobStatus.completed,
            agent_identifier="simple_prompt",
            data={"prompt": "Hello", "max_tokens": 100},
            result="Hello! How can I help you today?",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert response.id == "job_123"
        assert response.status == JobStatus.completed
        assert response.agent_identifier == "simple_prompt"
        assert response.result == "Hello! How can I help you today?"
        assert response.error_message is None


class TestJobUpdateModels:
    """Test job update models"""

    def test_job_status_update_valid(self):
        """Test JobStatusUpdate with valid data"""
        update = JobStatusUpdate(
            status=JobStatus.completed,
            result="Task completed successfully"
        )
        assert update.status == JobStatus.completed
        assert update.result == "Task completed successfully"
        assert update.error_message is None

    def test_job_status_update_completed_without_result(self):
        """Test JobStatusUpdate completed status requires result"""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusUpdate(status=JobStatus.completed)
        assert "Result is required when status is completed" in str(exc_info.value)

    def test_job_status_update_failed_without_error(self):
        """Test JobStatusUpdate failed status requires error message"""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusUpdate(status=JobStatus.failed)
        assert "Error message is required when status is failed" in str(exc_info.value)

    def test_job_status_update_failed_with_error(self):
        """Test JobStatusUpdate with failed status and error"""
        update = JobStatusUpdate(
            status=JobStatus.failed,
            error_message="Processing failed"
        )
        assert update.status == JobStatus.failed
        assert update.error_message == "Processing failed"


class TestStatisticsModels:
    """Test statistics models"""

    def test_job_stats_valid(self):
        """Test JobStats with valid data"""
        stats = JobStats(
            total_jobs=100,
            pending_jobs=5,
            running_jobs=2,
            completed_jobs=85,
            failed_jobs=8,
            success_rate=91.4
        )
        assert stats.total_jobs == 100
        assert stats.pending_jobs == 5
        assert stats.running_jobs == 2
        assert stats.completed_jobs == 85
        assert stats.failed_jobs == 8
        assert stats.success_rate == 91.4


class TestHealthModels:
    """Test health check models"""

    def test_health_response_valid(self):
        """Test HealthResponse with valid data"""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            environment="development",
            cors_origins=3
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.environment == "development"
        assert response.cors_origins == 3
        assert isinstance(response.timestamp, datetime)


class TestModelSerialization:
    """Test model serialization and validation"""

    def test_job_create_request_serialization(self):
        """Test JobCreateRequest JSON serialization"""
        request = JobCreateRequest(
            agent_identifier="simple_prompt",
            title="Test Job",
            data={"prompt": "Hello", "max_tokens": 500},
            priority=8,
            tags=["important", "test"]
        )
        
        json_data = request.model_dump()
        assert json_data["agent_identifier"] == "simple_prompt"
        assert json_data["title"] == "Test Job"
        assert json_data["data"]["prompt"] == "Hello"
        assert json_data["priority"] == 8
        assert "important" in json_data["tags"]

    def test_job_response_serialization(self):
        """Test JobResponse JSON serialization"""
        now = datetime.now()
        response = JobResponse(
            id="job_456",
            status=JobStatus.completed,
            agent_identifier="simple_prompt",
            data={"prompt": "Test"},
            result="Test completed",
            created_at=now,
            updated_at=now
        )
        
        json_data = response.model_dump()
        assert json_data["id"] == "job_456"
        assert json_data["status"] == "completed"
        assert json_data["agent_identifier"] == "simple_prompt"
        assert json_data["result"] == "Test completed"


class TestModelValidationEdgeCases:
    """Test edge cases and validation boundaries"""

    def test_empty_agent_identifier(self):
        """Test validation with empty agent identifier"""
        with pytest.raises(ValidationError):
            JobCreateRequest(
                agent_identifier="",
                data={"prompt": "test"}
            )

    def test_large_job_data(self):
        """Test handling of large job data"""
        large_prompt = "x" * 10000  # 10KB prompt
        request = JobCreateRequest(
            agent_identifier="simple_prompt",
            title="Large Job Test",
            data={"prompt": large_prompt, "max_tokens": 1000}
        )
        assert len(request.data["prompt"]) == 10000

    def test_minimal_job_data(self):
        """Test minimal valid job data"""
        request = JobCreateRequest(
            agent_identifier="test_agent",
            title="Minimal Test",
            data={}  # Empty data dict should be valid
        )
        assert request.data == {}
        assert request.priority == 0
        assert request.tags is None

    def test_job_status_update_running_status(self):
        """Test JobStatusUpdate with running status (no result/error required)"""
        update = JobStatusUpdate(status=JobStatus.running)
        assert update.status == JobStatus.running
        assert update.result is None
        assert update.error_message is None 