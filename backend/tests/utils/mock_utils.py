"""
Mock utilities for job pipeline integration testing.

Provides mock implementations of job pipeline components for testing
schedule-related functionality without dependencies on external services.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import pytest

from tests.fixtures.schedule_fixtures import ScheduleFixtures


class MockJobPipeline:
    """Mock implementation of the job pipeline for testing."""
    
    def __init__(self):
        self.created_jobs = []
        self.job_statuses = {}
        self.execution_results = {}
        self.execution_errors = {}
        self.should_fail = False
        self.failure_reason = "Mock execution failure"
        self.execution_delay = 0.1  # Default delay in seconds
        
    async def create_job(
        self,
        user_id: str,
        agent_name: str,
        agent_config_data: Dict[str, Any],
        schedule_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Mock job creation.
        
        Returns:
            Job ID of the created job
        """
        job_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        job_data = {
            "id": job_id,
            "user_id": user_id,
            "agent_name": agent_name,
            "agent_config_data": agent_config_data,
            "schedule_id": schedule_id,
            "priority": priority,
            "status": "pending",
            "created_at": current_time,
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error_message": None
        }
        
        self.created_jobs.append(job_data)
        self.job_statuses[job_id] = "pending"
        
        # Simulate async job processing
        if not self.should_fail:
            asyncio.create_task(self._simulate_job_execution(job_id))
        else:
            asyncio.create_task(self._simulate_job_failure(job_id))
        
        return job_id
    
    async def _simulate_job_execution(self, job_id: str):
        """Simulate successful job execution."""
        await asyncio.sleep(self.execution_delay)
        
        current_time = datetime.now(timezone.utc)
        self.job_statuses[job_id] = "running"
        
        # Find and update job data
        job_data = next((j for j in self.created_jobs if j["id"] == job_id), None)
        if job_data:
            job_data["status"] = "running"
            job_data["started_at"] = current_time
        
        # Simulate execution time
        await asyncio.sleep(self.execution_delay)
        
        # Complete the job
        completion_time = datetime.now(timezone.utc)
        self.job_statuses[job_id] = "completed"
        self.execution_results[job_id] = "Mock job completed successfully"
        
        if job_data:
            job_data["status"] = "completed"
            job_data["completed_at"] = completion_time
            job_data["result"] = self.execution_results[job_id]
    
    async def _simulate_job_failure(self, job_id: str):
        """Simulate job execution failure."""
        await asyncio.sleep(self.execution_delay)
        
        current_time = datetime.now(timezone.utc)
        self.job_statuses[job_id] = "running"
        
        # Find and update job data
        job_data = next((j for j in self.created_jobs if j["id"] == job_id), None)
        if job_data:
            job_data["status"] = "running"
            job_data["started_at"] = current_time
        
        # Simulate execution time
        await asyncio.sleep(self.execution_delay)
        
        # Fail the job
        failure_time = datetime.now(timezone.utc)
        self.job_statuses[job_id] = "failed"
        self.execution_errors[job_id] = self.failure_reason
        
        if job_data:
            job_data["status"] = "failed"
            job_data["completed_at"] = failure_time
            job_data["error_message"] = self.failure_reason
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """Get job status by ID."""
        return self.job_statuses.get(job_id)
    
    def get_job_data(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get complete job data by ID."""
        return next((j for j in self.created_jobs if j["id"] == job_id), None)
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all created jobs."""
        return self.created_jobs.copy()
    
    def get_jobs_by_schedule(self, schedule_id: str) -> List[Dict[str, Any]]:
        """Get jobs created for a specific schedule."""
        return [j for j in self.created_jobs if j.get("schedule_id") == schedule_id]
    
    def set_execution_behavior(
        self,
        should_fail: bool = False,
        failure_reason: str = "Mock execution failure",
        execution_delay: float = 0.1
    ):
        """Configure mock execution behavior."""
        self.should_fail = should_fail
        self.failure_reason = failure_reason
        self.execution_delay = execution_delay
    
    def reset(self):
        """Reset all mock data."""
        self.created_jobs.clear()
        self.job_statuses.clear()
        self.execution_results.clear()
        self.execution_errors.clear()
        self.should_fail = False
        self.failure_reason = "Mock execution failure"
        self.execution_delay = 0.1


class MockAgentService:
    """Mock implementation of agent service for testing."""
    
    def __init__(self):
        self.available_agents = {
            "test_agent": {
                "name": "test_agent",
                "description": "Test agent for unit testing",
                "capabilities": ["text_processing", "data_analysis"],
                "status": "available"
            },
            "data_processor": {
                "name": "data_processor",
                "description": "Data processing agent",
                "capabilities": ["data_processing", "file_handling"],
                "status": "available"
            },
            "report_generator": {
                "name": "report_generator",
                "description": "Report generation agent",
                "capabilities": ["report_generation", "visualization"],
                "status": "available"
            }
        }
        self.unavailable_agents = set()
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        return self.available_agents.get(agent_name)
    
    def is_agent_available(self, agent_name: str) -> bool:
        """Check if agent is available."""
        return (
            agent_name in self.available_agents and 
            agent_name not in self.unavailable_agents
        )
    
    def set_agent_unavailable(self, agent_name: str):
        """Mark an agent as unavailable."""
        self.unavailable_agents.add(agent_name)
    
    def set_agent_available(self, agent_name: str):
        """Mark an agent as available."""
        self.unavailable_agents.discard(agent_name)
    
    def validate_agent_config(self, agent_name: str, config_data: Dict[str, Any]) -> bool:
        """Validate agent configuration data."""
        if not self.is_agent_available(agent_name):
            return False
        
        # Basic validation - ensure required fields exist
        job_data = config_data.get("job_data", {})
        return bool(job_data and (job_data.get("prompt") or job_data.get("input_file")))
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return [name for name in self.available_agents.keys() 
                if name not in self.unavailable_agents]


class MockJobQueue:
    """Mock implementation of job queue for testing."""
    
    def __init__(self):
        self.queue = []
        self.processing = {}
        self.completed = {}
        self.failed = {}
        self.max_concurrent = 3
        self.processing_delay = 0.1
    
    async def enqueue_job(
        self,
        job_id: str,
        job_data: Dict[str, Any],
        priority: int = 5
    ):
        """Add job to the queue."""
        queue_item = {
            "job_id": job_id,
            "job_data": job_data,
            "priority": priority,
            "enqueued_at": datetime.now(timezone.utc),
            "attempts": 0
        }
        
        # Insert based on priority (higher priority first)
        inserted = False
        for i, item in enumerate(self.queue):
            if priority > item["priority"]:
                self.queue.insert(i, queue_item)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(queue_item)
    
    async def process_queue(self):
        """Process jobs in the queue."""
        while self.queue and len(self.processing) < self.max_concurrent:
            job_item = self.queue.pop(0)
            job_id = job_item["job_id"]
            
            self.processing[job_id] = {
                **job_item,
                "started_at": datetime.now(timezone.utc)
            }
            
            # Simulate async processing
            asyncio.create_task(self._process_job(job_id, job_item))
    
    async def _process_job(self, job_id: str, job_item: Dict[str, Any]):
        """Simulate job processing."""
        await asyncio.sleep(self.processing_delay)
        
        # Move from processing to completed
        if job_id in self.processing:
            completed_item = self.processing.pop(job_id)
            completed_item["completed_at"] = datetime.now(timezone.utc)
            completed_item["result"] = f"Processed job {job_id}"
            self.completed[job_id] = completed_item
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
    
    def get_processing_count(self) -> int:
        """Get number of jobs currently processing."""
        return len(self.processing)
    
    def is_job_processing(self, job_id: str) -> bool:
        """Check if job is currently processing."""
        return job_id in self.processing
    
    def is_job_completed(self, job_id: str) -> bool:
        """Check if job is completed."""
        return job_id in self.completed
    
    def clear(self):
        """Clear all queue data."""
        self.queue.clear()
        self.processing.clear()
        self.completed.clear()
        self.failed.clear()


class JobPipelineMockManager:
    """Manager for coordinating all job pipeline mocks."""
    
    def __init__(self):
        self.job_pipeline = MockJobPipeline()
        self.agent_service = MockAgentService()
        self.job_queue = MockJobQueue()
        self._active_patches = []
    
    def setup_mocks(self) -> Dict[str, Mock]:
        """Set up all mocks and return mock objects."""
        mocks = {}
        
        # Mock job pipeline
        job_pipeline_mock = Mock()
        job_pipeline_mock.create_job = AsyncMock(side_effect=self.job_pipeline.create_job)
        job_pipeline_mock.get_job_status = Mock(side_effect=self.job_pipeline.get_job_status)
        job_pipeline_mock.get_job_data = Mock(side_effect=self.job_pipeline.get_job_data)
        mocks["job_pipeline"] = job_pipeline_mock
        
        # Mock agent service
        agent_service_mock = Mock()
        agent_service_mock.get_agent_info = Mock(side_effect=self.agent_service.get_agent_info)
        agent_service_mock.is_agent_available = Mock(side_effect=self.agent_service.is_agent_available)
        agent_service_mock.validate_agent_config = Mock(side_effect=self.agent_service.validate_agent_config)
        mocks["agent_service"] = agent_service_mock
        
        # Mock job queue
        job_queue_mock = Mock()
        job_queue_mock.enqueue_job = AsyncMock(side_effect=self.job_queue.enqueue_job)
        job_queue_mock.process_queue = AsyncMock(side_effect=self.job_queue.process_queue)
        job_queue_mock.get_queue_size = Mock(side_effect=self.job_queue.get_queue_size)
        mocks["job_queue"] = job_queue_mock
        
        return mocks
    
    def configure_job_execution(
        self,
        should_fail: bool = False,
        failure_reason: str = "Mock execution failure",
        execution_delay: float = 0.1
    ):
        """Configure job execution behavior."""
        self.job_pipeline.set_execution_behavior(should_fail, failure_reason, execution_delay)
    
    def configure_agent_availability(self, agent_name: str, available: bool = True):
        """Configure agent availability."""
        if available:
            self.agent_service.set_agent_available(agent_name)
        else:
            self.agent_service.set_agent_unavailable(agent_name)
    
    def get_created_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs created during testing."""
        return self.job_pipeline.get_all_jobs()
    
    def get_jobs_for_schedule(self, schedule_id: str) -> List[Dict[str, Any]]:
        """Get jobs created for a specific schedule."""
        return self.job_pipeline.get_jobs_by_schedule(schedule_id)
    
    def reset_all(self):
        """Reset all mock states."""
        self.job_pipeline.reset()
        self.job_queue.clear()
        # Don't reset agent service as it contains static data
    
    @asynccontextmanager
    async def patch_job_pipeline(self, target_modules: List[str]):
        """Context manager to patch job pipeline modules."""
        mocks = self.setup_mocks()
        patches = []
        
        try:
            for module in target_modules:
                if "job_pipeline" in module:
                    patch_obj = patch(module, mocks["job_pipeline"])
                elif "agent_service" in module:
                    patch_obj = patch(module, mocks["agent_service"])
                elif "job_queue" in module:
                    patch_obj = patch(module, mocks["job_queue"])
                else:
                    continue
                
                patches.append(patch_obj)
                patch_obj.start()
            
            yield mocks
            
        finally:
            for patch_obj in patches:
                patch_obj.stop()


# Test scenario builders
class JobPipelineTestScenarios:
    """Pre-built test scenarios for common job pipeline testing situations."""
    
    @staticmethod
    def successful_job_execution() -> JobPipelineMockManager:
        """Scenario: All jobs execute successfully."""
        manager = JobPipelineMockManager()
        manager.configure_job_execution(should_fail=False, execution_delay=0.1)
        return manager
    
    @staticmethod
    def failing_job_execution(failure_reason: str = "Agent temporarily unavailable") -> JobPipelineMockManager:
        """Scenario: Jobs fail during execution."""
        manager = JobPipelineMockManager()
        manager.configure_job_execution(
            should_fail=True,
            failure_reason=failure_reason,
            execution_delay=0.1
        )
        return manager
    
    @staticmethod
    def agent_unavailable_scenario(agent_name: str = "test_agent") -> JobPipelineMockManager:
        """Scenario: Specific agent is unavailable."""
        manager = JobPipelineMockManager()
        manager.configure_agent_availability(agent_name, available=False)
        return manager
    
    @staticmethod
    def mixed_execution_scenario() -> JobPipelineMockManager:
        """Scenario: Mix of successful and failed jobs."""
        manager = JobPipelineMockManager()
        # This would require more complex setup for alternating success/failure
        return manager


# Pytest fixtures
@pytest.fixture
def mock_job_pipeline():
    """Pytest fixture providing MockJobPipeline."""
    return MockJobPipeline()


@pytest.fixture
def mock_agent_service():
    """Pytest fixture providing MockAgentService."""
    return MockAgentService()


@pytest.fixture
def mock_job_queue():
    """Pytest fixture providing MockJobQueue."""
    return MockJobQueue()


@pytest.fixture
def job_pipeline_manager():
    """Pytest fixture providing JobPipelineMockManager."""
    manager = JobPipelineMockManager()
    yield manager
    manager.reset_all()


@pytest.fixture
def successful_job_scenario():
    """Pytest fixture for successful job execution scenario."""
    return JobPipelineTestScenarios.successful_job_execution()


@pytest.fixture
def failing_job_scenario():
    """Pytest fixture for failing job execution scenario."""
    return JobPipelineTestScenarios.failing_job_execution()


@pytest.fixture
def agent_unavailable_scenario():
    """Pytest fixture for agent unavailable scenario."""
    return JobPipelineTestScenarios.agent_unavailable_scenario()


# Helper functions for common mock patterns
def create_job_creation_mock(
    job_id: Optional[str] = None,
    should_fail: bool = False,
    failure_reason: str = "Mock job creation failed"
) -> AsyncMock:
    """Create a mock for job creation with configurable behavior."""
    if should_fail:
        mock = AsyncMock(side_effect=Exception(failure_reason))
    else:
        result_job_id = job_id or str(uuid.uuid4())
        mock = AsyncMock(return_value=result_job_id)
    
    return mock


def create_agent_validation_mock(
    valid_agents: Optional[List[str]] = None,
    always_valid: bool = True
) -> Mock:
    """Create a mock for agent validation with configurable behavior."""
    if always_valid:
        return Mock(return_value=True)
    
    valid_agents = valid_agents or ["test_agent", "data_processor"]
    
    def validate_agent(agent_name: str, config_data: Dict[str, Any]) -> bool:
        return agent_name in valid_agents
    
    return Mock(side_effect=validate_agent) 