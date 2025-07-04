"""
Global test configuration and fixtures.

Provides common fixtures used across all test modules including:
- Database session management
- Authentication mocking
- Test data utilities
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

# Mock database session for testing
class MockAsyncSession:
    """Mock AsyncSession for testing without real database."""
    
    def __init__(self):
        self.executed_queries = []
        self.mock_results = {}
        self._transaction_active = False
        self._stored_records = {}  # Track records by ID for state persistence
        self._stored_jobs = {}  # Track jobs separately for cascade deletion
        
    async def execute(self, query, params=None):
        """Mock execute method."""
        query_str = str(query)
        self.executed_queries.append({"query": query_str, "params": params})
        
        # Return mock result based on query
        if "INSERT" in query_str.upper():
            # Mock insert result
            result = Mock()
            row_mock = Mock()
            # For inserts, include all provided params plus common fields
            row_data = params.copy() if params else {}
            row_data.update({
                "id": row_data.get("id", str(uuid.uuid4())),
                "created_at": row_data.get("created_at", datetime.now(timezone.utc)),
                "updated_at": row_data.get("updated_at", datetime.now(timezone.utc)),
                "enabled": row_data.get("enabled", True),
                "title": row_data.get("title", "Test Schedule"),
                "user_id": row_data.get("user_id", str(uuid.uuid4()))
            })
            row_mock._mapping = row_data
            
            # Store the record for future queries
            record_id = row_data.get("id")
            if record_id:
                if "jobs" in query_str.lower():
                    self._stored_jobs[record_id] = row_data
                else:
                    self._stored_records[record_id] = row_data
                
            result.fetchone.return_value = row_mock
            return result
        elif "SELECT" in query_str.upper():
            # Mock select result
            result = Mock()
            if "COUNT" in query_str.upper():
                result.scalar.return_value = len(self._stored_records)
                result.fetchall.return_value = []
            else:
                # Determine if this is querying jobs or schedules
                is_job_query = "jobs" in query_str.lower()
                storage = self._stored_jobs if is_job_query else self._stored_records
                
                # Check if this is a query by ID
                if params and "id" in params:
                    record_id = params["id"]
                    if record_id in storage:
                        row_mock = Mock()
                        row_mock._mapping = storage[record_id]
                        result.fetchone.return_value = row_mock
                        result.fetchall.return_value = [row_mock]
                    else:
                        result.fetchone.return_value = None
                        result.fetchall.return_value = []
                else:
                    # Return filtered records
                    mock_rows = []
                    for record_data in storage.values():
                        # Apply filters
                        matches = True
                        
                        # Filter by user_id if specified
                        if params and "user_id" in params:
                            if record_data.get("user_id") != params["user_id"]:
                                matches = False
                        
                        # Filter by schedule_id for jobs if specified
                        if params and "schedule_id" in params:
                            if record_data.get("schedule_id") != params["schedule_id"]:
                                matches = False
                        
                        if matches:
                            row_mock = Mock()
                            row_mock._mapping = record_data
                            mock_rows.append(row_mock)
                    
                    if mock_rows:
                        result.fetchone.return_value = mock_rows[0]
                        result.fetchall.return_value = mock_rows
                    else:
                        # Provide realistic default data if no stored data and no user filtering
                        if not params or "user_id" not in params:
                            row_mock = Mock()
                            # Provide realistic schedule data for selects when no stored data
                            row_data = {
                                "id": str(uuid.uuid4()),
                                "user_id": params.get("user_id", str(uuid.uuid4())) if params else str(uuid.uuid4()),
                                "title": "Test Schedule",
                                "description": "Test description",
                                "agent_name": "test_agent",
                                "cron_expression": "0 9 * * *",
                                "enabled": True,
                                "timezone": "UTC",
                                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}},
                                "next_run": datetime.now(timezone.utc) + timedelta(hours=1),
                                "last_run": None,
                                "created_at": datetime.now(timezone.utc),
                                "updated_at": datetime.now(timezone.utc)
                            }
                            row_mock._mapping = row_data
                            result.fetchone.return_value = row_mock
                            result.fetchall.return_value = [row_mock]
                        else:
                            result.fetchone.return_value = None
                            result.fetchall.return_value = []
            return result
        elif "UPDATE" in query_str.upper():
            # Mock update result
            result = Mock()
            result.rowcount = 1
            row_mock = Mock()
            
            # Determine if this is updating jobs or schedules
            is_job_query = "jobs" in query_str.lower()
            storage = self._stored_jobs if is_job_query else self._stored_records
            
            # Find the record to update
            record_id = params.get("id") if params else None
            if record_id and record_id in storage:
                # Update the stored record
                existing_data = storage[record_id].copy()
                if params:
                    existing_data.update(params)
                existing_data["updated_at"] = datetime.now(timezone.utc)
                storage[record_id] = existing_data
                row_mock._mapping = existing_data
            else:
                # For updates, merge the update params with existing data
                row_data = {
                    "id": record_id or str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "title": "Test Schedule",
                    "description": "Test description", 
                    "agent_name": "test_agent",
                    "cron_expression": "0 9 * * *",
                    "enabled": True,
                    "timezone": "UTC",
                    "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}},
                    "next_run": datetime.now(timezone.utc) + timedelta(hours=1),
                    "last_run": None,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                # Override with any update params
                if params:
                    row_data.update(params)
                row_mock._mapping = row_data
                
                # Store the updated record
                if record_id:
                    storage[record_id] = row_data
                    
            result.fetchone.return_value = row_mock
            return result
        elif "DELETE" in query_str.upper():
            # Mock delete result
            result = Mock()
            
            # Determine if this is deleting jobs or schedules
            is_job_query = "jobs" in query_str.lower()
            
            # Remove from stored records if ID is provided
            record_id = params.get("id") if params else None
            if record_id:
                deleted_count = 0
                
                if is_job_query:
                    # Delete from jobs
                    if record_id in self._stored_jobs:
                        del self._stored_jobs[record_id]
                        deleted_count = 1
                else:
                    # Delete from schedules - also implement cascade deletion for jobs
                    if record_id in self._stored_records:
                        del self._stored_records[record_id]
                        deleted_count = 1
                        
                        # Cascade delete associated jobs
                        jobs_to_delete = []
                        for job_id, job_data in self._stored_jobs.items():
                            if job_data.get("schedule_id") == record_id:
                                jobs_to_delete.append(job_id)
                        
                        for job_id in jobs_to_delete:
                            del self._stored_jobs[job_id]
                
                result.rowcount = deleted_count
            else:
                result.rowcount = 0
                
            return result
        
        # Default mock result
        result = Mock()
        result.fetchone.return_value = None
        result.fetchall.return_value = []
        result.scalar.return_value = 0
        return result
    
    async def commit(self):
        """Mock commit method."""
        pass
    
    async def rollback(self):
        """Mock rollback method."""
        pass
    
    async def close(self):
        """Mock close method."""
        pass
    
    def setup_mock_result(self, query_pattern: str, result_data: Any):
        """Setup mock result for specific query patterns."""
        self.mock_results[query_pattern] = result_data


@pytest.fixture
def test_db_session():
    """
    Test database session fixture.
    
    Provides a mock database session for integration tests.
    In a real implementation, this would connect to a test database.
    """
    session = MockAsyncSession()
    return session


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_schedule_id():
    """Generate a test schedule ID."""
    return str(uuid.uuid4())


@pytest.fixture
def test_job_id():
    """Generate a test job ID."""
    return str(uuid.uuid4())


@pytest.fixture
def current_time():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# Event loop configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 