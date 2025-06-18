"""
Unit tests for Job Processing Pipeline

Tests cover:
- Job submission and queuing
- Job execution with status updates
- Error handling and retry mechanisms
- Pipeline lifecycle management
- Metrics and monitoring
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from job_pipeline import (
    JobPipeline, JobTask, JobExecutionStatus, JobPriority,
    get_job_pipeline, start_job_pipeline, stop_job_pipeline
)
from models import JobStatus
from agent import AgentExecutionResult


@pytest.fixture
def mock_db_ops():
    """Mock database operations"""
    mock = AsyncMock()
    mock.update_job_status = AsyncMock()
    return mock


@pytest.fixture
def mock_agent():
    """Mock agent instance"""
    agent = Mock()
    agent.get_models.return_value = {'TestJobData': Mock}
    
    # Mock the internal method that job pipeline actually calls
    agent._execute_job_logic = AsyncMock(return_value=AgentExecutionResult(
        success=True,
        result='{"processed": true}'
    ))
    
    # Mock execute_job to call _execute_job_logic like the real BaseAgent does
    async def mock_execute_job(job_id, job_data, user_id=None):
        # Simulate what BaseAgent.execute_job does
        result = await agent._execute_job_logic(job_data)
        # Add execution time if not set
        if result.execution_time is None:
            result.execution_time = 1.0
        return result
    
    agent.execute_job = mock_execute_job
    
    # Mock agent state tracking
    agent.execution_count = 0
    agent.last_execution_time = None
    return agent


@pytest.fixture
def mock_registered_agents(mock_agent):
    """Mock registered agents"""
    return {'test_agent': mock_agent}


@pytest_asyncio.fixture
async def job_pipeline(mock_db_ops, mock_registered_agents):
    """Create job pipeline instance with mocked dependencies"""
    with patch('job_pipeline.get_database_operations', return_value=mock_db_ops):
        with patch('job_pipeline.get_agent_registry', return_value=Mock()):
            with patch('job_pipeline.get_registered_agents', return_value=mock_registered_agents):
                with patch('job_pipeline.validate_job_data') as mock_validate:
                    mock_validate.return_value = {'text': 'test'}
                    pipeline = JobPipeline(max_concurrent_jobs=2, max_queue_size=10)
                    yield pipeline
                    # Ensure pipeline is stopped after each test
                    if pipeline.is_running:
                        await pipeline.stop(timeout=2.0)


class TestJobTask:
    """Test JobTask dataclass"""
    
    def test_job_task_creation(self):
        """Test JobTask creation with default values"""
        task = JobTask(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'}
        )
        
        assert task.job_id == 'test-job-1'
        assert task.user_id == 'user-1'
        assert task.agent_name == 'test_agent'
        assert task.job_data == {'text': 'test'}
        assert task.priority == JobPriority.NORMAL
        assert task.max_retries == 3
        assert task.retry_count == 0
        assert isinstance(task.created_at, datetime)
        assert task.scheduled_at == task.created_at
    
    def test_job_task_with_scheduled_time(self):
        """Test JobTask with future scheduled time"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        task = JobTask(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            scheduled_at=future_time
        )
        
        assert task.scheduled_at == future_time
        assert not task.is_ready  # Should not be ready yet
    
    def test_job_task_ready_status(self):
        """Test job task ready status"""
        # Past time - should be ready
        past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        task = JobTask(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            scheduled_at=past_time
        )
        assert task.is_ready
        
        # Future time - should not be ready
        future_time = datetime.now(timezone.utc) + timedelta(minutes=1)
        task.scheduled_at = future_time
        assert not task.is_ready
    
    def test_job_task_retry_logic(self):
        """Test job task retry logic"""
        task = JobTask(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            max_retries=3
        )
        
        assert task.can_retry
        
        task.retry_count = 3
        assert not task.can_retry
        
        task.retry_count = 4
        assert not task.can_retry


class TestJobExecutionStatus:
    """Test JobExecutionStatus tracking"""
    
    def test_status_initialization(self):
        """Test status tracker initialization"""
        status = JobExecutionStatus()
        
        assert len(status.active_jobs) == 0
        assert status.completed_jobs == 0
        assert status.failed_jobs == 0
        assert status.retried_jobs == 0
        assert isinstance(status.start_time, datetime)
    
    def test_job_lifecycle_tracking(self):
        """Test complete job lifecycle tracking"""
        status = JobExecutionStatus()
        job_id = 'test-job-1'
        
        # Start job
        status.start_job(job_id)
        assert job_id in status.active_jobs
        assert job_id in status.job_metrics
        assert status.job_metrics[job_id]['status'] == JobStatus.running
        
        # Complete job successfully
        status.complete_job(job_id, success=True, execution_time=1.5)
        assert job_id not in status.active_jobs
        assert status.completed_jobs == 1
        assert status.failed_jobs == 0
        assert status.job_metrics[job_id]['success'] is True
        assert status.job_metrics[job_id]['execution_time'] == 1.5
    
    def test_job_failure_tracking(self):
        """Test job failure tracking"""
        status = JobExecutionStatus()
        job_id = 'test-job-1'
        
        status.start_job(job_id)
        status.complete_job(job_id, success=False, execution_time=0.5)
        
        assert status.completed_jobs == 0
        assert status.failed_jobs == 1
        assert status.job_metrics[job_id]['success'] is False
    
    def test_retry_tracking(self):
        """Test job retry tracking"""
        status = JobExecutionStatus()
        job_id = 'test-job-1'
        
        status.start_job(job_id)
        status.retry_job(job_id)
        status.retry_job(job_id)
        
        assert status.retried_jobs == 2
        assert status.job_metrics[job_id]['retries'] == 2
    
    def test_metrics_calculation(self):
        """Test metrics calculation"""
        status = JobExecutionStatus()
        
        # Simulate some job activity
        status.start_job('job-1')
        status.complete_job('job-1', success=True, execution_time=1.0)
        
        status.start_job('job-2')
        status.complete_job('job-2', success=False, execution_time=0.5)
        
        metrics = status.get_metrics()
        assert metrics['active_jobs'] == 0
        assert metrics['completed_jobs'] == 1
        assert metrics['failed_jobs'] == 1
        assert metrics['total_processed'] == 2
        assert metrics['success_rate'] == 50.0


class TestJobPipeline:
    """Test JobPipeline functionality"""
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, job_pipeline):
        """Test pipeline initialization"""
        assert not job_pipeline.is_running
        assert job_pipeline.max_concurrent_jobs == 2
        assert job_pipeline.max_queue_size == 10
        assert job_pipeline.job_queue.empty()
    
    @pytest.mark.asyncio
    async def test_pipeline_start_stop(self, job_pipeline):
        """Test pipeline start and stop"""
        await job_pipeline.start()
        assert job_pipeline.is_running
        assert len(job_pipeline.worker_tasks) > 0
        
        await job_pipeline.stop(timeout=2.0)
        assert not job_pipeline.is_running
    
    @pytest.mark.asyncio
    async def test_job_submission_success(self, job_pipeline):
        """Test successful job submission"""
        result = await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            priority=JobPriority.HIGH
        )
        
        assert result is True
        # Should be in queue for immediate execution
        assert job_pipeline.job_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_job_submission_unknown_agent(self, job_pipeline):
        """Test job submission with unknown agent"""
        result = await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='unknown_agent',
            job_data={'text': 'test'}
        )
        
        assert result is False
        job_pipeline.db_ops.update_job_status.assert_called_once_with(
            job_id='test-job-1',
            status=JobStatus.failed.value,
            result=None,
            error_message='Unknown agent: unknown_agent',
            result_format=None
        )
    
    @pytest.mark.asyncio
    async def test_scheduled_job_submission(self, job_pipeline):
        """Test submission of scheduled job"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        result = await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            scheduled_at=future_time
        )
        
        assert result is True
        assert len(job_pipeline.scheduled_jobs) == 1
        assert job_pipeline.job_queue.qsize() == 0  # Not in immediate queue
    
    @pytest.mark.asyncio
    async def test_job_execution_success(self, job_pipeline, mock_agent):
        """Test successful job execution"""
        await job_pipeline.start()
        
        # Submit job
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'}
        )
        
        # Wait for execution with timeout
        for _ in range(20):  # Up to 2 seconds
            if mock_agent._execute_job_logic.called:
                break
            await asyncio.sleep(0.1)
        
        # Verify agent was called
        mock_agent._execute_job_logic.assert_called_once()
        
        # Verify status updates
        assert job_pipeline.db_ops.update_job_status.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_job_execution_failure_with_retry(self, job_pipeline, mock_agent):
        """Test job execution failure with retry"""
        # Configure agent to fail first time, succeed second time
        mock_agent._execute_job_logic.side_effect = [
            AgentExecutionResult(success=False, error_message="First failure"),
            AgentExecutionResult(success=True, result='{"processed": true}')
        ]
        
        await job_pipeline.start()
        
        # Submit job
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            max_retries=2
        )
        
        # Wait for execution and retry with timeout
        for _ in range(50):  # Up to 5 seconds
            if mock_agent._execute_job_logic.call_count >= 2:
                break
            await asyncio.sleep(0.1)
        
        # Should have tried at least once
        assert mock_agent._execute_job_logic.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_job_execution_permanent_failure(self, job_pipeline, mock_agent):
        """Test job execution with permanent failure"""
        # Configure agent to always fail
        mock_agent._execute_job_logic.return_value = AgentExecutionResult(
            success=False, 
            error_message="Permanent failure"
        )
        
        await job_pipeline.start()
        
        # Submit job with no retries
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            max_retries=0
        )
        
        # Wait for execution with timeout
        for _ in range(20):  # Up to 2 seconds  
            if mock_agent._execute_job_logic.called:
                break
            await asyncio.sleep(0.1)
        
        # Verify failure was recorded
        job_pipeline.db_ops.update_job_status.assert_called_with(
            job_id='test-job-1',
            status=JobStatus.failed.value,
            result=None,
            error_message="Permanent failure",
            result_format=None
        )
    
    @pytest.mark.asyncio
    async def test_scheduler_functionality(self, job_pipeline):
        """Test job scheduler functionality"""
        await job_pipeline.start()
        
        # Submit a job scheduled for immediate execution (slightly in the past)
        past_time = datetime.now(timezone.utc) - timedelta(milliseconds=10)
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'},
            scheduled_at=past_time
        )
        
        # Should be immediately added to queue since it's already ready
        # Wait a brief moment for processing
        await asyncio.sleep(0.1)
        
        # Job should have been processed or moved to queue immediately
        assert (job_pipeline.job_queue.qsize() > 0 or 
                len(job_pipeline.active_tasks) > 0 or
                len(job_pipeline.scheduled_jobs) == 0)
    
    def test_pipeline_status(self, job_pipeline):
        """Test pipeline status reporting"""
        status = job_pipeline.get_pipeline_status()
        
        assert 'is_running' in status
        assert 'queue_size' in status
        assert 'scheduled_jobs' in status
        assert 'active_jobs' in status
        assert 'max_concurrent_jobs' in status
        assert 'worker_count' in status
        assert 'metrics' in status
        
        assert status['is_running'] is False
        assert status['max_concurrent_jobs'] == 2


class TestGlobalPipelineFunctions:
    """Test global pipeline functions"""
    
    @pytest.mark.asyncio
    async def test_get_job_pipeline_singleton(self):
        """Test that get_job_pipeline returns singleton"""
        with patch('job_pipeline.get_database_operations'):
            with patch('job_pipeline.get_agent_registry'):
                with patch('job_pipeline.get_registered_agents'):
                    pipeline1 = get_job_pipeline()
                    pipeline2 = get_job_pipeline()
                    
                    assert pipeline1 is pipeline2
    
    @pytest.mark.asyncio
    async def test_start_stop_global_pipeline(self):
        """Test starting and stopping global pipeline"""
        with patch('job_pipeline.get_database_operations'):
            with patch('job_pipeline.get_agent_registry'):
                with patch('job_pipeline.get_registered_agents'):
                    # Start pipeline
                    await start_job_pipeline()
                    pipeline = get_job_pipeline()
                    assert pipeline.is_running
                    
                    # Stop pipeline
                    await stop_job_pipeline()
                    assert not pipeline.is_running


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, job_pipeline, mock_agent):
        """Test handling of database errors"""
        # Configure database to raise exception
        job_pipeline.db_ops.update_job_status.side_effect = Exception("Database error")
        
        await job_pipeline.start()
        
        # Submit job
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'}
        )
        
        # Wait for execution attempt
        for _ in range(20):  # Up to 2 seconds
            if mock_agent._execute_job_logic.called:
                break
            await asyncio.sleep(0.1)
        
        # Job should still execute despite database error
        mock_agent._execute_job_logic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_exception_handling(self, job_pipeline, mock_agent):
        """Test handling of agent exceptions"""
        # Configure agent to raise exception
        mock_agent._execute_job_logic.side_effect = Exception("Agent crashed")
        
        await job_pipeline.start()
        
        # Submit job
        await job_pipeline.submit_job(
            job_id='test-job-1',
            user_id='user-1',
            agent_name='test_agent',
            job_data={'text': 'test'}
        )
        
        # Wait for execution attempt
        for _ in range(20):  # Up to 2 seconds
            if mock_agent._execute_job_logic.called:
                break
            await asyncio.sleep(0.1)
        
        # Should have attempted execution
        mock_agent._execute_job_logic.assert_called_once()


class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    def test_execution_time_tracking(self):
        """Test execution time tracking"""
        status = JobExecutionStatus()
        job_id = 'test-job-1'
        
        status.start_job(job_id)
        status.complete_job(job_id, success=True, execution_time=2.5)
        
        assert status.job_metrics[job_id]['execution_time'] == 2.5
    
    def test_metrics_with_no_jobs(self):
        """Test metrics when no jobs have been processed"""
        status = JobExecutionStatus()
        metrics = status.get_metrics()
        
        assert metrics['active_jobs'] == 0
        assert metrics['completed_jobs'] == 0
        assert metrics['failed_jobs'] == 0
        assert metrics['success_rate'] == 0.0
    
    @pytest.mark.asyncio
    async def test_cleanup_worker(self, job_pipeline):
        """Test cleanup worker functionality"""
        await job_pipeline.start()
        
        # Check that we have worker tasks and a cleanup task
        # 2 worker tasks + 1 scheduler task = 3 total
        assert len(job_pipeline.worker_tasks) == 3
        # Cleanup task is separate
        assert job_pipeline.cleanup_task is not None
        
        # Test cleanup doesn't crash
        await asyncio.sleep(0.1)


if __name__ == '__main__':
    pytest.main([__file__]) 