"""
Comprehensive tests for Job Monitoring routes.

Tests job logs and analytics endpoints with various scenarios.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.jobs.monitoring import router
from models import ApiResponse
from auth import get_current_user


@pytest.fixture
def mock_user():
    """Mock user for authentication."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "username": "testuser"
    }


@pytest.fixture
def app(mock_user):
    """Create FastAPI app with job monitoring router and dependency overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/jobs")
    
    # Override the authentication dependency
    def get_current_user_override():
        return mock_user
    
    app.dependency_overrides[get_current_user] = get_current_user_override
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_job():
    """Mock job data."""
    return {
        "id": "job123",
        "title": "Test Job",
        "status": "completed",
        "agent_identifier": "test-agent",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:05:00Z",
        "user_id": "user123"
    }


@pytest.fixture
def mock_failed_job():
    """Create a failed job for testing."""
    return {
        "id": "failed-job-123",
        "user_id": "user123",
        "agent_identifier": "test_agent",
        "status": "failed",
        "title": "Failed Job",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:02:00Z",
        "error_message": "Test error message"
    }


@pytest.fixture
def mock_job_with_logs():
    """Create a job with logs for testing edge cases."""
    return {
        "id": "job-with-logs",
        "user_id": "user123",
        "agent_identifier": "test_agent",
        "status": "completed",
        "title": "Job With Logs",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:05:00Z",
        "logs": [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "level": "INFO",
                "message": "Job started",
                "source": "system"
            },
            {
                "timestamp": "2024-01-01T10:05:00Z",
                "level": "INFO",
                "message": "Job completed",
                "source": "system"
            }
        ]
    }


class TestJobLogsEndpoint:
    """Test job logs retrieval endpoint."""

    def test_get_job_logs_success_completed_job(self, client, mock_user, mock_job):
        """Test successful job logs retrieval for completed job."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_job
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/job123/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["job_id"] == "job123"
            assert len(data["result"]["logs"]) >= 2  # Created and completed logs
            assert data["result"]["total_count"] >= 2
            
            # Check for specific log entries
            logs = data["result"]["logs"]
            created_log = next((log for log in logs if "Job created" in log["message"]), None)
            assert created_log is not None
            assert created_log["level"] == "INFO"
            assert created_log["source"] == "system"
            
            completed_log = next((log for log in logs if "completed successfully" in log["message"]), None)
            assert completed_log is not None
            assert completed_log["level"] == "INFO"

    def test_get_job_logs_success_failed_job(self, client, mock_user, mock_failed_job):
        """Test successful job logs retrieval for failed job."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_failed_job
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/failed-job-123/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            logs = data["result"]["logs"]
            error_log = next((log for log in logs if "Test error message" in log["message"]), None)
            assert error_log is not None
            assert error_log["level"] == "ERROR"

    def test_get_job_logs_with_level_filter(self, client, mock_user, mock_failed_job):
        """Test job logs retrieval with level filter."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_failed_job
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/failed-job-123/logs?level=ERROR")
            
            assert response.status_code == 200
            data = response.json()
            logs = data["result"]["logs"]
            
            # All logs should be ERROR level
            for log in logs:
                assert log["level"] == "ERROR"

    def test_get_job_logs_with_pagination(self, client, mock_user, mock_job):
        """Test job logs retrieval with pagination."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_job
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/job123/logs?limit=1&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert data["result"]["count"] == 1
            assert data["result"]["total_count"] >= 1

    def test_get_job_logs_running_job(self, client, mock_user):
        """Test job logs for running job."""
        running_job = {
            "id": "job789",
            "status": "running",
            "agent_identifier": "test-agent",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:01:00Z",
            "user_id": "user123"
        }
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = running_job
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/job789/logs")
            
            assert response.status_code == 200
            data = response.json()
            logs = data["result"]["logs"]
            
            # Should have created and started logs
            started_log = next((log for log in logs if "execution started" in log["message"]), None)
            assert started_log is not None
            assert started_log["level"] == "INFO"

    def test_get_job_logs_job_not_found(self, client, mock_user):
        """Test job logs retrieval for non-existent job."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = None
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/nonexistent/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Job not found" in data["error"]
            assert data["metadata"]["error_code"] == "JOB_NOT_FOUND"

    def test_get_job_logs_database_error(self, client, mock_user):
        """Test job logs retrieval with database error."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.side_effect = Exception("Database connection failed")
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/job123/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Database connection failed" in data["error"]
            assert data["metadata"]["error_code"] == "JOB_LOGS_ERROR"

    def test_get_job_logs_query_parameter_validation(self, client, mock_user, mock_job):
        """Test job logs endpoint with various query parameters."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_job
            mock_db.return_value = mock_db_ops
            
            # Test with maximum limit
            response = client.get("/jobs/job123/logs?limit=1000")
            assert response.status_code == 200
            
            # Test with custom offset
            response = client.get("/jobs/job123/logs?offset=5")
            assert response.status_code == 200
            
            # Test with level filter
            response = client.get("/jobs/job123/logs?level=INFO")
            assert response.status_code == 200
            data = response.json()
            for log in data["result"]["logs"]:
                assert log["level"] == "INFO"


class TestJobAnalyticsEndpoint:
    """Test job analytics summary endpoint."""

    @pytest.fixture
    def mock_jobs_data(self):
        """Mock jobs data for analytics testing."""
        base_time = datetime.now(timezone.utc) - timedelta(days=3)
        return [
            {
                "id": "job1",
                "status": "completed",
                "agent_identifier": "agent-a",
                "created_at": base_time.isoformat(),
                "updated_at": (base_time + timedelta(minutes=5)).isoformat(),
                "user_id": "user123"
            },
            {
                "id": "job2", 
                "status": "completed",
                "agent_identifier": "agent-a",
                "created_at": (base_time + timedelta(hours=1)).isoformat(),
                "updated_at": (base_time + timedelta(hours=1, minutes=3)).isoformat(),
                "user_id": "user123"
            },
            {
                "id": "job3",
                "status": "failed",
                "agent_identifier": "agent-b",
                "created_at": (base_time + timedelta(hours=2)).isoformat(),
                "updated_at": (base_time + timedelta(hours=2, minutes=1)).isoformat(),
                "user_id": "user123"
            },
            {
                "id": "job4",
                "status": "pending",
                "agent_identifier": "agent-a",
                "created_at": (base_time + timedelta(hours=3)).isoformat(),
                "updated_at": (base_time + timedelta(hours=3)).isoformat(),
                "user_id": "user123"
            },
            {
                "id": "job5",
                "status": "running",
                "agent_identifier": "agent-c",
                "created_at": (base_time + timedelta(hours=4)).isoformat(),
                "updated_at": (base_time + timedelta(hours=4)).isoformat(),
                "user_id": "user123"
            }
        ]

    def test_get_analytics_summary_success(self, client, mock_user, mock_jobs_data):
        """Test successful analytics summary retrieval."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = mock_jobs_data
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            analytics = data["result"]["analytics"]
            assert "period" in analytics
            assert "totals" in analytics
            assert "performance" in analytics
            assert "breakdown" in analytics
            
            # Check totals
            totals = analytics["totals"]
            assert totals["total_jobs"] == 5
            assert totals["completed_jobs"] == 2
            assert totals["failed_jobs"] == 1
            assert totals["pending_jobs"] == 1
            assert totals["running_jobs"] == 1
            
            # Check performance metrics
            performance = analytics["performance"]
            assert performance["success_rate_percentage"] == 40.0  # 2 out of 5
            assert "average_execution_time_seconds" in performance
            assert "total_execution_time_seconds" in performance

    def test_get_analytics_summary_with_agent_filter(self, client, mock_user, mock_jobs_data):
        """Test analytics summary with agent filter."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = mock_jobs_data
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary?agent_identifier=agent-a")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should only include jobs from agent-a (3 jobs)
            analytics = data["result"]["analytics"]
            totals = analytics["totals"]
            assert totals["total_jobs"] == 3
            assert totals["completed_jobs"] == 2
            assert totals["pending_jobs"] == 1
            
            # Check filters are recorded
            assert data["result"]["filters"]["agent_identifier"] == "agent-a"

    def test_get_analytics_summary_with_custom_days(self, client, mock_user, mock_jobs_data):
        """Test analytics summary with custom day range."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = mock_jobs_data
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary?days=30")
            
            assert response.status_code == 200
            data = response.json()
            
            analytics = data["result"]["analytics"]
            assert analytics["period"]["days"] == 30
            assert data["metadata"]["period_days"] == 30

    def test_get_analytics_summary_no_jobs(self, client, mock_user):
        """Test analytics summary with no jobs."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = []
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            analytics = data["result"]["analytics"]
            totals = analytics["totals"]
            assert totals["total_jobs"] == 0
            assert totals["completed_jobs"] == 0
            assert analytics["performance"]["success_rate_percentage"] == 0
            assert analytics["performance"]["average_execution_time_seconds"] == 0

    def test_get_analytics_summary_old_jobs_filtered(self, client, mock_user):
        """Test that old jobs outside date range are filtered out."""
        old_job = {
            "id": "old_job",
            "status": "completed",
            "agent_identifier": "agent-a",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "updated_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "user_id": "user123"
        }
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = [old_job]
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary?days=7")
            
            assert response.status_code == 200
            data = response.json()
            
            # Old job should be filtered out
            analytics = data["result"]["analytics"]
            assert analytics["totals"]["total_jobs"] == 0

    def test_get_analytics_summary_database_error(self, client, mock_user):
        """Test analytics summary with database error."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.side_effect = Exception("Database error")
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Database error" in data["error"]
            assert data["metadata"]["error_code"] == "JOB_ANALYTICS_ERROR"

    def test_get_analytics_summary_malformed_dates(self, client, mock_user):
        """Test analytics with jobs having malformed dates."""
        malformed_jobs = [
            {
                "id": "job1",
                "status": "completed",
                "agent_identifier": "agent-a",
                "created_at": "invalid-date",
                "updated_at": "also-invalid",
                "user_id": "user123"
            }
        ]
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = malformed_jobs
            mock_db.return_value = mock_db_ops
            
            # Should handle malformed dates by returning an error
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Invalid isoformat string" in data["error"]
            assert data["metadata"]["error_code"] == "JOB_ANALYTICS_ERROR"

    def test_analytics_breakdown_by_agent_and_status(self, client, mock_user, mock_jobs_data):
        """Test analytics breakdown by agent and status."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = mock_jobs_data
            mock_db.return_value = mock_db_ops
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            breakdown = data["result"]["analytics"]["breakdown"]
            
            # Check status breakdown
            assert breakdown["by_status"]["completed"] == 2
            assert breakdown["by_status"]["failed"] == 1
            assert breakdown["by_status"]["pending"] == 1
            assert breakdown["by_status"]["running"] == 1
            
            # Check agent breakdown
            assert breakdown["by_agent"]["agent-a"] == 3
            assert breakdown["by_agent"]["agent-b"] == 1
            assert breakdown["by_agent"]["agent-c"] == 1

    def test_analytics_query_parameter_validation(self, client, mock_user, mock_jobs_data):
        """Test analytics endpoint query parameter validation."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_user_jobs.return_value = mock_jobs_data
            mock_db.return_value = mock_db_ops
            
            # Test minimum days value
            response = client.get("/jobs/analytics/summary?days=1")
            assert response.status_code == 200
            
            # Test maximum days value
            response = client.get("/jobs/analytics/summary?days=90")
            assert response.status_code == 200
            
            # Test with agent identifier
            response = client.get("/jobs/analytics/summary?agent_identifier=test-agent")
            assert response.status_code == 200


class TestJobMonitoringIntegration:
    """Test integration scenarios for job monitoring."""

    def test_authorization_consistency(self, client):
        """Test that all endpoints require proper authorization."""
        # Remove auth override to test unauthorized access
        if get_current_user in client.app.dependency_overrides:
            del client.app.dependency_overrides[get_current_user]
        
        endpoints = [
            ("GET", "/jobs/test-job-123/logs"),
            ("GET", "/jobs/analytics/summary")
        ]
        
        for method, url in endpoints:
            response = client.get(url)
            assert response.status_code in [401, 403], f"Expected auth error for {method} {url}"

    def test_error_handling_consistency(self, client, mock_user):
        """Test consistent error handling patterns across endpoints."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            mock_db.get_job.side_effect = Exception("Database error")
            mock_db.get_user_jobs.side_effect = Exception("Database error")
            mock_db_ops.return_value = mock_db
            
            endpoints = [
                ("logs", "/jobs/test-job-123/logs"),
                ("analytics", "/jobs/analytics/summary")
            ]
            
            for name, url in endpoints:
                response = client.get(url)
                data = response.json()
                
                assert response.status_code == 200, f"{name} should return 200"
                assert data["success"] is False, f"{name} should have success=False"
                assert "Database error" in data["error"], f"{name} should have database error"

    def test_logs_endpoint_edge_cases(self, client, mock_user, mock_job_with_logs):
        """Test edge cases in logs endpoint to fill coverage gaps."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            mock_db.get_job.return_value = mock_job_with_logs
            mock_db_ops.return_value = mock_db
            
            # Test with large limit value (but within validation constraints)
            response = client.get(f"/jobs/{mock_job_with_logs['id']}/logs?limit=1000")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should handle large limits gracefully (capped at 1000)
            assert data["success"] is True
            assert data["metadata"]["filters"]["limit"] == 1000

    def test_analytics_summary_edge_cases(self, client, mock_user):
        """Test edge cases in analytics summary to fill coverage gaps."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            
            # Test with empty job list
            mock_db.get_user_jobs.return_value = []
            mock_db_ops.return_value = mock_db
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["result"]["analytics"]["totals"]["total_jobs"] == 0
            assert data["result"]["analytics"]["breakdown"]["by_status"] == {}
            assert data["result"]["analytics"]["breakdown"]["by_agent"] == {}

    def test_analytics_summary_with_varied_data(self, client, mock_user):
        """Test analytics summary with varied job data to ensure all code paths are covered."""
        # Create jobs with different statuses and agents (using recent dates)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        
        varied_jobs = [
            {
                "id": "job-1",
                "status": "completed",
                "agent_identifier": "agent_a",
                "created_at": (now - timedelta(days=1)).isoformat(),
                "updated_at": (now - timedelta(days=1) + timedelta(minutes=5)).isoformat()
            },
            {
                "id": "job-2", 
                "status": "failed",
                "agent_identifier": "agent_b",
                "created_at": (now - timedelta(days=2)).isoformat(),
                "updated_at": (now - timedelta(days=2) + timedelta(minutes=2)).isoformat()
            },
            {
                "id": "job-3",
                "status": "running",
                "agent_identifier": "agent_a",
                "created_at": (now - timedelta(days=3)).isoformat(),
                "updated_at": (now - timedelta(days=3) + timedelta(minutes=1)).isoformat()
            },
            {
                "id": "job-4",
                "status": "completed",
                "agent_identifier": "agent_c",
                "created_at": (now - timedelta(days=4)).isoformat(),
                "updated_at": (now - timedelta(days=4) + timedelta(minutes=3)).isoformat()
            }
        ]
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            mock_db.get_user_jobs.return_value = varied_jobs
            mock_db_ops.return_value = mock_db
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["result"]["analytics"]["totals"]["total_jobs"] == 4
            
            # Check status distribution
            status_dist = data["result"]["analytics"]["breakdown"]["by_status"]
            assert status_dist["completed"] == 2
            assert status_dist["failed"] == 1
            assert status_dist["running"] == 1
            
            # Check agent distribution
            agent_dist = data["result"]["analytics"]["breakdown"]["by_agent"]
            assert agent_dist["agent_a"] == 2
            assert agent_dist["agent_b"] == 1
            assert agent_dist["agent_c"] == 1

    def test_logs_endpoint_with_job_missing_logs(self, client, mock_user):
        """Test logs endpoint with job that has no logs field."""
        job_without_logs = {
            "id": "job-no-logs",
            "user_id": "user123",
            "status": "completed",
            "agent_identifier": "test_agent",
            "title": "Job Without Logs",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:05:00Z"
            # No 'logs' field
        }
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            mock_db.get_job.return_value = job_without_logs
            mock_db_ops.return_value = mock_db
            
            response = client.get(f"/jobs/{job_without_logs['id']}/logs")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            # The endpoint generates default logs based on job status, so it won't be empty
            assert len(data["result"]["logs"]) > 0  # Should have at least creation and completion logs
            assert data["result"]["total_count"] > 0

    def test_analytics_summary_calculation_accuracy(self, client, mock_user):
        """Test analytics summary calculation accuracy with edge cases."""
        # Test with jobs having None or missing agent_identifier (using recent dates)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        
        edge_case_jobs = [
            {
                "id": "job-1",
                "status": "completed",
                "agent_identifier": None,  # None value
                "created_at": (now - timedelta(days=1)).isoformat(),
                "updated_at": (now - timedelta(days=1) + timedelta(minutes=5)).isoformat()
            },
            {
                "id": "job-2",
                "status": "pending",
                # Missing agent_identifier
                "created_at": (now - timedelta(days=2)).isoformat(),
                "updated_at": (now - timedelta(days=2)).isoformat()
            },
            {
                "id": "job-3",
                "status": "completed",
                "agent_identifier": "",  # Empty string
                "created_at": (now - timedelta(days=3)).isoformat(),
                "updated_at": (now - timedelta(days=3) + timedelta(minutes=3)).isoformat()
            }
        ]
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db_ops:
            mock_db = AsyncMock()
            mock_db.get_user_jobs.return_value = edge_case_jobs
            mock_db_ops.return_value = mock_db
            
            response = client.get("/jobs/analytics/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["result"]["analytics"]["totals"]["total_jobs"] == 3
            
            # Should handle None/missing agent_identifier gracefully
            status_dist = data["result"]["analytics"]["breakdown"]["by_status"]
            assert status_dist["completed"] == 2
            assert status_dist["pending"] == 1

    def test_logs_and_analytics_consistency(self, client, mock_user, mock_job):
        """Test that logs and analytics are consistent for the same job."""
        # Update job to have recent date for analytics window
        recent_job = {
            **mock_job,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = recent_job
            mock_db_ops.get_user_jobs.return_value = [recent_job]
            mock_db.return_value = mock_db_ops
            
            # Get logs
            logs_response = client.get("/jobs/job123/logs")
            assert logs_response.status_code == 200
            
            # Get analytics
            analytics_response = client.get("/jobs/analytics/summary")
            assert analytics_response.status_code == 200
            
            analytics_data = analytics_response.json()
            assert analytics_data["result"]["analytics"]["totals"]["completed_jobs"] == 1

    def test_endpoint_metadata_consistency(self, client, mock_user, mock_job):
        """Test that all endpoints return consistent metadata."""
        with patch('routes.jobs.monitoring.get_database_operations') as mock_db:
            mock_db_ops = AsyncMock()
            mock_db_ops.get_job.return_value = mock_job
            mock_db_ops.get_user_jobs.return_value = [mock_job]
            mock_db.return_value = mock_db_ops
            
            # Test logs endpoint metadata
            logs_response = client.get("/jobs/job123/logs")
            logs_data = logs_response.json()
            assert "metadata" in logs_data
            assert "timestamp" in logs_data["metadata"]
            assert logs_data["metadata"]["endpoint"] == "job_logs"
            
            # Test analytics endpoint metadata
            analytics_response = client.get("/jobs/analytics/summary")
            analytics_data = analytics_response.json()
            assert "metadata" in analytics_data
            assert "timestamp" in analytics_data["metadata"]
            assert analytics_data["metadata"]["endpoint"] == "job_analytics" 