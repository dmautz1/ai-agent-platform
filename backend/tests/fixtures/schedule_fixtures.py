"""
Test fixtures for schedule-related testing.

Provides valid and invalid examples of schedule data for use across
all schedule test suites.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import uuid


class ScheduleFixtures:
    """Collection of schedule test fixtures."""
    
    @staticmethod
    def valid_schedule_create_data() -> Dict[str, Any]:
        """Valid schedule creation data."""
        return {
            "title": "Daily Data Processing",
            "description": "Process daily analytics data",
            "agent_name": "data_processor",
            "cron_expression": "0 9 * * *",  # Daily at 9 AM
            "enabled": True,
            "timezone": "UTC",
            "agent_config_data": {
                "name": "data_processor",
                "job_data": {
                    "input_file": "daily_data.csv",
                    "output_format": "json"
                },
                "execution": {
                    "priority": 5,
                    "timeout_minutes": 30
                },
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            }
        }
    
    @staticmethod
    def valid_schedule_create_minimal() -> Dict[str, Any]:
        """Minimal valid schedule creation data."""
        return {
            "title": "Simple Job",
            "agent_name": "simple_agent",
            "cron_expression": "0 0 * * *",  # Daily at midnight
            "agent_config_data": {
                "name": "simple_agent",
                "job_data": {
                    "prompt": "Hello world"
                }
            }
        }
    
    @staticmethod
    def valid_schedule_update_data() -> Dict[str, Any]:
        """Valid schedule update data."""
        return {
            "title": "Updated Daily Processing",
            "description": "Updated description",
            "cron_expression": "0 10 * * *",  # Daily at 10 AM
            "enabled": False
        }
    
    @staticmethod
    def valid_cron_expressions() -> list[str]:
        """List of valid cron expressions for testing."""
        return [
            "0 9 * * *",        # Daily at 9 AM
            "0 */6 * * *",      # Every 6 hours
            "0 0 * * 0",        # Weekly on Sunday
            "0 0 1 * *",        # Monthly on 1st
            "*/15 * * * *",     # Every 15 minutes
            "0 9-17 * * 1-5",   # Weekdays 9 AM to 5 PM
            "0 8,12,16 * * *",  # Three times a day
        ]
    
    @staticmethod
    def invalid_cron_expressions() -> list[str]:
        """List of invalid cron expressions for testing."""
        return [
            "",                 # Empty
            "invalid",          # Not cron format
            "0 25 * * *",       # Invalid hour (25)
            "0 * * * 8",        # Invalid day of week (8)
            "0 * 32 * *",       # Invalid day of month (32)
            "0 * * 13 *",       # Invalid month (13)
            "* * * * * *",      # Too many fields
            "0 *",              # Too few fields
        ]
    
    @staticmethod
    def invalid_schedule_data() -> Dict[str, Dict[str, Any]]:
        """Invalid schedule data examples for validation testing."""
        return {
            "empty_title": {
                "title": "",
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}}
            },
            "missing_agent_name": {
                "title": "Test Job",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}}
            },
            "invalid_cron": {
                "title": "Test Job",
                "agent_name": "test_agent",
                "cron_expression": "invalid_cron",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}}
            },
            "missing_agent_config": {
                "title": "Test Job",
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *"
            },
            "empty_agent_config": {
                "title": "Test Job",
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {}
            },
            "title_too_long": {
                "title": "x" * 201,  # Exceeds 200 char limit
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}}
            },
            "description_too_long": {
                "title": "Test Job",
                "description": "x" * 1001,  # Exceeds 1000 char limit
                "agent_name": "test_agent",
                "cron_expression": "0 9 * * *",
                "agent_config_data": {"name": "test_agent", "job_data": {"prompt": "test"}}
            }
        }
    
    @staticmethod
    def complete_schedule_record() -> Dict[str, Any]:
        """Complete schedule database record for testing."""
        schedule_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        return {
            "id": schedule_id,
            "user_id": user_id,
            "title": "Test Schedule",
            "description": "Test schedule description",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "timezone": "UTC",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {
                    "prompt": "Test prompt",
                    "max_tokens": 1000
                },
                "execution": {
                    "priority": 5
                }
            },
            "next_run": (current_time + timedelta(hours=1)).isoformat(),
            "last_run": current_time.isoformat(),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
    
    @staticmethod
    def schedule_execution_history() -> list[Dict[str, Any]]:
        """Schedule execution history records for testing."""
        schedule_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        return [
            {
                "schedule_id": schedule_id,
                "job_id": str(uuid.uuid4()),
                "execution_time": (current_time - timedelta(hours=24)).isoformat(),
                "status": "completed",
                "duration_seconds": 45.5,
                "error_message": None,
                "result_preview": "Processing completed successfully with 100 records"
            },
            {
                "schedule_id": schedule_id,
                "job_id": str(uuid.uuid4()),
                "execution_time": (current_time - timedelta(hours=48)).isoformat(),
                "status": "failed",
                "duration_seconds": 15.2,
                "error_message": "Connection timeout",
                "result_preview": None
            },
            {
                "schedule_id": schedule_id,
                "job_id": str(uuid.uuid4()),
                "execution_time": (current_time - timedelta(hours=72)).isoformat(),
                "status": "completed",
                "duration_seconds": 32.1,
                "error_message": None,
                "result_preview": "Data processed: 75 records analyzed"
            }
        ]
    
    @staticmethod
    def upcoming_jobs_data() -> list[Dict[str, Any]]:
        """Upcoming jobs data for testing."""
        current_time = datetime.now(timezone.utc)
        
        return [
            {
                "id": str(uuid.uuid4()),
                "schedule_id": str(uuid.uuid4()),
                "title": "Daily Report Generation",
                "description": "Generate daily analytics report",
                "agent_name": "report_generator",
                "cron_expression": "0 9 * * *",
                "enabled": True,
                "next_run": (current_time + timedelta(hours=2)).isoformat(),
                "time_until_run": 7200.0,  # 2 hours in seconds
                "cron_description": "Daily at 9:00 AM",
                "is_overdue": False
            },
            {
                "id": str(uuid.uuid4()),
                "schedule_id": str(uuid.uuid4()),
                "title": "Weekly Backup",
                "description": "Weekly data backup process",
                "agent_name": "backup_agent",
                "cron_expression": "0 0 * * 0",
                "enabled": True,
                "next_run": (current_time + timedelta(days=1)).isoformat(),
                "time_until_run": 86400.0,  # 1 day in seconds
                "cron_description": "Weekly on Sunday at midnight",
                "is_overdue": False
            },
            {
                "id": str(uuid.uuid4()),
                "schedule_id": str(uuid.uuid4()),
                "title": "Overdue Job",
                "description": "This job should have run already",
                "agent_name": "late_agent",
                "cron_expression": "0 8 * * *",
                "enabled": True,
                "next_run": (current_time - timedelta(hours=1)).isoformat(),
                "time_until_run": -3600.0,  # 1 hour ago
                "cron_description": "Daily at 8:00 AM",
                "is_overdue": True
            }
        ]
    
    @staticmethod
    def timezone_test_data() -> Dict[str, Dict[str, Any]]:
        """Timezone-specific test data."""
        return {
            "utc": {
                "timezone": "UTC",
                "cron_expression": "0 9 * * *",
                "expected_hour": 9
            },
            "eastern": {
                "timezone": "America/New_York",
                "cron_expression": "0 9 * * *",
                "expected_hour": 9  # Local time
            },
            "pacific": {
                "timezone": "America/Los_Angeles",
                "cron_expression": "0 6 * * *",
                "expected_hour": 6  # Local time
            },
            "london": {
                "timezone": "Europe/London",
                "cron_expression": "0 14 * * *",
                "expected_hour": 14  # Local time
            }
        }


# Convenience functions for direct fixture access
def get_valid_schedule_data() -> Dict[str, Any]:
    """Get valid schedule creation data."""
    return ScheduleFixtures.valid_schedule_create_data()


def get_invalid_schedule_data() -> Dict[str, Dict[str, Any]]:
    """Get invalid schedule data examples."""
    return ScheduleFixtures.invalid_schedule_data()


def get_valid_cron_expressions() -> list[str]:
    """Get list of valid cron expressions."""
    return ScheduleFixtures.valid_cron_expressions()


def get_invalid_cron_expressions() -> list[str]:
    """Get list of invalid cron expressions."""
    return ScheduleFixtures.invalid_cron_expressions() 