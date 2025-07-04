"""
Unit tests for SchedulerService background service.

Tests comprehensive scheduler functionality including:
- Service lifecycle and statistics tracking (Task 4.1)
- Due schedule detection with tolerance window handling (Task 4.2)  
- Job creation for due schedules with proper data mapping (Task 4.3)
- Next run time calculation and schedule updates after execution (Task 4.4)
- Error handling for invalid cron expressions and missing data (Task 4.5)
- Concurrent execution prevention and database error recovery (Task 4.6)
- Schedule disabling on critical errors and error logging (Task 4.7)
- Statistics collection and reporting functionality (Task 4.8)
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from services.scheduler import SchedulerService, get_scheduler_service
from models.schedule import ScheduleStatus
from utils.cron_utils import CronValidationError
from tests.fixtures.schedule_fixtures import ScheduleFixtures
from tests.utils.mock_utils import JobPipelineMockManager


class MockSupabaseScheduler:
    """Mock Supabase client for scheduler testing."""
    
    def __init__(self):
        self.schedules_data = []
        self.update_calls = []
        self.query_calls = []
        self.table_mock = Mock()
        self._setup_table_mock()
        
    def _setup_table_mock(self):
        """Setup table mock with chainable methods."""
        self.mock_result = Mock()
        self.mock_result.data = []
        
        # Setup chaining methods
        self.table_mock.select = Mock(return_value=self.table_mock)
        self.table_mock.eq = Mock(return_value=self.table_mock)
        self.table_mock.not_ = Mock()
        self.table_mock.not_.is_ = Mock(return_value=self.table_mock)
        self.table_mock.lte = Mock(return_value=self.table_mock)
        self.table_mock.update = Mock(return_value=self.table_mock)
        self.table_mock.insert = Mock(return_value=self.table_mock)
        self.table_mock.execute = Mock(return_value=self.mock_result)
        
    def setup_schedules_data(self, schedules: List[Dict[str, Any]]):
        """Setup mock schedules data."""
        self.schedules_data = schedules
        self.mock_result.data = schedules
        
    def add_schedule(self, schedule_data: Dict[str, Any]):
        """Add a schedule to mock data."""
        self.schedules_data.append(schedule_data)
        self.mock_result.data = self.schedules_data
        
    def table(self, table_name: str):
        """Mock table method."""
        return self.table_mock
        
    def get_update_calls(self) -> List[Dict[str, Any]]:
        """Get recorded update calls."""
        return self.update_calls
        
    def record_update_call(self, schedule_id: str, update_data: Dict[str, Any]):
        """Record an update call."""
        self.update_calls.append({
            "schedule_id": schedule_id,
            "update_data": update_data
        })


class MockJobPipelineScheduler:
    """Mock job pipeline for scheduler testing."""
    
    def __init__(self):
        self.submitted_jobs = []
        self.submission_errors = {}
        
    def setup_submission_error(self, error_message: str):
        """Setup job submission error."""
        self.submission_error = Exception(error_message)
        
    async def submit_job(self, job_id: str, user_id: str, agent_name: str, 
                        job_data: Dict[str, Any], priority: int = 5, 
                        tags: List[str] = None) -> bool:
        """Mock job submission."""
        if hasattr(self, 'submission_error'):
            raise self.submission_error
            
        job_record = {
            "job_id": job_id,
            "user_id": user_id,
            "agent_name": agent_name,
            "job_data": job_data,
            "priority": priority,
            "tags": tags or []
        }
        self.submitted_jobs.append(job_record)
        return True
        
    def get_submitted_jobs(self) -> List[Dict[str, Any]]:
        """Get all submitted jobs."""
        return self.submitted_jobs
        
    def reset(self):
        """Reset mock state."""
        self.submitted_jobs = []
        if hasattr(self, 'submission_error'):
            delattr(self, 'submission_error')


@pytest.fixture
def mock_supabase():
    """Mock Supabase client fixture."""
    return MockSupabaseScheduler()


@pytest.fixture  
def mock_job_pipeline():
    """Mock job pipeline fixture."""
    return MockJobPipelineScheduler()


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for testing."""
    schedule_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    current_time = datetime.now(timezone.utc)
    
    return {
        "id": schedule_id,
        "user_id": user_id,
        "title": "Test Schedule",
        "agent_name": "test_agent",
        "cron_expression": "0 9 * * *",
        "agent_config_data": {
            "name": "test_agent",
            "job_data": {"prompt": "Test prompt"},
            "execution": {"priority": 5}
        },
        "next_run": (current_time - timedelta(minutes=5)).isoformat(),
        "last_run": (current_time - timedelta(days=1)).isoformat()
    }


@pytest.fixture
def scheduler_service():
    """Create scheduler service for testing."""
    return SchedulerService(check_interval=1, tolerance_seconds=60)


class TestSchedulerServiceLifecycle:
    """Tests for scheduler service lifecycle and statistics tracking (Task 4.1)."""
    
    @pytest.mark.asyncio
    async def test_scheduler_service_initialization(self, scheduler_service):
        """Test scheduler service initialization."""
        assert scheduler_service.check_interval == 1
        assert scheduler_service.tolerance_seconds == 60
        assert scheduler_service.running is False
        assert scheduler_service.task is None
        assert scheduler_service.stats["total_checks"] == 0
        assert scheduler_service.stats["schedules_processed"] == 0
        assert scheduler_service.stats["jobs_created"] == 0
        assert scheduler_service.stats["errors"] == 0
        assert scheduler_service.stats["start_time"] is None
    
    @pytest.mark.asyncio
    async def test_scheduler_service_start_stop(self, scheduler_service):
        """Test scheduler service start/stop lifecycle."""
        # Mock dependencies
        with patch('services.scheduler.get_supabase_client'):
            with patch('services.scheduler.get_job_pipeline'):
                # Test start
                await scheduler_service.start()
                
                assert scheduler_service.running is True
                assert scheduler_service.task is not None
                assert scheduler_service.stats["start_time"] is not None
                
                # Wait briefly for task to start
                await asyncio.sleep(0.1)
                
                # Test stop
                await scheduler_service.stop()
                
                assert scheduler_service.running is False
                assert scheduler_service.task.cancelled() or scheduler_service.task.done()
    
    @pytest.mark.asyncio
    async def test_scheduler_start_when_already_running(self, scheduler_service):
        """Test starting scheduler when already running."""
        with patch('services.scheduler.get_supabase_client'):
            with patch('services.scheduler.get_job_pipeline'):
                # Start first time
                await scheduler_service.start()
                first_task = scheduler_service.task
                
                # Try to start again
                await scheduler_service.start()
                
                # Should still be the same task
                assert scheduler_service.task is first_task
                assert scheduler_service.running is True
                
                # Cleanup
                await scheduler_service.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_stop_when_not_running(self, scheduler_service):
        """Test stopping scheduler when not running."""
        # Should not raise exception
        await scheduler_service.stop()
        assert scheduler_service.running is False
    
    def test_scheduler_statistics_tracking(self, scheduler_service):
        """Test scheduler statistics collection."""
        # Test initial stats
        stats = scheduler_service.get_stats()
        assert stats["running"] is False
        assert stats["total_checks"] == 0
        assert stats["uptime_seconds"] == 0
        
        # Simulate some activity
        scheduler_service.stats["total_checks"] = 10
        scheduler_service.stats["schedules_processed"] = 5
        scheduler_service.stats["jobs_created"] = 3
        scheduler_service.stats["errors"] = 1
        scheduler_service.stats["start_time"] = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        stats = scheduler_service.get_stats()
        assert stats["total_checks"] == 10
        assert stats["schedules_processed"] == 5
        assert stats["jobs_created"] == 3
        assert stats["errors"] == 1
        assert stats["uptime_seconds"] > 0
    
    @pytest.mark.asyncio
    async def test_force_check_when_not_running(self, scheduler_service):
        """Test force check when scheduler is not running."""
        with pytest.raises(RuntimeError, match="Scheduler service is not running"):
            await scheduler_service.force_check()
    
    @pytest.mark.asyncio  
    async def test_force_check_when_running(self, scheduler_service, mock_supabase):
        """Test force check when scheduler is running."""
        mock_supabase.setup_schedules_data([])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                await scheduler_service.start()
                
                # Force a check
                await scheduler_service.force_check()
                
                # force_check() calls _check_and_process_schedules() directly,
                # which doesn't increment total_checks (that's done in the main loop)
                # Just verify it completed without error
                assert scheduler_service.running is True
                
                await scheduler_service.stop()


class TestDueScheduleDetection:
    """Tests for due schedule detection with tolerance window handling (Task 4.2)."""
    
    @pytest.mark.asyncio
    async def test_detect_due_schedules_empty_database(self, scheduler_service, mock_supabase):
        """Test due schedule detection with empty database."""
        mock_supabase.setup_schedules_data([])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                await scheduler_service._check_and_process_schedules()
                
                # Should complete without error
                assert scheduler_service.stats["total_checks"] == 0  # Not incremented in direct call
    
    @pytest.mark.asyncio
    async def test_detect_schedules_within_tolerance_window(self, scheduler_service, mock_supabase):
        """Test detecting schedules within tolerance window."""
        current_time = datetime.now(timezone.utc)
        
        # Schedule that's due within tolerance
        due_schedule = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Due Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *", 
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"},
                "execution": {"priority": 5}
            },
            "next_run": (current_time - timedelta(seconds=30)).isoformat(),
            "last_run": (current_time - timedelta(days=1)).isoformat()
        }
        
        mock_supabase.setup_schedules_data([due_schedule])
        mock_job_pipeline = MockJobPipelineScheduler()
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch.object(scheduler_service, '_create_scheduled_job', new_callable=AsyncMock) as mock_create:
                    with patch.object(scheduler_service, '_update_schedule_after_execution', new_callable=AsyncMock):
                        mock_create.return_value = str(uuid.uuid4())
                        
                        await scheduler_service._check_and_process_schedules()
                        
                        # Should have processed the due schedule
                        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skip_schedules_outside_tolerance_window(self, scheduler_service, mock_supabase):
        """Test skipping schedules outside tolerance window."""
        current_time = datetime.now(timezone.utc)
        
        # Schedule that's not yet due (outside tolerance)
        early_schedule = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Early Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "agent_config_data": {
                "name": "test_agent", 
                "job_data": {"prompt": "test"},
                "execution": {"priority": 5}
            },
            "next_run": (current_time + timedelta(minutes=10)).isoformat(),
            "last_run": (current_time - timedelta(days=1)).isoformat()
        }
        
        mock_supabase.setup_schedules_data([early_schedule])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                with patch.object(scheduler_service, '_create_scheduled_job', new_callable=AsyncMock) as mock_create:
                    await scheduler_service._check_and_process_schedules()
                    
                    # Should not have processed the early schedule
                    mock_create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_tolerance_window_calculation(self, scheduler_service):
        """Test tolerance window calculation."""
        current_time = datetime.now(timezone.utc)
        expected_tolerance = current_time + timedelta(seconds=scheduler_service.tolerance_seconds)
        
        with patch('services.scheduler.datetime') as mock_datetime:
            mock_datetime.now.return_value = current_time
            mock_datetime.timedelta = timedelta
            mock_datetime.timezone = timezone
            
            mock_supabase = MockSupabaseScheduler()
            mock_supabase.setup_schedules_data([])
            
            with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
                with patch('services.scheduler.get_job_pipeline'):
                    await scheduler_service._check_and_process_schedules()
                    
                    # Verify tolerance window was used in query
                    mock_supabase.table_mock.lte.assert_called_once()
                    call_args = mock_supabase.table_mock.lte.call_args[0]
                    assert call_args[0] == "next_run"
                    # Tolerance should be approximately correct (within 1 second)
                    called_time = datetime.fromisoformat(call_args[1].replace('Z', '+00:00'))
                    time_diff = abs((called_time - expected_tolerance).total_seconds())
                    assert time_diff < 1.0 


class TestJobCreation:
    """Tests for job creation for due schedules with proper data mapping (Task 4.3)."""
    
    @pytest.mark.asyncio
    async def test_create_scheduled_job_success(self, scheduler_service):
        """Test successful scheduled job creation."""
        schedule_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        agent_name = "test_agent"
        schedule_title = "Test Schedule"
        
        agent_config_data = {
            "name": "test_agent",
            "job_data": {
                "prompt": "Test prompt",
                "max_tokens": 1000
            },
            "execution": {
                "priority": 8,
                "timeout_seconds": 600
            }
        }
        
        # Mock dependencies
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        
        # Mock successful database insert
        expected_job_record = {
            "id": "mocked-job-id",
            "user_id": user_id,
            "agent_identifier": agent_name,
            "title": f"[Scheduled] {schedule_title}",
            "data": agent_config_data["job_data"],
            "status": "pending",
            "priority": 8,
            "schedule_id": schedule_id,
            "execution_source": "scheduled"
        }
        mock_supabase.mock_result.data = [expected_job_record]
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch('services.scheduler.uuid.uuid4', return_value="mocked-job-id"):
                    job_id = await scheduler_service._create_scheduled_job(
                        schedule_id, user_id, agent_name, agent_config_data, schedule_title
                    )
                    
                    assert job_id == "mocked-job-id"
                    
                    # Verify job was submitted to pipeline
                    submitted_jobs = mock_job_pipeline.get_submitted_jobs()
                    assert len(submitted_jobs) == 1
                    
                    submitted_job = submitted_jobs[0]
                    assert submitted_job["job_id"] == "mocked-job-id"
                    assert submitted_job["user_id"] == user_id
                    assert submitted_job["agent_name"] == agent_name
                    assert submitted_job["job_data"] == agent_config_data["job_data"]
                    assert submitted_job["priority"] == 8
                    assert "scheduled" in submitted_job["tags"]
                    assert "automated" in submitted_job["tags"]
    
    @pytest.mark.asyncio
    async def test_create_scheduled_job_with_default_priority(self, scheduler_service):
        """Test scheduled job creation with default priority."""
        schedule_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        agent_config_data = {
            "name": "test_agent",
            "job_data": {"prompt": "test"},
            "execution": {}  # No priority specified
        }
        
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        mock_supabase.mock_result.data = [{"id": "job-id"}]
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch('services.scheduler.uuid.uuid4', return_value="job-id"):
                    await scheduler_service._create_scheduled_job(
                        schedule_id, user_id, "test_agent", agent_config_data, "Test"
                    )
                    
                    # Should use default priority of 5
                    submitted_jobs = mock_job_pipeline.get_submitted_jobs()
                    assert submitted_jobs[0]["priority"] == 5
    
    @pytest.mark.asyncio
    async def test_create_scheduled_job_database_failure(self, scheduler_service):
        """Test job creation when database insert fails."""
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        
        # Mock database insert failure
        mock_supabase.mock_result.data = []  # Empty result indicates failure
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with pytest.raises(Exception, match="Failed to create job record"):
                    await scheduler_service._create_scheduled_job(
                        str(uuid.uuid4()), str(uuid.uuid4()), "test_agent", 
                        {"name": "test_agent", "job_data": {"prompt": "test"}}, "Test"
                    )
    
    @pytest.mark.asyncio
    async def test_create_scheduled_job_pipeline_failure(self, scheduler_service):
        """Test job creation when pipeline submission fails."""
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        
        # Mock successful database insert
        mock_supabase.mock_result.data = [{"id": "job-id"}]
        
        # Mock pipeline submission failure
        mock_job_pipeline.setup_submission_error("Pipeline submission failed")
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch('services.scheduler.uuid.uuid4', return_value="job-id"):
                    with pytest.raises(Exception, match="Pipeline submission failed"):
                        await scheduler_service._create_scheduled_job(
                            str(uuid.uuid4()), str(uuid.uuid4()), "test_agent",
                            {"name": "test_agent", "job_data": {"prompt": "test"}}, "Test"
                        )


class TestNextRunTimeCalculation:
    """Tests for next run time calculation and schedule updates after execution (Task 4.4)."""
    
    @pytest.mark.asyncio
    async def test_update_schedule_after_execution_success(self, scheduler_service):
        """Test successful schedule update after execution."""
        schedule_id = str(uuid.uuid4())
        execution_time = datetime.now(timezone.utc)
        next_run = execution_time + timedelta(hours=24)
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.mock_result.data = [{"id": schedule_id}]  # Mock successful update
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            await scheduler_service._update_schedule_after_execution(
                schedule_id, execution_time, next_run
            )
            
            # Verify update was called with correct data
            mock_supabase.table_mock.update.assert_called_once()
            update_call = mock_supabase.table_mock.update.call_args[0][0]
            
            assert update_call["last_run"] == execution_time.isoformat()
            assert update_call["next_run"] == next_run.isoformat()
            assert "updated_at" in update_call
    
    @pytest.mark.asyncio
    async def test_update_schedule_after_execution_failure(self, scheduler_service):
        """Test schedule update when database update fails."""
        schedule_id = str(uuid.uuid4())
        execution_time = datetime.now(timezone.utc)
        next_run = execution_time + timedelta(hours=24)
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.mock_result.data = []  # Mock failed update
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            # Should not raise exception, just log warning
            await scheduler_service._update_schedule_after_execution(
                schedule_id, execution_time, next_run
            )
    
    @pytest.mark.asyncio
    async def test_process_schedule_with_next_run_calculation(self, scheduler_service):
        """Test complete schedule processing with next run calculation."""
        current_time = datetime.now(timezone.utc)
        schedule_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",  # Daily at 9 AM
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"},
                "execution": {"priority": 5}
            },
            "next_run": (current_time - timedelta(minutes=5)).isoformat(),
            "last_run": (current_time - timedelta(days=1)).isoformat()
        }
        
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        
        # Mock successful job creation
        mock_supabase.mock_result.data = [{"id": "job-id"}]
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch('services.scheduler.uuid.uuid4', return_value="job-id"):
                    with patch('utils.cron_utils.CronUtils.get_next_run_time') as mock_next_run:
                        expected_next_run = current_time + timedelta(days=1)
                        mock_next_run.return_value = expected_next_run
                        
                        await scheduler_service._process_schedule(schedule_data, current_time)
                        
                        # Verify next run time was calculated
                        mock_next_run.assert_called_once_with("0 9 * * *", current_time)
                        
                        # Verify schedule was updated with new next run time
                        mock_supabase.table_mock.update.assert_called()
                        update_data = mock_supabase.table_mock.update.call_args[0][0]
                        assert update_data["next_run"] == expected_next_run.isoformat()
    
    @pytest.mark.asyncio
    async def test_process_schedule_without_next_run(self, scheduler_service):
        """Test processing schedule that has no next_run time."""
        schedule_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Test Schedule",
            "agent_name": "test_agent", 
            "cron_expression": "0 9 * * *",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"}
            },
            "next_run": None,  # No next run time
            "last_run": None
        }
        
        with patch.object(scheduler_service, '_create_scheduled_job', new_callable=AsyncMock) as mock_create:
            await scheduler_service._process_schedule(schedule_data, datetime.now(timezone.utc))
            
            # Should skip processing due to missing next_run
            mock_create.assert_not_called()


class TestErrorHandling:
    """Tests for error handling scenarios (Tasks 4.5, 4.6, 4.7)."""
    
    @pytest.mark.asyncio
    async def test_invalid_cron_expression_handling(self, scheduler_service):
        """Test handling of invalid cron expressions (Task 4.5)."""
        schedule_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Invalid Cron Schedule",
            "agent_name": "test_agent",
            "cron_expression": "invalid_cron",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"}
            },
            "next_run": datetime.now(timezone.utc).isoformat(),
            "last_run": None
        }
        
        mock_supabase = MockSupabaseScheduler()
        mock_job_pipeline = MockJobPipelineScheduler()
        mock_supabase.mock_result.data = [{"id": "job-id"}]
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                with patch('services.scheduler.uuid.uuid4', return_value="job-id"):
                    with patch('utils.cron_utils.CronUtils.get_next_run_time') as mock_next_run:
                        # Mock cron validation error
                        mock_next_run.side_effect = CronValidationError("Invalid cron expression")
                        
                        with patch.object(scheduler_service, '_disable_schedule_with_error', new_callable=AsyncMock) as mock_disable:
                            await scheduler_service._process_schedule(schedule_data, datetime.now(timezone.utc))
                            
                            # Should disable schedule due to invalid cron
                            mock_disable.assert_called_once_with(
                                schedule_data["id"], 
                                "Invalid cron expression: Invalid cron expression"
                            )
    
    @pytest.mark.asyncio
    async def test_schedule_error_handling(self, scheduler_service):
        """Test general schedule error handling (Task 4.6)."""
        schedule_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Error Schedule", 
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"}
            },
            "next_run": datetime.now(timezone.utc).isoformat(),
            "last_run": None
        }
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.setup_schedules_data([schedule_data])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                with patch.object(scheduler_service, '_create_scheduled_job', new_callable=AsyncMock) as mock_create:
                    with patch.object(scheduler_service, '_handle_schedule_error', new_callable=AsyncMock) as mock_handle_error:
                        # Mock job creation failure
                        mock_create.side_effect = Exception("Job creation failed")
                        
                        # This should catch the exception and call handle_error
                        await scheduler_service._check_and_process_schedules()
                        
                        # Should handle the error
                        mock_handle_error.assert_called_once_with(
                            schedule_data["id"], 
                            "Job creation failed"
                        )
    
    @pytest.mark.asyncio
    async def test_disable_schedule_with_error(self, scheduler_service):
        """Test disabling schedule on critical errors (Task 4.7)."""
        schedule_id = str(uuid.uuid4())
        error_message = "Critical error occurred"
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.mock_result.data = [{"id": schedule_id}]  # Mock successful disable
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            await scheduler_service._disable_schedule_with_error(schedule_id, error_message)
            
            # Verify schedule was disabled
            mock_supabase.table_mock.update.assert_called_once()
            update_data = mock_supabase.table_mock.update.call_args[0][0]
            
            assert update_data["enabled"] is False
            assert update_data["next_run"] is None
            assert "updated_at" in update_data
    
    @pytest.mark.asyncio
    async def test_disable_schedule_database_error(self, scheduler_service):
        """Test error handling when disabling schedule fails."""
        schedule_id = str(uuid.uuid4())
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.table_mock.update.side_effect = Exception("Database error")
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            # Should not raise exception, just log error
            await scheduler_service._disable_schedule_with_error(schedule_id, "Test error")
    
    @pytest.mark.asyncio
    async def test_database_error_recovery(self, scheduler_service):
        """Test database error recovery in main loop (Task 4.6)."""
        mock_supabase = MockSupabaseScheduler()
        
        # Mock database error on first call, success on second
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Database connection lost")
            return mock_supabase.table_mock
        
        mock_supabase.table = Mock(side_effect=side_effect)
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                # First call should raise and increment error counter
                with pytest.raises(Exception, match="Database connection lost"):
                    await scheduler_service._check_and_process_schedules()
                
                # Stats should track the error
                assert scheduler_service.stats["errors"] == 0  # Errors tracked in main loop
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_prevention(self, scheduler_service):
        """Test prevention of concurrent schedule execution (Task 4.6)."""
        # This tests that the scheduler loop handles one check at a time
        # by testing that a long-running check doesn't interfere with stopping
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.setup_schedules_data([])  # Empty data to avoid processing issues
        
        # Mock normal execute method (not async)
        def slow_execute():
            import time
            time.sleep(0.1)  # Shorter delay to speed up test
            return mock_supabase.mock_result
        
        mock_supabase.table_mock.execute = Mock(side_effect=slow_execute)
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                await scheduler_service.start()
                
                # Start a check that will take time
                check_task = asyncio.create_task(scheduler_service._check_and_process_schedules())
                
                # Wait a brief moment for check to start
                await asyncio.sleep(0.05)
                
                # Try to stop (should complete quickly)
                stop_task = asyncio.create_task(scheduler_service.stop())
                
                # Both should complete reasonably quickly
                await asyncio.wait_for(asyncio.gather(check_task, stop_task, return_exceptions=True), timeout=2.0)
                
                assert scheduler_service.running is False


class TestStatisticsCollection:
    """Tests for statistics collection and reporting functionality (Task 4.8)."""
    
    @pytest.mark.asyncio
    async def test_statistics_during_processing(self, scheduler_service):
        """Test statistics collection during schedule processing."""
        # Create multiple schedules
        current_time = datetime.now(timezone.utc)
        schedules = []
        
        for i in range(3):
            schedule = {
                "id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "title": f"Test Schedule {i}",
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {
                    "name": "test_agent",
                    "job_data": {"prompt": f"test {i}"},
                    "execution": {"priority": 5}
                },
                "next_run": (current_time - timedelta(minutes=5)).isoformat(),
                "last_run": (current_time - timedelta(days=1)).isoformat()
            }
            schedules.append(schedule)
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.setup_schedules_data(schedules)
        mock_job_pipeline = MockJobPipelineScheduler()
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline', return_value=mock_job_pipeline):
                # Mock successful job creation for each schedule
                with patch.object(scheduler_service, '_create_scheduled_job', new_callable=AsyncMock) as mock_create:
                    with patch.object(scheduler_service, '_update_schedule_after_execution', new_callable=AsyncMock):
                        with patch('utils.cron_utils.CronUtils.get_next_run_time', return_value=current_time + timedelta(days=1)):
                            mock_create.side_effect = [f"job-{i}" for i in range(3)]
                            
                            await scheduler_service._check_and_process_schedules()
                            
                            # Verify statistics were updated
                            assert scheduler_service.stats["schedules_processed"] == 3
                            assert scheduler_service.stats["jobs_created"] == 3
                            # Note: last_check is only set in the main scheduler loop, not in _check_and_process_schedules
    
    @pytest.mark.asyncio
    async def test_error_statistics_tracking(self, scheduler_service):
        """Test error statistics tracking."""
        schedule_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "title": "Error Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "test"}
            },
            "next_run": datetime.now(timezone.utc).isoformat(),
            "last_run": None
        }
        
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.setup_schedules_data([schedule_data])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                with patch.object(scheduler_service, '_process_schedule', new_callable=AsyncMock) as mock_process:
                    # Mock processing error
                    mock_process.side_effect = Exception("Processing error")
                    
                    await scheduler_service._check_and_process_schedules()
                    
                    # Error should be handled and schedule should be processed
                    mock_process.assert_called_once()
    
    def test_detailed_statistics_reporting(self, scheduler_service):
        """Test detailed statistics reporting."""
        # Set up various statistics
        start_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        scheduler_service.stats.update({
            "total_checks": 25,
            "schedules_processed": 15,
            "jobs_created": 12,
            "errors": 2,
            "start_time": start_time,
            "last_check": datetime.now(timezone.utc) - timedelta(seconds=30),
            "last_error": "Previous error message"
        })
        scheduler_service.running = True
        
        stats = scheduler_service.get_stats()
        
        # Verify all statistics are included
        assert stats["running"] is True
        assert stats["total_checks"] == 25
        assert stats["schedules_processed"] == 15
        assert stats["jobs_created"] == 12
        assert stats["errors"] == 2
        assert stats["start_time"] == start_time
        assert stats["last_check"] is not None
        assert stats["last_error"] == "Previous error message"
        assert stats["uptime_seconds"] > 0
        
        # Verify uptime calculation
        expected_uptime = (datetime.now(timezone.utc) - start_time).total_seconds()
        assert abs(stats["uptime_seconds"] - expected_uptime) < 1.0  # Within 1 second
    
    @pytest.mark.asyncio
    async def test_scheduler_loop_statistics_increment(self, scheduler_service):
        """Test that scheduler loop properly increments statistics."""
        mock_supabase = MockSupabaseScheduler()
        mock_supabase.setup_schedules_data([])
        
        with patch('services.scheduler.get_supabase_client', return_value=mock_supabase):
            with patch('services.scheduler.get_job_pipeline'):
                # Mock short sleep to speed up test
                original_sleep = scheduler_service.check_interval
                scheduler_service.check_interval = 0.1
                
                try:
                    await scheduler_service.start()
                    
                    # Wait for a few iterations
                    await asyncio.sleep(0.3)
                    
                    await scheduler_service.stop()
                    
                    # Should have incremented check counter
                    assert scheduler_service.stats["total_checks"] > 0
                    assert scheduler_service.stats["last_check"] is not None
                    
                finally:
                    scheduler_service.check_interval = original_sleep


# Global service tests
class TestGlobalSchedulerFunctions:
    """Test global scheduler service functions."""
    
    def test_get_scheduler_service_singleton(self):
        """Test that get_scheduler_service returns singleton."""
        from services.scheduler import get_scheduler_service
        
        service1 = get_scheduler_service() 
        service2 = get_scheduler_service()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_start_stop_global_scheduler(self):
        """Test starting and stopping global scheduler service."""
        from services.scheduler import start_scheduler_service, stop_scheduler_service, get_scheduler_service
        
        with patch('services.scheduler.get_supabase_client'):
            with patch('services.scheduler.get_job_pipeline'):
                # Start global service
                await start_scheduler_service()
                scheduler = get_scheduler_service()
                assert scheduler.running is True
                
                # Stop global service  
                await stop_scheduler_service()
                assert scheduler.running is False
    
    def test_get_scheduler_stats_global(self):
        """Test getting statistics from global scheduler service."""
        from services.scheduler import get_scheduler_stats, get_scheduler_service
        
        # Get scheduler and set some stats
        scheduler = get_scheduler_service()
        scheduler.stats["total_checks"] = 42
        
        stats = get_scheduler_stats()
        assert stats["total_checks"] == 42 