"""
Cron expression utilities for the AI Agent Platform scheduling system.

Provides:
- Cron expression validation using croniter
- Next run time calculation with timezone support
- Cron expression parsing and description generation
- Timezone-aware scheduling utilities

Dependencies:
- croniter>=2.0.0 for cron expression handling
"""

from croniter import croniter, CroniterBadCronError, CroniterBadDateError
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import pytz
import logging

logger = logging.getLogger(__name__)

class CronValidationError(Exception):
    """Custom exception for cron validation errors"""
    pass

class CronUtils:
    """Utility class for cron expression operations"""
    
    @staticmethod
    def validate_cron_expression(cron_expression: str) -> bool:
        """
        Validate a cron expression using croniter.
        
        Args:
            cron_expression: The cron expression to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            CronValidationError: If the cron expression is invalid
        """
        try:
            if not cron_expression or not cron_expression.strip():
                raise CronValidationError("Cron expression cannot be empty")
            
            # Basic format validation
            parts = cron_expression.strip().split()
            if len(parts) != 5:
                raise CronValidationError("Cron expression must have exactly 5 fields")
            
            # Use croniter to validate the expression
            base_time = datetime.now(timezone.utc)
            cron = croniter(cron_expression.strip(), base_time)
            
            # Try to get the next execution time to ensure it's valid
            next_time = cron.get_next(datetime)
            if not next_time:
                raise CronValidationError("Could not calculate next execution time")
                
            return True
            
        except CroniterBadCronError as e:
            raise CronValidationError(f"Invalid cron expression: {str(e)}")
        except CroniterBadDateError as e:
            raise CronValidationError(f"Invalid date in cron expression: {str(e)}")
        except CronValidationError:
            # Re-raise CronValidationError without modification
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating cron expression '{cron_expression}': {e}")
            raise CronValidationError(f"Cron validation failed: {str(e)}")
    
    @staticmethod
    def get_next_run_time(
        cron_expression: str, 
        base_time: Optional[datetime] = None,
        timezone_str: Optional[str] = None
    ) -> datetime:
        """
        Calculate the next run time for a cron expression.
        
        Args:
            cron_expression: The cron expression
            base_time: Base time to calculate from (defaults to current UTC time)
            timezone_str: Timezone string (e.g., 'America/New_York', defaults to UTC)
            
        Returns:
            datetime: Next execution time in UTC
            
        Raises:
            CronValidationError: If calculation fails
        """
        try:
            # Validate the cron expression first
            CronUtils.validate_cron_expression(cron_expression)
            
            # Set base time
            if base_time is None:
                base_time = datetime.now(timezone.utc)
            elif base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc)
            
            # Handle timezone conversion
            if timezone_str:
                try:
                    tz = pytz.timezone(timezone_str)
                    base_time = base_time.astimezone(tz)
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning(f"Unknown timezone '{timezone_str}', using UTC")
                    base_time = base_time.astimezone(timezone.utc)
            
            # Calculate next run time
            cron = croniter(cron_expression.strip(), base_time)
            next_time = cron.get_next(datetime)
            
            # Ensure result is in UTC
            if next_time.tzinfo is None:
                next_time = next_time.replace(tzinfo=timezone.utc)
            else:
                next_time = next_time.astimezone(timezone.utc)
            
            return next_time
            
        except CronValidationError:
            raise
        except Exception as e:
            logger.error(f"Error calculating next run time for '{cron_expression}': {e}")
            raise CronValidationError(f"Could not calculate next run time: {str(e)}")
    
    @staticmethod
    def get_next_n_run_times(
        cron_expression: str,
        count: int = 5,
        base_time: Optional[datetime] = None,
        timezone_str: Optional[str] = None
    ) -> List[datetime]:
        """
        Get the next N execution times for a cron expression.
        
        Args:
            cron_expression: The cron expression
            count: Number of future execution times to return
            base_time: Base time to calculate from (defaults to current UTC time)
            timezone_str: Timezone string (defaults to UTC)
            
        Returns:
            List[datetime]: List of next execution times in UTC
            
        Raises:
            CronValidationError: If calculation fails
        """
        try:
            # Validate inputs
            if count <= 0:
                raise CronValidationError("Count must be positive")
            if count > 100:
                raise CronValidationError("Count cannot exceed 100")
            
            # Validate the cron expression
            CronUtils.validate_cron_expression(cron_expression)
            
            # Set base time
            if base_time is None:
                base_time = datetime.now(timezone.utc)
            elif base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc)
            
            # Handle timezone conversion
            if timezone_str:
                try:
                    tz = pytz.timezone(timezone_str)
                    base_time = base_time.astimezone(tz)
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning(f"Unknown timezone '{timezone_str}', using UTC")
                    base_time = base_time.astimezone(timezone.utc)
            
            # Calculate next run times
            cron = croniter(cron_expression.strip(), base_time)
            next_times = []
            
            for _ in range(count):
                next_time = cron.get_next(datetime)
                # Ensure result is in UTC
                if next_time.tzinfo is None:
                    next_time = next_time.replace(tzinfo=timezone.utc)
                else:
                    next_time = next_time.astimezone(timezone.utc)
                next_times.append(next_time)
            
            return next_times
            
        except CronValidationError:
            raise
        except Exception as e:
            logger.error(f"Error calculating next {count} run times for '{cron_expression}': {e}")
            raise CronValidationError(f"Could not calculate next run times: {str(e)}")
    
    @staticmethod
    def describe_cron_expression(cron_expression: str) -> str:
        """
        Generate a human-readable description of a cron expression.
        
        Args:
            cron_expression: The cron expression to describe
            
        Returns:
            str: Human-readable description
            
        Raises:
            CronValidationError: If the cron expression is invalid
        """
        try:
            # Validate first
            CronUtils.validate_cron_expression(cron_expression)
            
            parts = cron_expression.strip().split()
            
            # Basic descriptions for common patterns
            common_patterns = {
                "* * * * *": "Every minute",
                "0 * * * *": "Every hour",
                "0 0 * * *": "Daily at midnight",
                "0 12 * * *": "Daily at noon",
                "0 9 * * *": "Daily at 9:00 AM",
                "0 9 * * 1": "Every Monday at 9:00 AM",
                "0 9 * * 1-5": "Every weekday at 9:00 AM",
                "0 0 1 * *": "First day of every month at midnight",
                "0 0 * * 0": "Every Sunday at midnight",
            }
            
            if cron_expression.strip() in common_patterns:
                return common_patterns[cron_expression.strip()]
            
            # Try to build a description from parts
            minute, hour, day, month, weekday = parts[:5]
            
            description_parts = []
            
            # Time part
            if minute == "0" and hour != "*":
                if hour.isdigit():
                    description_parts.append(f"at {hour}:00")
                else:
                    description_parts.append(f"at hour {hour}")
            elif minute != "*" and hour != "*":
                if minute.isdigit() and hour.isdigit():
                    description_parts.append(f"at {hour}:{minute.zfill(2)}")
                else:
                    description_parts.append(f"at {hour}:{minute}")
            elif minute != "*":
                description_parts.append(f"at minute {minute}")
            elif hour != "*":
                description_parts.append(f"at hour {hour}")
            
            # Day/weekday part
            if weekday != "*":
                if weekday.isdigit():
                    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    if 0 <= int(weekday) <= 6:
                        description_parts.append(f"on {weekday_names[int(weekday)]}")
                    else:
                        description_parts.append(f"on weekday {weekday}")
                else:
                    description_parts.append(f"on weekday {weekday}")
            elif day != "*":
                if day.isdigit():
                    description_parts.append(f"on day {day} of the month")
                else:
                    description_parts.append(f"on day {day}")
            
            # Month part
            if month != "*":
                if month.isdigit():
                    month_names = ["", "January", "February", "March", "April", "May", "June",
                                 "July", "August", "September", "October", "November", "December"]
                    if 1 <= int(month) <= 12:
                        description_parts.append(f"in {month_names[int(month)]}")
                    else:
                        description_parts.append(f"in month {month}")
                elif "," in month:
                    # Handle comma-separated months
                    month_names = ["", "January", "February", "March", "April", "May", "June",
                                 "July", "August", "September", "October", "November", "December"]
                    month_parts = month.split(",")
                    month_name_list = []
                    for m in month_parts:
                        if m.strip().isdigit() and 1 <= int(m.strip()) <= 12:
                            month_name_list.append(month_names[int(m.strip())])
                        else:
                            month_name_list.append(m.strip())
                    if month_name_list:
                        description_parts.append(f"in {' and '.join(month_name_list)}")
                    else:
                        description_parts.append(f"in month {month}")
                else:
                    description_parts.append(f"in month {month}")
            
            if description_parts:
                return "Runs " + " ".join(description_parts)
            else:
                return f"Cron expression: {cron_expression}"
                
        except CronValidationError:
            raise
        except Exception as e:
            logger.error(f"Error describing cron expression '{cron_expression}': {e}")
            return f"Cron expression: {cron_expression}"
    
    @staticmethod
    def is_due(cron_expression: str, last_run: Optional[datetime] = None, tolerance_seconds: int = 60) -> bool:
        """
        Check if a cron job is due to run.
        
        Args:
            cron_expression: The cron expression
            last_run: Last execution time (None if never run)
            tolerance_seconds: Tolerance window in seconds
            
        Returns:
            bool: True if the job is due to run
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            if last_run is None:
                # Never run, check if we're past the first scheduled time
                next_time = CronUtils.get_next_run_time(cron_expression, current_time - timedelta(days=1))
                return next_time <= current_time
            
            # Calculate next run time after last run
            next_time = CronUtils.get_next_run_time(cron_expression, last_run)
            
            # Check if we're within the tolerance window
            time_diff = (current_time - next_time).total_seconds()
            return -tolerance_seconds <= time_diff <= tolerance_seconds
            
        except Exception as e:
            logger.error(f"Error checking if cron job is due: {e}")
            return False

# Convenience functions for common use cases
def validate_cron(cron_expression: str) -> bool:
    """Validate a cron expression."""
    try:
        return CronUtils.validate_cron_expression(cron_expression)
    except CronValidationError:
        return False

def next_run_time(cron_expression: str, timezone_str: Optional[str] = None) -> Optional[datetime]:
    """Get the next run time for a cron expression."""
    try:
        return CronUtils.get_next_run_time(cron_expression, timezone_str=timezone_str)
    except CronValidationError:
        return None

def describe_cron(cron_expression: str) -> str:
    """Get a human-readable description of a cron expression."""
    try:
        return CronUtils.describe_cron_expression(cron_expression)
    except CronValidationError:
        return f"Invalid cron expression: {cron_expression}" 