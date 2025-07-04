"""
Time-based test utilities for schedule testing.

Provides utilities for mocking time, testing cron expressions,
and handling timezone-related testing scenarios.
"""

import pytz
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from freezegun import freeze_time
from croniter import croniter

import pytest


class MockTimeProvider:
    """Mock time provider for controlled time testing."""
    
    def __init__(self, base_time: Optional[datetime] = None):
        self.base_time = base_time or datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        self.current_time = self.base_time
        self.time_callbacks = []
        
    def now(self, tz: Optional[timezone] = None) -> datetime:
        """Get current mock time."""
        if tz and tz != timezone.utc:
            return self.current_time.astimezone(tz)
        return self.current_time
    
    def utcnow(self) -> datetime:
        """Get current mock time in UTC."""
        return self.current_time
    
    def advance_time(self, **kwargs):
        """Advance mock time by specified amount."""
        delta = timedelta(**kwargs)
        self.current_time += delta
        
        # Call registered callbacks
        for callback in self.time_callbacks:
            callback(self.current_time)
    
    def set_time(self, new_time: datetime):
        """Set mock time to specific value."""
        self.current_time = new_time
        
        # Call registered callbacks
        for callback in self.time_callbacks:
            callback(self.current_time)
    
    def register_time_callback(self, callback: Callable[[datetime], None]):
        """Register callback to be called when time changes."""
        self.time_callbacks.append(callback)
    
    def reset(self):
        """Reset to base time."""
        self.current_time = self.base_time
        self.time_callbacks.clear()


class CronTestHelper:
    """Helper for testing cron expressions and schedules."""
    
    def __init__(self, time_provider: Optional[MockTimeProvider] = None):
        self.time_provider = time_provider or MockTimeProvider()
    
    def get_next_run_time(
        self,
        cron_expression: str,
        base_time: Optional[datetime] = None,
        timezone_name: str = "UTC"
    ) -> datetime:
        """Calculate next run time for cron expression."""
        if base_time is None:
            base_time = self.time_provider.now()
        
        # Convert to target timezone if needed
        tz = pytz.timezone(timezone_name)
        if base_time.tzinfo != tz:
            base_time = base_time.astimezone(tz)
        
        cron = croniter(cron_expression, base_time)
        next_time = cron.get_next(datetime)
        
        # Convert back to UTC for storage
        return next_time.astimezone(timezone.utc)
    
    def get_previous_run_time(
        self,
        cron_expression: str,
        base_time: Optional[datetime] = None,
        timezone_name: str = "UTC"
    ) -> datetime:
        """Calculate previous run time for cron expression."""
        if base_time is None:
            base_time = self.time_provider.now()
        
        tz = pytz.timezone(timezone_name)
        if base_time.tzinfo != tz:
            base_time = base_time.astimezone(tz)
        
        cron = croniter(cron_expression, base_time)
        prev_time = cron.get_prev(datetime)
        
        return prev_time.astimezone(timezone.utc)
    
    def get_next_n_runs(
        self,
        cron_expression: str,
        n: int,
        base_time: Optional[datetime] = None,
        timezone_name: str = "UTC"
    ) -> List[datetime]:
        """Get next N run times for cron expression."""
        if base_time is None:
            base_time = self.time_provider.now()
        
        tz = pytz.timezone(timezone_name)
        if base_time.tzinfo != tz:
            base_time = base_time.astimezone(tz)
        
        cron = croniter(cron_expression, base_time)
        run_times = []
        
        for _ in range(n):
            next_time = cron.get_next(datetime)
            run_times.append(next_time.astimezone(timezone.utc))
        
        return run_times
    
    def is_time_due(
        self,
        cron_expression: str,
        check_time: Optional[datetime] = None,
        tolerance_minutes: int = 5,
        timezone_name: str = "UTC"
    ) -> bool:
        """Check if a cron expression is due at given time."""
        if check_time is None:
            check_time = self.time_provider.now()
        
        # Get the most recent scheduled time
        prev_run = self.get_previous_run_time(cron_expression, check_time, timezone_name)
        next_run = self.get_next_run_time(cron_expression, prev_run, timezone_name)
        
        # Check if we're within tolerance of the scheduled time
        tolerance = timedelta(minutes=tolerance_minutes)
        return abs(check_time - next_run) <= tolerance
    
    def simulate_schedule_execution(
        self,
        cron_expression: str,
        duration_hours: int = 24,
        timezone_name: str = "UTC"
    ) -> List[datetime]:
        """Simulate schedule execution over a time period."""
        start_time = self.time_provider.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        execution_times = []
        current_time = start_time
        
        while current_time < end_time:
            next_run = self.get_next_run_time(cron_expression, current_time, timezone_name)
            if next_run > end_time:
                break
            
            execution_times.append(next_run)
            current_time = next_run + timedelta(seconds=1)  # Move past execution time
        
        return execution_times
    
    def validate_cron_expression(self, cron_expression: str) -> bool:
        """Validate if cron expression is valid."""
        try:
            croniter(cron_expression)
            return True
        except (ValueError, TypeError):
            return False
    
    def describe_cron_expression(self, cron_expression: str) -> str:
        """Get human-readable description of cron expression."""
        # This is a simplified version - you might want to use a library like cron-descriptor
        try:
            cron = croniter(cron_expression)
            # Basic descriptions for common patterns
            parts = cron_expression.split()
            
            if len(parts) != 5:
                return "Invalid cron expression"
            
            minute, hour, day, month, weekday = parts
            
            # Simple patterns
            if cron_expression == "0 0 * * *":
                return "Daily at midnight"
            elif cron_expression == "0 9 * * *":
                return "Daily at 9:00 AM"
            elif cron_expression == "0 0 * * 0":
                return "Weekly on Sunday at midnight"
            elif cron_expression == "0 0 1 * *":
                return "Monthly on the 1st at midnight"
            elif cron_expression.startswith("*/"):
                interval = cron_expression.split()[0][2:]
                return f"Every {interval} minutes"
            else:
                return f"Custom schedule: {cron_expression}"
                
        except Exception:
            return "Invalid cron expression"


class TimezoneTestHelper:
    """Helper for timezone-related testing."""
    
    @staticmethod
    def get_common_timezones() -> Dict[str, str]:
        """Get dictionary of common timezone names."""
        return {
            "UTC": "UTC",
            "Eastern": "America/New_York",
            "Pacific": "America/Los_Angeles",
            "Central": "America/Chicago",
            "Mountain": "America/Denver",
            "London": "Europe/London",
            "Paris": "Europe/Paris",
            "Tokyo": "Asia/Tokyo",
            "Sydney": "Australia/Sydney"
        }
    
    @staticmethod
    def convert_time_to_timezone(
        dt: datetime,
        target_timezone: str
    ) -> datetime:
        """Convert datetime to target timezone."""
        tz = pytz.timezone(target_timezone)
        
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.astimezone(tz)
    
    @staticmethod
    def create_time_in_timezone(
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        second: int = 0,
        timezone_name: str = "UTC"
    ) -> datetime:
        """Create datetime in specific timezone."""
        tz = pytz.timezone(timezone_name)
        dt = tz.localize(datetime(year, month, day, hour, minute, second))
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def test_dst_transition(
        cron_expression: str,
        year: int,
        timezone_name: str = "America/New_York"
    ) -> Dict[str, List[datetime]]:
        """Test cron expression behavior during DST transitions."""
        tz = pytz.timezone(timezone_name)
        
        # Find DST transitions for the year
        dst_start = None
        dst_end = None
        
        # Check each day in March and November (typical DST months)
        for month in [3, 11]:
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day, 12, 0, 0)
                    dt_tz = tz.localize(dt)
                    
                    if month == 3 and dst_start is None and dt_tz.dst():
                        dst_start = dt_tz
                    elif month == 11 and dst_end is None and not dt_tz.dst():
                        dst_end = dt_tz
                        
                except Exception:
                    continue
        
        results = {}
        cron_helper = CronTestHelper()
        
        if dst_start:
            # Test week around DST start
            test_start = dst_start - timedelta(days=3)
            runs = []
            for i in range(7):
                test_time = test_start + timedelta(days=i)
                try:
                    next_run = cron_helper.get_next_run_time(
                        cron_expression, test_time, timezone_name
                    )
                    runs.append(next_run)
                except Exception:
                    pass
            results["dst_start"] = runs
        
        if dst_end:
            # Test week around DST end
            test_start = dst_end - timedelta(days=3)
            runs = []
            for i in range(7):
                test_time = test_start + timedelta(days=i)
                try:
                    next_run = cron_helper.get_next_run_time(
                        cron_expression, test_time, timezone_name
                    )
                    runs.append(next_run)
                except Exception:
                    pass
            results["dst_end"] = runs
        
        return results


class TimeTestManager:
    """Manager for coordinating time-based testing utilities."""
    
    def __init__(self, base_time: Optional[datetime] = None):
        self.time_provider = MockTimeProvider(base_time)
        self.cron_helper = CronTestHelper(self.time_provider)
        self.timezone_helper = TimezoneTestHelper()
        self._active_patches = []
    
    def setup_time_mocks(self) -> Dict[str, Mock]:
        """Set up time-related mocks."""
        mocks = {}
        
        # Mock datetime.now
        datetime_mock = Mock()
        datetime_mock.now = Mock(side_effect=self.time_provider.now)
        datetime_mock.utcnow = Mock(side_effect=self.time_provider.utcnow)
        mocks["datetime"] = datetime_mock
        
        return mocks
    
    @contextmanager
    def freeze_time_at(self, frozen_time: datetime):
        """Context manager to freeze time at specific datetime."""
        with freeze_time(frozen_time) as frozen:
            self.time_provider.set_time(frozen_time)
            yield frozen
    
    @contextmanager
    def freeze_time_context(self, frozen_time: datetime):
        """Context manager to freeze time at specific datetime (alias for freeze_time_at)."""
        with self.freeze_time_at(frozen_time) as frozen:
            yield frozen
    
    @contextmanager
    def time_travel(self, start_time: datetime):
        """Context manager for time travel testing."""
        original_time = self.time_provider.current_time
        self.time_provider.set_time(start_time)
        
        try:
            yield self.time_provider
        finally:
            self.time_provider.set_time(original_time)
    
    def create_schedule_test_scenario(
        self,
        cron_expression: str,
        scenario_hours: int = 48,
        timezone_name: str = "UTC"
    ) -> Dict[str, Any]:
        """Create a comprehensive test scenario for a schedule."""
        scenario = {
            "cron_expression": cron_expression,
            "timezone": timezone_name,
            "is_valid": self.cron_helper.validate_cron_expression(cron_expression),
            "description": self.cron_helper.describe_cron_expression(cron_expression)
        }
        
        if scenario["is_valid"]:
            current_time = self.time_provider.now()
            
            scenario.update({
                "next_run": self.cron_helper.get_next_run_time(
                    cron_expression, current_time, timezone_name
                ),
                "previous_run": self.cron_helper.get_previous_run_time(
                    cron_expression, current_time, timezone_name
                ),
                "next_5_runs": self.cron_helper.get_next_n_runs(
                    cron_expression, 5, current_time, timezone_name
                ),
                "simulated_runs": self.cron_helper.simulate_schedule_execution(
                    cron_expression, scenario_hours, timezone_name
                )
            })
        
        return scenario
    
    def test_cron_edge_cases(self, cron_expression: str) -> Dict[str, Any]:
        """Test cron expression edge cases."""
        results = {
            "leap_year": {},
            "month_boundaries": {},
            "dst_transitions": {}
        }
        
        # Test leap year (February 29)
        leap_year = 2024
        try:
            leap_time = datetime(leap_year, 2, 29, 12, 0, 0, tzinfo=timezone.utc)
            with self.time_travel(leap_time):
                results["leap_year"] = {
                    "next_run": self.cron_helper.get_next_run_time(cron_expression),
                    "is_due": self.cron_helper.is_time_due(cron_expression)
                }
        except Exception as e:
            results["leap_year"]["error"] = str(e)
        
        # Test month boundaries
        for month in [1, 2, 12]:  # January, February, December
            try:
                # Last day of month
                if month == 2:
                    last_day = 28
                elif month in [1, 12]:
                    last_day = 31
                else:
                    last_day = 30
                
                boundary_time = datetime(2024, month, last_day, 23, 59, 0, tzinfo=timezone.utc)
                with self.time_travel(boundary_time):
                    results["month_boundaries"][f"month_{month}"] = {
                        "next_run": self.cron_helper.get_next_run_time(cron_expression),
                        "next_3_runs": self.cron_helper.get_next_n_runs(cron_expression, 3)
                    }
            except Exception as e:
                results["month_boundaries"][f"month_{month}"] = {"error": str(e)}
        
        # Test DST transitions for US Eastern timezone
        try:
            dst_results = self.timezone_helper.test_dst_transition(
                cron_expression, 2024, "America/New_York"
            )
            results["dst_transitions"] = dst_results
        except Exception as e:
            results["dst_transitions"]["error"] = str(e)
        
        return results
    
    def reset_time(self):
        """Reset time provider to base time."""
        self.time_provider.reset()


# Test scenario builders
class TimeTestScenarios:
    """Pre-built time-based test scenarios."""
    
    @staticmethod
    def daily_schedule_scenario() -> TimeTestManager:
        """Scenario: Daily schedule testing."""
        # Start on a Monday at 8 AM
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)  # Monday
        return TimeTestManager(base_time)
    
    @staticmethod
    def weekly_schedule_scenario() -> TimeTestManager:
        """Scenario: Weekly schedule testing."""
        # Start on a Sunday at midnight
        base_time = datetime(2024, 1, 14, 0, 0, 0, tzinfo=timezone.utc)  # Sunday
        return TimeTestManager(base_time)
    
    @staticmethod
    def monthly_schedule_scenario() -> TimeTestManager:
        """Scenario: Monthly schedule testing."""
        # Start on the 1st of the month
        base_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        return TimeTestManager(base_time)
    
    @staticmethod
    def dst_transition_scenario() -> TimeTestManager:
        """Scenario: DST transition testing."""
        # Start just before DST transition (second Sunday in March)
        base_time = datetime(2024, 3, 9, 23, 0, 0, tzinfo=timezone.utc)
        return TimeTestManager(base_time)
    
    @staticmethod
    def year_boundary_scenario() -> TimeTestManager:
        """Scenario: Year boundary testing."""
        # Start on New Year's Eve
        base_time = datetime(2023, 12, 31, 23, 0, 0, tzinfo=timezone.utc)
        return TimeTestManager(base_time)


# Pytest fixtures
@pytest.fixture
def mock_time_provider():
    """Pytest fixture providing MockTimeProvider."""
    provider = MockTimeProvider()
    yield provider
    provider.reset()


@pytest.fixture
def cron_helper(mock_time_provider):
    """Pytest fixture providing CronTestHelper."""
    return CronTestHelper(mock_time_provider)


@pytest.fixture
def timezone_helper():
    """Pytest fixture providing TimezoneTestHelper."""
    return TimezoneTestHelper()


@pytest.fixture
def time_manager():
    """Pytest fixture providing TimeTestManager."""
    manager = TimeTestManager()
    yield manager
    manager.reset_time()


@pytest.fixture
def frozen_monday_9am():
    """Pytest fixture with time frozen at Monday 9 AM."""
    frozen_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    with freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture
def frozen_sunday_midnight():
    """Pytest fixture with time frozen at Sunday midnight."""
    frozen_time = datetime(2024, 1, 14, 0, 0, 0, tzinfo=timezone.utc)
    with freeze_time(frozen_time):
        yield frozen_time


# Helper functions
def create_test_datetime(
    year: int = 2024,
    month: int = 1,
    day: int = 15,
    hour: int = 10,
    minute: int = 0,
    second: int = 0,
    timezone_name: str = "UTC"
) -> datetime:
    """Create test datetime with timezone."""
    if timezone_name == "UTC":
        return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    else:
        tz = pytz.timezone(timezone_name)
        dt = tz.localize(datetime(year, month, day, hour, minute, second))
        return dt.astimezone(timezone.utc)


def get_cron_test_cases() -> List[Dict[str, Any]]:
    """Get comprehensive list of cron test cases."""
    return [
        {
            "expression": "0 9 * * *",
            "description": "Daily at 9 AM",
            "expected_interval_hours": 24,
            "test_timezone": "UTC"
        },
        {
            "expression": "0 */6 * * *",
            "description": "Every 6 hours",
            "expected_interval_hours": 6,
            "test_timezone": "UTC"
        },
        {
            "expression": "0 0 * * 0",
            "description": "Weekly on Sunday",
            "expected_interval_hours": 168,  # 7 days
            "test_timezone": "America/New_York"
        },
        {
            "expression": "0 0 1 * *",
            "description": "Monthly on 1st",
            "expected_interval_hours": None,  # Variable
            "test_timezone": "Europe/London"
        },
        {
            "expression": "*/15 * * * *",
            "description": "Every 15 minutes",
            "expected_interval_hours": 0.25,
            "test_timezone": "Asia/Tokyo"
        },
        {
            "expression": "0 9-17 * * 1-5",
            "description": "Weekdays 9 AM to 5 PM",
            "expected_interval_hours": 1,
            "test_timezone": "America/Los_Angeles"
        }
    ]


def assert_cron_schedule_accuracy(
    cron_expression: str,
    expected_count: int,
    test_hours: int = 24,
    tolerance: int = 1
):
    """Assert that cron schedule runs expected number of times."""
    time_manager = TimeTestManager()
    runs = time_manager.cron_helper.simulate_schedule_execution(
        cron_expression, test_hours
    )
    
    assert abs(len(runs) - expected_count) <= tolerance, (
        f"Expected {expected_count} runs (±{tolerance}), got {len(runs)} "
        f"for cron '{cron_expression}' over {test_hours} hours"
    ) 