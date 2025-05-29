"""
Unit tests for Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models import (
    JobStatus, JobType, AgentType,
    BaseResponse, ErrorResponse, UserInfo,
    JobDataBase, TextProcessingJobData, TextSummarizationJobData, 
    WebScrapingJobData, CustomJobData,
    JobCreateRequest, JobResponse, JobListResponse, JobCreateResponse,
    JobDetailResponse, JobStatusUpdate, JobStats, JobStatsResponse,
    AuthResponse, HealthResponse
)

class TestEnums:
    """Test enumeration types"""

    def test_job_status_enum(self):
        """Test JobStatus enumeration values"""
        assert JobStatus.pending == "pending"
        assert JobStatus.running == "running" 
        assert JobStatus.completed == "completed"
        assert JobStatus.failed == "failed"

    def test_job_type_enum(self):
        """Test JobType enumeration values"""
        assert JobType.text_processing == "text_processing"
        assert JobType.text_summarization == "text_summarization"
        assert JobType.web_scraping == "web_scraping"
        assert JobType.custom == "custom"

    def test_agent_type_enum(self):
        """Test AgentType enumeration values"""
        assert AgentType.google_adk == "google_adk"
        assert AgentType.openai == "openai"
        assert AgentType.custom == "custom"

class TestBaseModels:
    """Test base model classes"""

    def test_base_response_default(self):
        """Test BaseResponse with default values"""
        response = BaseResponse()
        assert response.success is True
        assert response.message == "Operation successful"
        assert isinstance(response.timestamp, datetime)

    def test_base_response_custom(self):
        """Test BaseResponse with custom values"""
        custom_time = datetime.now()
        response = BaseResponse(
            success=False,
            message="Custom message",
            timestamp=custom_time
        )
        assert response.success is False
        assert response.message == "Custom message"
        assert response.timestamp == custom_time

    def test_error_response(self):
        """Test ErrorResponse model"""
        error = ErrorResponse(
            message="Error occurred",
            error_code="ERR001",
            details={"field": "value"}
        )
        assert error.success is False
        assert error.message == "Error occurred"
        assert error.error_code == "ERR001"
        assert error.details == {"field": "value"}

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
    """Test job data models"""

    def test_text_processing_job_data_valid(self):
        """Test TextProcessingJobData with valid data"""
        job_data = TextProcessingJobData(
            text="Sample text to process",
            operation="analyze_sentiment",
            parameters={"language": "en"}
        )
        assert job_data.job_type == JobType.text_processing
        assert job_data.agent_type == AgentType.google_adk
        assert job_data.text == "Sample text to process"
        assert job_data.operation == "analyze_sentiment"
        assert job_data.parameters == {"language": "en"}

    def test_text_processing_job_data_invalid_text_length(self):
        """Test TextProcessingJobData with invalid text length"""
        # Test empty text
        with pytest.raises(ValidationError) as exc_info:
            TextProcessingJobData(
                text="",
                operation="analyze"
            )
        assert "at least 1 characters" in str(exc_info.value)

        # Test text too long (over 50000 characters)
        long_text = "x" * 50001
        with pytest.raises(ValidationError) as exc_info:
            TextProcessingJobData(
                text=long_text,
                operation="analyze"
            )
        assert "at most 50000 characters" in str(exc_info.value)

    def test_text_summarization_job_data_valid(self):
        """Test TextSummarizationJobData with valid data"""
        job_data = TextSummarizationJobData(
            text="Long text to summarize",
            max_length=200,
            min_length=50,
            style="neutral"
        )
        assert job_data.job_type == JobType.text_summarization
        assert job_data.text == "Long text to summarize"
        assert job_data.max_length == 200
        assert job_data.min_length == 50
        assert job_data.style == "neutral"

    def test_text_summarization_job_data_invalid_lengths(self):
        """Test TextSummarizationJobData with invalid length constraints"""
        with pytest.raises(ValidationError) as exc_info:
            TextSummarizationJobData(
                text="Text to summarize",
                max_length=100,
                min_length=150  # min_length > max_length
            )
        assert "min_length must be less than max_length" in str(exc_info.value)

    def test_web_scraping_job_data_valid(self):
        """Test WebScrapingJobData with valid data"""
        job_data = WebScrapingJobData(
            url="https://example.com",
            selectors={"title": "h1", "content": ".main"},
            options={"timeout": 30}
        )
        assert job_data.job_type == JobType.web_scraping
        assert job_data.url == "https://example.com"
        assert job_data.selectors == {"title": "h1", "content": ".main"}
        assert job_data.options == {"timeout": 30}

    def test_web_scraping_job_data_invalid_url(self):
        """Test WebScrapingJobData with invalid URL"""
        with pytest.raises(ValidationError) as exc_info:
            WebScrapingJobData(url="invalid-url")
        assert "URL must start with http:// or https://" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            WebScrapingJobData(url="ftp://example.com")
        assert "URL must start with http:// or https://" in str(exc_info.value)

    def test_custom_job_data_valid(self):
        """Test CustomJobData with valid data"""
        job_data = CustomJobData(
            custom_data={"operation": "custom_task", "params": {"key": "value"}}
        )
        assert job_data.job_type == JobType.custom
        assert job_data.custom_data == {"operation": "custom_task", "params": {"key": "value"}}

class TestJobRequestResponseModels:
    """Test job request and response models"""

    def test_job_create_request_valid(self):
        """Test JobCreateRequest with valid data"""
        request = JobCreateRequest(
            data=TextProcessingJobData(
                text="Sample text",
                operation="analyze"
            ),
            priority=5,
            tags=["analysis", "text"]
        )
        assert request.priority == 5
        assert request.tags == ["analysis", "text"]
        assert request.data.job_type == JobType.text_processing

    def test_job_create_request_invalid_priority(self):
        """Test JobCreateRequest with invalid priority"""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(
                data=TextProcessingJobData(
                    text="Sample text",
                    operation="analyze"
                ),
                priority=15  # Priority > 10
            )
        assert "less than or equal to 10" in str(exc_info.value)

    def test_job_response_valid(self):
        """Test JobResponse with valid data"""
        response = JobResponse(
            id="test-job-id",
            status=JobStatus.completed,
            data={"job_type": "text_processing", "text": "Sample"},
            result="Processing completed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert response.id == "test-job-id"
        assert response.status == JobStatus.completed
        assert response.result == "Processing completed"

    def test_job_list_response_valid(self):
        """Test JobListResponse with valid data"""
        job = JobResponse(
            id="test-job-id",
            status=JobStatus.completed,
            data={"job_type": "text_processing"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        response = JobListResponse(
            jobs=[job],
            total_count=1
        )
        assert len(response.jobs) == 1
        assert response.total_count == 1
        assert response.success is True

    def test_job_create_response_valid(self):
        """Test JobCreateResponse with valid data"""
        response = JobCreateResponse(
            job_id="test-job-id",
            message="Job created successfully"
        )
        assert response.job_id == "test-job-id"
        assert response.success is True

    def test_job_detail_response_valid(self):
        """Test JobDetailResponse with valid data"""
        job = JobResponse(
            id="test-job-id",
            status=JobStatus.completed,
            data={"job_type": "text_processing"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        response = JobDetailResponse(job=job)
        assert response.job.id == "test-job-id"
        assert response.success is True

class TestJobUpdateModels:
    """Test job update models"""

    def test_job_status_update_valid(self):
        """Test JobStatusUpdate with valid data"""
        update = JobStatusUpdate(
            status=JobStatus.completed,
            result="Job completed successfully"
        )
        assert update.status == JobStatus.completed
        assert update.result == "Job completed successfully"

    def test_job_status_update_completed_without_result(self):
        """Test JobStatusUpdate with completed status but no result"""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusUpdate(status=JobStatus.completed)
        assert "Result is required when status is completed" in str(exc_info.value)

    def test_job_status_update_failed_without_error(self):
        """Test JobStatusUpdate with failed status but no error message"""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusUpdate(status=JobStatus.failed)
        assert "Error message is required when status is failed" in str(exc_info.value)

    def test_job_status_update_failed_with_error(self):
        """Test JobStatusUpdate with failed status and error message"""
        update = JobStatusUpdate(
            status=JobStatus.failed,
            error_message="Job failed due to timeout"
        )
        assert update.status == JobStatus.failed
        assert update.error_message == "Job failed due to timeout"

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

    def test_job_stats_response_valid(self):
        """Test JobStatsResponse with valid data"""
        stats = JobStats(
            total_jobs=50,
            pending_jobs=1,
            running_jobs=0,
            completed_jobs=45,
            failed_jobs=4,
            success_rate=91.8
        )
        response = JobStatsResponse(stats=stats)
        assert response.stats.total_jobs == 50
        assert response.success is True

class TestAuthenticationModels:
    """Test authentication models"""

    def test_auth_response_valid(self):
        """Test AuthResponse with valid data"""
        user = UserInfo(
            id="test-user-id",
            email="test@example.com"
        )
        response = AuthResponse(
            user=user,
            message="Authentication successful"
        )
        assert response.user.id == "test-user-id"
        assert response.user.email == "test@example.com"
        assert response.success is True

class TestHealthModels:
    """Test health check models"""

    def test_health_response_valid(self):
        """Test HealthResponse with valid data"""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            environment="development",
            cors_origins=5
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.environment == "development"
        assert response.cors_origins == 5
        assert isinstance(response.timestamp, datetime)

class TestModelSerialization:
    """Test model serialization and deserialization"""

    def test_job_create_request_serialization(self):
        """Test JobCreateRequest JSON serialization"""
        request = JobCreateRequest(
            data=TextProcessingJobData(
                text="Sample text",
                operation="analyze"
            ),
            priority=1,
            tags=["test"]
        )
        
        # Serialize to dict
        request_dict = request.dict()
        assert request_dict["priority"] == 1
        assert request_dict["tags"] == ["test"]
        assert request_dict["data"]["job_type"] == "text_processing"
        
        # Serialize to JSON
        request_json = request.json()
        assert isinstance(request_json, str)
        assert "text_processing" in request_json

    def test_job_response_serialization(self):
        """Test JobResponse JSON serialization"""
        response = JobResponse(
            id="test-id",
            status=JobStatus.completed,
            data={"job_type": "text_processing"},
            result="Success",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 1, 0)
        )
        
        response_dict = response.dict()
        assert response_dict["id"] == "test-id"
        assert response_dict["status"] == "completed"
        assert isinstance(response_dict["created_at"], datetime)

class TestModelValidationEdgeCases:
    """Test edge cases and validation scenarios"""

    def test_empty_custom_data(self):
        """Test CustomJobData with empty custom_data"""
        job_data = CustomJobData(custom_data={})
        assert job_data.custom_data == {}

    def test_large_text_processing_data(self):
        """Test TextProcessingJobData with maximum allowed text length"""
        max_text = "x" * 50000  # Maximum allowed length
        job_data = TextProcessingJobData(
            text=max_text,
            operation="analyze"
        )
        assert len(job_data.text) == 50000

    def test_minimal_web_scraping_data(self):
        """Test WebScrapingJobData with minimal required fields"""
        job_data = WebScrapingJobData(url="https://example.com")
        assert job_data.url == "https://example.com"
        assert job_data.selectors is None
        assert job_data.options is None

    def test_job_status_update_running_status(self):
        """Test JobStatusUpdate with running status (no validation constraints)"""
        update = JobStatusUpdate(status=JobStatus.running)
        assert update.status == JobStatus.running
        assert update.result is None
        assert update.error_message is None 