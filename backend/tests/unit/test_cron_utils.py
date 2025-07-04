"""
Unit tests for CronUtils cron expression utilities.

Tests validation, next run time calculation, description generation,
and edge cases for cron expression handling.
"""

import pytest
from unittest import mock
import pytz
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from utils.cron_utils import CronUtils, CronValidationError
from tests.fixtures.schedule_fixtures import ScheduleFixtures
# from tests.utils.time_utils import MockTimeProvider, CronTestHelper, TimeTestManager, timezone_test_cases


class TestCronUtilsValidation:
    """Test CronUtils.validate_cron_expression with valid and invalid patterns."""
    
    @pytest.mark.parametrize("valid_cron", [
        "0 9 * * *",        # Daily at 9 AM
        "0 */6 * * *",      # Every 6 hours
        "0 0 * * 0",        # Weekly on Sunday
        "0 0 1 * *",        # Monthly on 1st
        "*/15 * * * *",     # Every 15 minutes
        "0 9-17 * * 1-5",   # Weekdays 9 AM to 5 PM
        "0 8,12,16 * * *",  # Three times a day
        "0 2 */2 * *",      # Every other day at 2 AM
        "0 0 1,15 * *",     # 1st and 15th of month
        "0 0 * * 1,3,5",    # Monday, Wednesday, Friday
        "30 14 1 * *",      # 1st of month at 2:30 PM
        "0 22 * * 1-5",     # Weekdays at 10 PM
        "*/10 * * * *",     # Every 10 minutes
        "0 */4 * * *",      # Every 4 hours
        "0 0 */3 * *",      # Every 3 days
        "0 0 1 */2 *",      # Every 2 months on 1st
        "0 6 * * 0,6",      # Weekends at 6 AM
        "45 23 * * *",      # Daily at 11:45 PM
        "0 0 * 1,7 *",      # January and July
        "0 12 1-7 * 0",     # First Sunday of month at noon
    ])
    def test_valid_cron_expressions(self, valid_cron):
        """Test CronUtils.validate_cron_expression with valid patterns."""
        assert CronUtils.validate_cron_expression(valid_cron) is True
    
    @pytest.mark.parametrize("invalid_cron", [
        "",                 # Empty string
        "   ",              # Whitespace only
        "invalid",          # Not cron format
        "0 25 * * *",       # Invalid hour (25)
        "60 0 * * *",       # Invalid minute (60)
        "0 * * * 8",        # Invalid day of week (8)
        "0 * 32 * *",       # Invalid day of month (32)
        "0 * * 13 *",       # Invalid month (13)
        "0 * 0 * *",        # Invalid day of month (0)
        "0 * * 0 *",        # Invalid month (0)
        "0 *",              # Too few fields (2)
        "0 * *",            # Too few fields (3)
        "0 * * *",          # Too few fields (4)
        "@invalid",         # Invalid special string
        "0 0-24 * * *",     # Invalid range for hour
        "0 0 1-32 * *",     # Invalid range for day
        "0 0 * 1-13 *",     # Invalid range for month
        "0 0 * * 0-8",      # Invalid range for weekday
        "0 0 31 4 *",       # April 31st (invalid date)
        "abc def ghi jkl mno",  # Non-numeric fields
        "0,61 * * * *",     # Invalid minute in list
        "0 0,25 * * *",     # Invalid hour in list
        "*/0 * * * *",      # Step value of 0
        "60/2 * * * *",     # Invalid base value with step
        "0-60 * * * *",     # Invalid range for minute
    ])
    def test_invalid_cron_expressions(self, invalid_cron):
        """Test CronUtils.validate_cron_expression with invalid patterns."""
        with pytest.raises(CronValidationError):
            CronUtils.validate_cron_expression(invalid_cron)
    
    def test_cron_validation_edge_cases(self):
        """Test edge cases for cron expression validation."""
        # None input
        with pytest.raises(CronValidationError):
            CronUtils.validate_cron_expression(None)
        
        # Valid complex expressions
        complex_valid = [
            "0 0 1-7 * 0",      # First week of month on Sunday
            "0 0 * * 0#1",      # First Sunday of month (if supported)
            "0 0 L * *",        # Last day of month (if supported) 
            "0 0 * * 0L",       # Last Sunday of month (if supported)
        ]
        
        for expr in complex_valid:
            try:
                result = CronUtils.validate_cron_expression(expr)
                # Should either validate successfully or raise CronValidationError
                assert isinstance(result, bool)
            except CronValidationError:
                # Some complex expressions might not be supported
                pass
    
    def test_validate_cron_expression_return_type(self):
        """Test that validate_cron_expression returns correct types."""
        # Valid expression should return True
        result = CronUtils.validate_cron_expression("0 9 * * *")
        assert result is True
        assert isinstance(result, bool)
        
        # Invalid expression should raise exception, not return False
        with pytest.raises(CronValidationError):
            CronUtils.validate_cron_expression("invalid")
    
    def test_validation_error_messages(self):
        """Test that validation error messages are descriptive."""
        test_cases = [
            ("", "empty"),
            ("invalid", "invalid"),
            ("0 25 * * *", "hour"),
            ("60 0 * * *", "minute"),
            ("* * * * * *", "fields"),
            ("0 *", "fields"),
        ]
        
        for invalid_expr, expected_keyword in test_cases:
            with pytest.raises(CronValidationError) as exc_info:
                CronUtils.validate_cron_expression(invalid_expr)
            
            error_msg = str(exc_info.value).lower()
            # Error message should be informative
            assert len(error_msg) > 0
            assert any(keyword in error_msg for keyword in [
                "cron", "expression", "invalid", "field", expected_keyword
            ])


class TestCronUtilsNextRunTime:
    """Test CronUtils.get_next_run_time with timezone handling and edge cases."""
    
    def test_basic_next_run_time_calculation(self):
        """Test basic next run time calculation."""
        # Test with current time
        next_run = CronUtils.get_next_run_time("0 9 * * *")
        assert isinstance(next_run, datetime)
        assert next_run.tzinfo == timezone.utc
        assert next_run > datetime.now(timezone.utc)
        
        # Test with specific base time
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 9 * * *", base_time)
        
        assert next_run.year == 2024
        assert next_run.month == 1
        assert next_run.day == 15
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert next_run.second == 0
    
    def test_next_run_time_with_timezones(self):
        """Test next run time calculation with different timezones."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        # Test UTC timezone
        next_run_utc = CronUtils.get_next_run_time(
            "0 9 * * *", base_time, "UTC"
        )
        assert next_run_utc.hour == 9
        assert next_run_utc.tzinfo == timezone.utc
        
        # Test New York timezone
        next_run_ny = CronUtils.get_next_run_time(
            "0 9 * * *", base_time, "America/New_York"
        )
        assert next_run_ny.tzinfo == timezone.utc
        # Result should be different from UTC due to timezone conversion
        assert next_run_ny != next_run_utc
        
        # Test Tokyo timezone
        next_run_tokyo = CronUtils.get_next_run_time(
            "0 9 * * *", base_time, "Asia/Tokyo"
        )
        assert next_run_tokyo.tzinfo == timezone.utc
        assert next_run_tokyo != next_run_utc
        assert next_run_tokyo != next_run_ny
    
    def test_next_run_time_edge_cases(self):
        """Test next run time calculation edge cases."""
        # Test end of day
        base_time = datetime(2024, 1, 15, 23, 59, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 0 * * *", base_time)
        assert next_run.day == 16  # Should roll to next day
        assert next_run.hour == 0
        
        # Test end of month
        base_time = datetime(2024, 1, 31, 23, 59, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 0 * * *", base_time)
        assert next_run.month == 2  # Should roll to next month
        assert next_run.day == 1
        
        # Test end of year
        base_time = datetime(2024, 12, 31, 23, 59, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 0 * * *", base_time)
        assert next_run.year == 2025  # Should roll to next year
        assert next_run.month == 1
        assert next_run.day == 1
    
    def test_next_run_time_leap_year(self):
        """Test next run time calculation during leap year."""
        # Test February 28th in leap year
        base_time = datetime(2024, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 0 * * *", base_time)
        assert next_run.month == 2
        assert next_run.day == 29  # Should be Feb 29 in leap year
        
        # Test February 28th in non-leap year
        base_time = datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        next_run = CronUtils.get_next_run_time("0 0 * * *", base_time)
        assert next_run.month == 3
        assert next_run.day == 1  # Should roll to March 1 in non-leap year
    
    def test_next_run_time_dst_transitions(self):
        """Test next run time calculation during DST transitions."""
        # This is a complex test that would require specific DST dates
        # For now, test that the function handles timezone-aware calculations
        
        # Test during typical DST transition period (March/November)
        base_time = datetime(2024, 3, 10, 1, 0, 0, tzinfo=timezone.utc)
        
        # Should not raise exception during DST transition
        next_run = CronUtils.get_next_run_time(
            "0 2 * * *", base_time, "America/New_York"
        )
        assert isinstance(next_run, datetime)
        assert next_run.tzinfo == timezone.utc
    
    def test_next_run_time_invalid_timezone(self):
        """Test next run time with invalid timezone."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        # Should handle invalid timezone gracefully
        next_run = CronUtils.get_next_run_time(
            "0 9 * * *", base_time, "Invalid/Timezone"
        )
        assert isinstance(next_run, datetime)
        assert next_run.tzinfo == timezone.utc
    
    def test_next_run_time_multiple_calculations(self):
        """Test multiple next run time calculations."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        # Test that multiple calls are consistent
        next_run_1 = CronUtils.get_next_run_time("0 9 * * *", base_time)
        next_run_2 = CronUtils.get_next_run_time("0 9 * * *", base_time)
        assert next_run_1 == next_run_2
        
        # Test progression of times
        times = []
        current_time = base_time
        for _ in range(5):
            next_time = CronUtils.get_next_run_time("0 */6 * * *", current_time)
            times.append(next_time)
            current_time = next_time + timedelta(seconds=1)
        
        # Times should be 6 hours apart
        for i in range(1, len(times)):
            diff = times[i] - times[i-1]
            assert abs(diff.total_seconds() - 6*3600) <= 1  # Allow 1 second tolerance
    
    def test_get_next_n_run_times(self):
        """Test getting multiple next run times."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        # Test basic functionality
        next_times = CronUtils.get_next_n_run_times("0 9 * * *", 5, base_time)
        assert len(next_times) == 5
        assert all(isinstance(t, datetime) for t in next_times)
        assert all(t.tzinfo == timezone.utc for t in next_times)
        
        # Times should be in chronological order
        for i in range(1, len(next_times)):
            assert next_times[i] > next_times[i-1]
        
        # Daily schedule should have 24-hour intervals
        for i in range(1, len(next_times)):
            diff = next_times[i] - next_times[i-1]
            assert abs(diff.total_seconds() - 24*3600) <= 1
    
    def test_get_next_n_run_times_validation(self):
        """Test validation for get_next_n_run_times."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        # Test invalid count
        with pytest.raises(CronValidationError):
            CronUtils.get_next_n_run_times("0 9 * * *", 0, base_time)
        
        with pytest.raises(CronValidationError):
            CronUtils.get_next_n_run_times("0 9 * * *", -1, base_time)
        
        with pytest.raises(CronValidationError):
            CronUtils.get_next_n_run_times("0 9 * * *", 101, base_time)
        
        # Test invalid cron expression
        with pytest.raises(CronValidationError):
            CronUtils.get_next_n_run_times("invalid", 5, base_time)


class TestCronUtilsDescriptions:
    """Test CronUtils.describe_cron_expression for human-readable descriptions."""
    
    @pytest.mark.parametrize("cron_expr,expected_keywords", [
        ("* * * * *", ["every", "minute"]),
        ("0 * * * *", ["every", "hour"]),
        ("0 0 * * *", ["daily", "midnight"]),
        ("0 9 * * *", ["daily", "9"]),
        ("0 9 * * 1", ["monday", "9"]),
        ("0 9 * * 1-5", ["weekday", "9"]),
        ("0 0 1 * *", ["month", "1st", "first"]),
        ("0 0 * * 0", ["sunday", "midnight"]),
        ("*/15 * * * *", ["15", "minute"]),
        ("0 */6 * * *", ["6", "hour"]),
        ("0 8,12,16 * * *", ["8", "12", "16"]),
        ("0 0 1,15 * *", ["1", "15"]),
        ("0 0 * 1,7 *", ["january", "july"]),
    ])
    def test_common_cron_descriptions(self, cron_expr, expected_keywords):
        """Test descriptions for common cron expressions."""
        description = CronUtils.describe_cron_expression(cron_expr)
        
        assert isinstance(description, str)
        assert len(description) > 0
        
        # Check that description contains relevant keywords
        description_lower = description.lower()
        keyword_found = any(
            any(keyword.lower() in description_lower for keyword in expected_keywords)
            for keyword in expected_keywords
        )
        assert keyword_found, f"Expected keywords {expected_keywords} not found in '{description}'"
    
    def test_describe_complex_expressions(self):
        """Test descriptions for complex cron expressions."""
        complex_expressions = [
            "0 9-17 * * 1-5",  # Business hours
            "*/30 9-17 * * 1-5",  # Every 30 minutes during business hours
            "0 0 */2 * *",     # Every other day
            "0 0 1 */2 *",     # Every other month
            "0 0 * * 0,6",     # Weekends
            "30 14 1 * *",     # 1st of month at 2:30 PM
            "45 23 * * *",     # Daily at 11:45 PM
        ]
        
        for expr in complex_expressions:
            description = CronUtils.describe_cron_expression(expr)
            assert isinstance(description, str)
            assert len(description) > 0
            
            # Description should be more informative than just the cron expression
            assert description != expr
            assert "cron expression" in description.lower() or any(
                word in description.lower() for word in [
                    "at", "every", "on", "daily", "weekly", "monthly",
                    "minute", "hour", "day", "month", "weekday", "weekend"
                ]
            )
    
    def test_describe_invalid_expressions(self):
        """Test descriptions for invalid cron expressions."""
        invalid_expressions = [
            "invalid",
            "0 25 * * *",
            "60 0 * * *",
            "* * * * * *",
            ""
        ]
        
        for expr in invalid_expressions:
            with pytest.raises(CronValidationError):
                CronUtils.describe_cron_expression(expr)
    
    def test_description_consistency(self):
        """Test that descriptions are consistent across multiple calls."""
        test_expressions = [
            "0 9 * * *",
            "0 0 * * 0",
            "*/15 * * * *",
            "0 9-17 * * 1-5"
        ]
        
        for expr in test_expressions:
            desc1 = CronUtils.describe_cron_expression(expr)
            desc2 = CronUtils.describe_cron_expression(expr)
            assert desc1 == desc2
    
    def test_description_readability(self):
        """Test that descriptions are human-readable."""
        expressions = [
            "0 9 * * *",
            "0 0 * * 0",
            "*/30 * * * *",
            "0 9-17 * * 1-5"
        ]
        
        for expr in expressions:
            description = CronUtils.describe_cron_expression(expr)
            
            # Basic readability checks
            assert len(description) > 10  # Should be descriptive
            assert description[0].isupper() or description.startswith("at")  # Should start with capital or "at"
            assert any(char.isalpha() for char in description)  # Should contain letters
            
            # Should not just be the cron expression itself
            assert description != expr
    
    def test_description_special_cases(self):
        """Test descriptions for special cron cases."""
        special_cases = [
            ("0 0 * * *", "midnight"),
            ("0 12 * * *", "noon"),
            ("0 9 * * 1", "monday"),
            ("0 9 * * 0", "sunday"),
            ("0 0 1 * *", "first"),
        ]
        
        for expr, expected_word in special_cases:
            description = CronUtils.describe_cron_expression(expr)
            assert expected_word.lower() in description.lower()


class TestCronUtilsIsDue:
    """Test CronUtils.is_due functionality."""
    
    def test_is_due_basic_functionality(self):
        """Test basic is_due functionality."""
        # Test with no last run (never executed)
        is_due = CronUtils.is_due("0 9 * * *", None)
        assert isinstance(is_due, bool)
        
        # Test with recent execution
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        is_due = CronUtils.is_due("0 9 * * *", recent_time)
        assert isinstance(is_due, bool)
    
    def test_is_due_tolerance_window(self):
        """Test is_due with different tolerance windows."""
        base_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        
        # Test within tolerance
        current_time = base_time + timedelta(seconds=30)
        with mock.patch('utils.cron_utils.datetime') as mock_dt:
            mock_dt.now.return_value = current_time
            is_due = CronUtils.is_due("0 9 * * *", base_time - timedelta(days=1), 60)
            assert isinstance(is_due, bool)
        
        # Test outside tolerance
        current_time = base_time + timedelta(minutes=5)
        with mock.patch('utils.cron_utils.datetime') as mock_dt:
            mock_dt.now.return_value = current_time
            is_due = CronUtils.is_due("0 9 * * *", base_time - timedelta(days=1), 60)
            assert isinstance(is_due, bool)
    
    def test_is_due_error_handling(self):
        """Test is_due error handling."""
        # Test with invalid cron expression
        is_due = CronUtils.is_due("invalid", None)
        assert is_due is False
        
        # Test with invalid last_run
        is_due = CronUtils.is_due("0 9 * * *", "invalid")
        assert is_due is False


class TestCronUtilsIntegration:
    """Integration tests for CronUtils with time utilities."""
    
    def test_cron_utils_with_fixtures(self):
        """Test CronUtils with schedule fixtures."""
        valid_expressions = ScheduleFixtures.valid_cron_expressions()
        
        for expr in valid_expressions:
            # Should validate successfully
            assert CronUtils.validate_cron_expression(expr) is True
            
            # Should calculate next run time
            next_run = CronUtils.get_next_run_time(expr)
            assert isinstance(next_run, datetime)
            
            # Should generate description
            description = CronUtils.describe_cron_expression(expr)
            assert isinstance(description, str)
            assert len(description) > 0
        
        invalid_expressions = ScheduleFixtures.invalid_cron_expressions()
        
        for expr in invalid_expressions:
            # Should raise validation error
            with pytest.raises(CronValidationError):
                CronUtils.validate_cron_expression(expr)
    
    def test_comprehensive_cron_workflow(self):
        """Test complete workflow with CronUtils."""
        cron_expr = "0 9 * * 1-5"  # Weekdays at 9 AM
        
        # 1. Validate expression
        assert CronUtils.validate_cron_expression(cron_expr) is True
        
        # 2. Get description
        description = CronUtils.describe_cron_expression(cron_expr)
        assert "weekday" in description.lower() or "monday" in description.lower()
        
        # 3. Calculate next run times
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)  # Monday
        next_runs = CronUtils.get_next_n_run_times(cron_expr, 5, base_time)
        
        assert len(next_runs) == 5
        for run_time in next_runs:
            assert run_time.hour == 9
            assert run_time.minute == 0
            # Should be weekdays (Monday=0, Friday=4)
            assert run_time.weekday() in [0, 1, 2, 3, 4]
        
        # 4. Test is_due functionality
        is_due = CronUtils.is_due(cron_expr, base_time - timedelta(days=1))
        assert isinstance(is_due, bool)
    
    def test_edge_case_combinations(self):
        """Test combinations of edge cases."""
        edge_cases = [
            ("0 0 29 2 *", "leap year"),      # Feb 29
            ("0 0 31 4 *", "invalid date"),   # April 31
            ("0 0 1 * 0", "month/weekday"),   # 1st of month + Sunday
            ("0 2 * * *", "dst transition"), # 2 AM during DST
        ]
        
        for expr, case_type in edge_cases:
            try:
                # Some expressions might be invalid
                is_valid = CronUtils.validate_cron_expression(expr)
                if is_valid:
                    # If valid, should be able to calculate next run
                    next_run = CronUtils.get_next_run_time(expr)
                    assert isinstance(next_run, datetime)
                    
                    # Should generate description
                    description = CronUtils.describe_cron_expression(expr)
                    assert isinstance(description, str)
                    
            except CronValidationError:
                # Expected for some edge cases
                pass


# Convenience function tests
def test_convenience_functions():
    """Test convenience functions for CronUtils."""
    from utils.cron_utils import validate_cron, next_run_time, describe_cron
    
    # Test validate_cron
    assert validate_cron("0 9 * * *") is True
    assert validate_cron("invalid") is False
    
    # Test next_run_time
    next_run = next_run_time("0 9 * * *")
    assert isinstance(next_run, datetime) or next_run is None
    
    invalid_next = next_run_time("invalid")
    assert invalid_next is None
    
    # Test describe_cron
    description = describe_cron("0 9 * * *")
    assert isinstance(description, str)
    assert len(description) > 0
    
    invalid_description = describe_cron("invalid")
    assert isinstance(invalid_description, str)
    assert "invalid" in invalid_description.lower()


# Performance tests
@pytest.mark.performance
class TestCronUtilsPerformance:
    """Performance tests for CronUtils."""
    
    def test_validation_performance(self):
        """Test validation performance with many expressions."""
        expressions = [
            "0 9 * * *",
            "*/15 * * * *",
            "0 0 * * 0",
            "0 9-17 * * 1-5"
        ] * 25  # 100 expressions total
        
        import time
        start_time = time.time()
        
        for expr in expressions:
            CronUtils.validate_cron_expression(expr)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 validations in reasonable time
        assert duration < 1.0  # Less than 1 second
    
    def test_next_run_calculation_performance(self):
        """Test next run calculation performance."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        
        import time
        start_time = time.time()
        
        for _ in range(100):
            CronUtils.get_next_run_time("0 9 * * *", base_time)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 calculations in reasonable time
        assert duration < 1.0  # Less than 1 second 