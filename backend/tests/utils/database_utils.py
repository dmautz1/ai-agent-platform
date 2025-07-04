"""
Database test utilities for schedule-related testing.

Provides database setup, teardown, and helper functions for testing
schedule operations with proper isolation and cleanup.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

import pytest
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_database_client
from models.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from tests.fixtures.schedule_fixtures import ScheduleFixtures


class DatabaseTestUtils:
    """Database utilities for schedule testing."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.created_schedules = []
        self.created_jobs = []
        
    async def create_test_schedule(
        self,
        user_id: str,
        schedule_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test schedule in the database.
        
        Args:
            user_id: User ID to associate with the schedule
            schedule_data: Optional schedule data, uses fixture if not provided
            **kwargs: Additional fields to override
            
        Returns:
            Created schedule data with ID
        """
        if schedule_data is None:
            schedule_data = ScheduleFixtures.valid_schedule_create_data()
            
        # Override with any provided kwargs
        schedule_data.update(kwargs)
        
        # Ensure user_id is set
        schedule_data["user_id"] = user_id
        
        # Create schedule in database
        schedule_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        query = text("""
            INSERT INTO schedules (
                id, user_id, title, description, agent_name, cron_expression,
                enabled, timezone, agent_config_data, next_run, last_run,
                created_at, updated_at
            ) VALUES (
                :id, :user_id, :title, :description, :agent_name, :cron_expression,
                :enabled, :timezone, :agent_config_data, :next_run, :last_run,
                :created_at, :updated_at
            )
            RETURNING *
        """)
        
        params = {
            "id": schedule_id,
            "user_id": schedule_data["user_id"],
            "title": schedule_data["title"],
            "description": schedule_data.get("description"),
            "agent_name": schedule_data["agent_name"],
            "cron_expression": schedule_data["cron_expression"],
            "enabled": schedule_data.get("enabled", True),
            "timezone": schedule_data.get("timezone", "UTC"),
            "agent_config_data": schedule_data["agent_config_data"],
            "next_run": schedule_data.get("next_run", current_time + timedelta(hours=1)),
            "last_run": schedule_data.get("last_run"),
            "created_at": current_time,
            "updated_at": current_time
        }
        
        result = await self.session.execute(query, params)
        schedule = result.fetchone()
        
        # Track for cleanup
        self.created_schedules.append(schedule_id)
        
        # Convert to dict
        schedule_dict = dict(schedule._mapping)
        schedule_dict["id"] = schedule_id
        
        return schedule_dict
    
    async def create_multiple_schedules(
        self,
        user_id: str,
        count: int = 3,
        base_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create multiple test schedules.
        
        Args:
            user_id: User ID to associate with schedules
            count: Number of schedules to create
            base_data: Base schedule data to use
            
        Returns:
            List of created schedule data
        """
        schedules = []
        
        for i in range(count):
            # Start with fixture data to ensure all required fields
            data = ScheduleFixtures.valid_schedule_create_data()
            
            # Override with base_data if provided
            if base_data:
                data.update(base_data)
                
            # Override with iteration-specific data
            data.update({
                "title": f"Test Schedule {i + 1}",
                "description": f"Test schedule description {i + 1}",
                "cron_expression": data.get("cron_expression", f"0 {9 + i} * * *")  # Different hours
            })
            
            schedule = await self.create_test_schedule(user_id, data)
            schedules.append(schedule)
            
        return schedules
    
    async def create_test_job(
        self,
        user_id: str,
        schedule_id: Optional[str] = None,
        job_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a test job in the database.
        
        Args:
            user_id: User ID to associate with the job
            schedule_id: Schedule ID if this is a scheduled job
            job_data: Optional job data
            **kwargs: Additional fields to override
            
        Returns:
            Created job data with ID
        """
        if job_data is None:
            job_data = {
                "agent_name": "test_agent",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}},
                "status": "completed",
                "priority": 5
            }
        
        # Override with any provided kwargs
        job_data.update(kwargs)
        
        # Ensure required fields are set
        job_data["user_id"] = user_id
        if schedule_id:
            job_data["schedule_id"] = schedule_id
        
        # Create job in database
        job_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        query = text("""
            INSERT INTO jobs (
                id, user_id, schedule_id, agent_name, agent_config_data,
                status, priority, created_at, updated_at, started_at, completed_at
            ) VALUES (
                :id, :user_id, :schedule_id, :agent_name, :agent_config_data,
                :status, :priority, :created_at, :updated_at, :started_at, :completed_at
            )
            RETURNING *
        """)
        
        params = {
            "id": job_id,
            "user_id": job_data["user_id"],
            "schedule_id": job_data.get("schedule_id"),
            "agent_name": job_data["agent_name"],
            "agent_config_data": job_data["agent_config_data"],
            "status": job_data.get("status", "completed"),
            "priority": job_data.get("priority", 5),
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": job_data.get("started_at", current_time - timedelta(minutes=5)),
            "completed_at": job_data.get("completed_at", current_time)
        }
        
        result = await self.session.execute(query, params)
        job = result.fetchone()
        return dict(job._mapping) if job else None
    
    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule by ID."""
        query = text("SELECT * FROM schedules WHERE id = :id")
        result = await self.session.execute(query, {"id": schedule_id})
        schedule = result.fetchone()
        return dict(schedule._mapping) if schedule else None
    
    async def get_schedules_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all schedules for a user."""
        query = text("SELECT * FROM schedules WHERE user_id = :user_id ORDER BY created_at")
        result = await self.session.execute(query, {"user_id": user_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_jobs_by_schedule(self, schedule_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a schedule."""
        query = text("SELECT * FROM jobs WHERE schedule_id = :schedule_id ORDER BY created_at DESC")
        result = await self.session.execute(query, {"schedule_id": schedule_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        query = text("SELECT * FROM jobs WHERE id = :id")
        result = await self.session.execute(query, {"id": job_id})
        job = result.fetchone()
        return dict(job._mapping) if job else None
    
    async def update_schedule(
        self,
        schedule_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a schedule."""
        # Build dynamic update query
        set_clauses = []
        params = {"id": schedule_id, "updated_at": datetime.now(timezone.utc)}
        
        for key, value in update_data.items():
            if key != "id":
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        
        if not set_clauses:
            return await self.get_schedule_by_id(schedule_id)
        
        query = text(f"""
            UPDATE schedules 
            SET {', '.join(set_clauses)}, updated_at = :updated_at
            WHERE id = :id
            RETURNING *
        """)
        
        result = await self.session.execute(query, params)
        schedule = result.fetchone()
        return dict(schedule._mapping) if schedule else None
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule and return success status."""
        query = text("DELETE FROM schedules WHERE id = :id")
        result = await self.session.execute(query, {"id": schedule_id})
        return result.rowcount > 0
    
    async def count_schedules(self, user_id: Optional[str] = None) -> int:
        """Count schedules, optionally filtered by user."""
        if user_id:
            query = text("SELECT COUNT(*) FROM schedules WHERE user_id = :user_id")
            params = {"user_id": user_id}
        else:
            query = text("SELECT COUNT(*) FROM schedules")
            params = {}
            
        result = await self.session.execute(query, params)
        return result.scalar()
    
    async def count_jobs(self, schedule_id: Optional[str] = None) -> int:
        """Count jobs, optionally filtered by schedule."""
        if schedule_id:
            query = text("SELECT COUNT(*) FROM jobs WHERE schedule_id = :schedule_id")
            params = {"schedule_id": schedule_id}
        else:
            query = text("SELECT COUNT(*) FROM jobs")
            params = {}
            
        result = await self.session.execute(query, params)
        return result.scalar()
    
    async def get_due_schedules(self, tolerance_minutes: int = 5) -> List[Dict[str, Any]]:
        """Get schedules that are due for execution."""
        current_time = datetime.now(timezone.utc)
        tolerance_time = current_time + timedelta(minutes=tolerance_minutes)
        
        query = text("""
            SELECT * FROM schedules 
            WHERE enabled = true 
            AND next_run <= :tolerance_time
            ORDER BY next_run
        """)
        
        result = await self.session.execute(query, {"tolerance_time": tolerance_time})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def cleanup(self):
        """Clean up all test data created by this utility."""
        # Delete jobs first (foreign key constraint)
        if self.created_jobs:
            job_ids = "', '".join(self.created_jobs)
            query = text(f"DELETE FROM jobs WHERE id IN ('{job_ids}')")
            await self.session.execute(query)
        
        # Delete schedules
        if self.created_schedules:
            schedule_ids = "', '".join(self.created_schedules)
            query = text(f"DELETE FROM schedules WHERE id IN ('{schedule_ids}')")
            await self.session.execute(query)
        
        await self.session.commit()
        
        # Clear tracking lists
        self.created_schedules.clear()
        self.created_jobs.clear()


@asynccontextmanager
async def test_db_session():
    """
    Context manager for test database sessions with automatic cleanup.
    
    Usage:
        async with test_db_session() as session:
            db_utils = DatabaseTestUtils(session)
            # ... run tests
            # cleanup happens automatically
    """
    # This would need to be configured with your actual test database
    # For now, this is a placeholder structure
    session = None  # Replace with actual session creation
    
    try:
        yield session
    finally:
        if session:
            await session.rollback()
            await session.close()


class ScheduleTestHelpers:
    """Higher-level helper functions for schedule testing."""
    
    @staticmethod
    async def create_schedule_with_history(
        db_utils: DatabaseTestUtils,
        user_id: str,
        history_count: int = 3
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a schedule with execution history.
        
        Returns:
            Tuple of (schedule_data, history_jobs)
        """
        # Create schedule
        schedule = await db_utils.create_test_schedule(user_id)
        
        # Create history jobs
        jobs = []
        for i in range(history_count):
            execution_time = datetime.now(timezone.utc) - timedelta(hours=24 * (i + 1))
            job = await db_utils.create_test_job(
                user_id=user_id,
                schedule_id=schedule["id"],
                status="completed" if i % 2 == 0 else "failed",
                started_at=execution_time,
                completed_at=execution_time + timedelta(seconds=30),
                error_message="Test error" if i % 2 == 1 else None
            )
            jobs.append(job)
        
        return schedule, jobs
    
    @staticmethod
    async def create_overdue_schedule(
        db_utils: DatabaseTestUtils,
        user_id: str,
        hours_overdue: int = 2
    ) -> Dict[str, Any]:
        """Create a schedule that is overdue."""
        overdue_time = datetime.now(timezone.utc) - timedelta(hours=hours_overdue)
        
        return await db_utils.create_test_schedule(
            user_id=user_id,
            next_run=overdue_time,
            enabled=True
        )
    
    @staticmethod
    async def create_upcoming_schedule(
        db_utils: DatabaseTestUtils,
        user_id: str,
        hours_until: int = 2
    ) -> Dict[str, Any]:
        """Create a schedule that will run in the future."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=hours_until)
        
        return await db_utils.create_test_schedule(
            user_id=user_id,
            next_run=future_time,
            enabled=True
        )
    
    @staticmethod
    async def get_schedule_execution_history(
        db_utils: DatabaseTestUtils,
        schedule_id: str
    ) -> List[Dict[str, Any]]:
        """Get execution history for a schedule."""
        return await db_utils.get_jobs_by_schedule(schedule_id)
    
    @staticmethod
    async def enable_schedule(
        db_utils: DatabaseTestUtils,
        schedule_id: str
    ) -> Dict[str, Any]:
        """Enable a schedule and update next_run time."""
        current_time = datetime.now(timezone.utc)
        next_run = current_time + timedelta(hours=1)  # Simple next run calculation
        
        return await db_utils.update_schedule(
            schedule_id,
            {
                "enabled": True,
                "next_run": next_run
            }
        )
    
    @staticmethod
    async def disable_schedule(
        db_utils: DatabaseTestUtils,
        schedule_id: str
    ) -> Dict[str, Any]:
        """Disable a schedule and clear next_run time."""
        return await db_utils.update_schedule(
            schedule_id,
            {
                "enabled": False,
                "next_run": None
            }
        )


# Pytest fixtures for easy use in tests
@pytest.fixture
async def db_utils(db_session):
    """Pytest fixture providing DatabaseTestUtils with automatic cleanup."""
    utils = DatabaseTestUtils(db_session)
    yield utils
    await utils.cleanup()


@pytest.fixture
def test_user_id():
    """Pytest fixture providing a test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def schedule_helpers():
    """Pytest fixture providing ScheduleTestHelpers."""
    return ScheduleTestHelpers 