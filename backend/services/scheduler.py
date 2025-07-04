"""
Background Scheduler Service for the AI Agent Platform.

Provides:
- Continuous monitoring of enabled schedules
- Automatic job creation for due schedules
- Next run time updates after execution
- Error handling and logging for scheduler operations
- Graceful startup and shutdown
- Schedule statistics tracking

The scheduler runs as a background asyncio task and integrates with
the existing job pipeline and database systems.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
import uuid

from database import get_supabase_client
from models.schedule import Schedule, ScheduleStatus
from utils.cron_utils import CronUtils, CronValidationError
from job_pipeline import JobPipeline, get_job_pipeline
from config.environment import get_settings

# Setup logging
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Background service for monitoring and executing scheduled jobs.
    
    This service continuously monitors the database for enabled schedules
    and creates jobs when they are due for execution. It handles:
    - Schedule monitoring and execution
    - Next run time calculations
    - Error handling and logging
    - Statistics tracking
    - Graceful shutdown
    """
    
    def __init__(self, check_interval: int = 30, tolerance_seconds: int = 60):
        """
        Initialize the scheduler service.
        
        Args:
            check_interval: How often to check for due schedules (seconds)
            tolerance_seconds: Tolerance window for due schedule detection
        """
        self.check_interval = check_interval
        # Reduce default tolerance to minimize race condition window
        self.tolerance_seconds = min(tolerance_seconds, 30) if tolerance_seconds > 30 else tolerance_seconds
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.settings = get_settings()
        
        # Statistics
        self.stats = {
            "total_checks": 0,
            "schedules_processed": 0,
            "jobs_created": 0,
            "errors": 0,
            "last_check": None,
            "last_error": None,
            "start_time": None
        }
        
        logger.info(f"SchedulerService initialized with {check_interval}s check interval, {self.tolerance_seconds}s tolerance")
    
    async def start(self):
        """Start the scheduler service."""
        if self.running:
            logger.warning("Scheduler service is already running")
            return
        
        self.running = True
        self.stats["start_time"] = datetime.now(timezone.utc)
        
        # Start the background task
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler service started")
    
    async def stop(self):
        """Stop the scheduler service gracefully."""
        if not self.running:
            logger.warning("Scheduler service is not running")
            return
        
        self.running = False
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled")
        
        logger.info("Scheduler service stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for due schedules."""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                await self._check_and_process_schedules()
                self.stats["total_checks"] += 1
                self.stats["last_check"] = datetime.now(timezone.utc)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                logger.error(f"Error in scheduler loop: {e}")
                
                # Continue running but wait before retrying
                await asyncio.sleep(min(self.check_interval, 60))
        
        logger.info("Scheduler loop ended")
    
    async def _check_and_process_schedules(self):
        """Check for due schedules and process them."""
        try:
            supabase = get_supabase_client()
            current_time = datetime.now(timezone.utc)
            
            # Calculate the time window for due schedules
            tolerance_window = current_time + timedelta(seconds=self.tolerance_seconds)
            
            # Get enabled schedules that are due
            result = supabase.table("schedules").select(
                "id, user_id, title, agent_name, cron_expression, agent_config_data, next_run, last_run"
            ).eq("enabled", True).not_.is_(
                "next_run", "null"
            ).lte("next_run", tolerance_window.isoformat()).execute()
            
            if not result.data:
                return
            
            logger.info(f"Found {len(result.data)} schedules due for execution")
            
            # Process each due schedule
            for schedule_data in result.data:
                try:
                    await self._process_schedule(schedule_data, current_time)
                    self.stats["schedules_processed"] += 1
                except Exception as e:
                    logger.error(f"Error processing schedule {schedule_data['id']}: {e}")
                    await self._handle_schedule_error(schedule_data["id"], str(e))
                    
        except Exception as e:
            logger.error(f"Error checking schedules: {e}")
            raise
    
    async def _process_schedule(self, schedule_data: Dict[str, Any], current_time: datetime):
        """Process a single due schedule."""
        schedule_id = schedule_data["id"]
        user_id = schedule_data["user_id"]
        title = schedule_data["title"]
        agent_name = schedule_data["agent_name"]
        cron_expression = schedule_data["cron_expression"]
        agent_config_data = schedule_data["agent_config_data"]
        
        logger.info(f"Processing schedule '{title}' (ID: {schedule_id})")
        
        try:
            # Verify the schedule is actually due
            next_run_str = schedule_data.get("next_run")
            if not next_run_str:
                logger.warning(f"Schedule {schedule_id} has no next_run time, skipping")
                return
            
            next_run = datetime.fromisoformat(next_run_str.replace('Z', '+00:00'))
            
            # Check if really due (within tolerance)
            time_diff = (current_time - next_run).total_seconds()
            if time_diff < -self.tolerance_seconds:
                logger.debug(f"Schedule {schedule_id} not yet due (still {-time_diff:.1f}s early)")
                return
            
            # Calculate next run time FIRST
            try:
                next_next_run = CronUtils.get_next_run_time(cron_expression, current_time)
            except CronValidationError as e:
                logger.error(f"Invalid cron expression for schedule {schedule_id}: {e}")
                await self._disable_schedule_with_error(schedule_id, f"Invalid cron expression: {e}")
                return
            
            # ATOMIC CLAIM AND UPDATE: Update schedule BEFORE creating job
            # This prevents race conditions by ensuring only one scheduler can claim a schedule
            success = await self._atomic_claim_schedule(
                schedule_id, current_time, next_next_run, next_run
            )
            
            if not success:
                logger.debug(f"Schedule {schedule_id} was already claimed by another scheduler instance")
                return
            
            # Now create the job - at this point we own this execution
            job_id = await self._create_scheduled_job(
                schedule_id, user_id, agent_name, agent_config_data, title
            )
            
            self.stats["jobs_created"] += 1
            logger.info(
                f"Successfully created job {job_id} for schedule '{title}', "
                f"next run: {next_next_run.isoformat()}"
            )
            
        except Exception as e:
            logger.error(f"Error processing schedule {schedule_id}: {e}")
            raise
    
    async def _atomic_claim_schedule(
        self, 
        schedule_id: str, 
        execution_time: datetime, 
        next_run: datetime,
        expected_next_run: datetime
    ) -> bool:
        """
        Atomically claim a schedule for execution.
        
        This prevents race conditions by updating the schedule's next_run time
        only if it matches the expected value (optimistic locking).
        
        IMPORTANT: For maximum reliability in high-concurrency environments,
        consider adding a database unique constraint on (schedule_id, next_run)
        or implementing distributed locking with Redis.
        
        Args:
            schedule_id: Schedule to claim
            execution_time: Current execution time
            next_run: New next run time to set
            expected_next_run: Expected current next_run value
            
        Returns:
            True if successfully claimed, False if already claimed by another instance
        """
        try:
            supabase = get_supabase_client()
            
            update_data = {
                "last_run": execution_time.isoformat(),
                "next_run": next_run.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Use optimistic locking: only update if next_run hasn't changed
            # This ensures only one scheduler instance can claim a schedule
            result = supabase.table("schedules").update(update_data).eq("id", schedule_id).eq(
                "next_run", expected_next_run.isoformat()
            ).execute()
            
            if result.data and len(result.data) > 0:
                logger.debug(f"Successfully claimed schedule {schedule_id}")
                return True
            else:
                logger.debug(f"Failed to claim schedule {schedule_id} - already processed by another instance")
                return False
                
        except Exception as e:
            logger.error(f"Error claiming schedule {schedule_id}: {e}")
            return False
    
    async def _create_scheduled_job(
        self, 
        schedule_id: str, 
        user_id: str, 
        agent_name: str, 
        agent_config_data: Dict[str, Any], 
        schedule_title: str
    ) -> str:
        """Create a job for a scheduled execution."""
        try:
            supabase = get_supabase_client()
            job_pipeline = get_job_pipeline()
            
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Extract job data from agent configuration
            job_data = agent_config_data.get("job_data", {})
            
            # Prepare job data for creation
            job_record = {
                "id": job_id,
                "user_id": user_id,
                "agent_identifier": agent_name,
                "title": f"[Scheduled] {schedule_title}",
                "data": job_data,
                "status": "pending",
                "priority": agent_config_data.get("execution", {}).get("priority", 5),
                "schedule_id": schedule_id,
                "execution_source": "scheduled",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "tags": ["scheduled", "automated"]
            }
            
            # Insert job into database
            result = supabase.table("jobs").insert(job_record).execute()
            
            if not result.data:
                raise Exception("Failed to create job record")
            
            # Add job to processing pipeline
            pipeline_submitted = await job_pipeline.submit_job(
                job_id=job_id,
                user_id=user_id,
                agent_name=agent_name,
                job_data=job_data,
                priority=job_record["priority"],
                tags=job_record["tags"]
            )
            
            if not pipeline_submitted:
                logger.error(f"Failed to submit scheduled job {job_id} to pipeline")
                raise Exception("Failed to submit job to processing pipeline")
            
            logger.info(f"Created and submitted scheduled job {job_id} for schedule {schedule_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating scheduled job: {e}")
            raise
    
    async def _handle_schedule_error(self, schedule_id: str, error_message: str):
        """Handle errors that occur during schedule processing."""
        try:
            logger.error(f"Schedule error for {schedule_id}: {error_message}")
            # Could implement additional error handling here like:
            # - Incrementing error counters
            # - Disabling schedules after too many errors
            # - Sending notifications
            
        except Exception as e:
            logger.error(f"Error handling schedule error for {schedule_id}: {e}")
    
    async def _disable_schedule_with_error(self, schedule_id: str, error_message: str):
        """Disable a schedule due to a critical error."""
        try:
            supabase = get_supabase_client()
            
            update_data = {
                "enabled": False,
                "next_run": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = supabase.table("schedules").update(update_data).eq("id", schedule_id).execute()
            
            if result.data:
                logger.warning(f"Disabled schedule {schedule_id} due to error: {error_message}")
            else:
                logger.error(f"Failed to disable schedule {schedule_id}")
                
        except Exception as e:
            logger.error(f"Error disabling schedule {schedule_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        stats = self.stats.copy()
        stats["running"] = self.running
        stats["uptime_seconds"] = (
            (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
            if self.stats["start_time"] else 0
        )
        return stats
    
    async def force_check(self):
        """Force an immediate check of schedules (for testing/debugging)."""
        if not self.running:
            raise RuntimeError("Scheduler service is not running")
        
        logger.info("Forcing immediate schedule check")
        await self._check_and_process_schedules()

# Global scheduler instance
_scheduler_service: Optional[SchedulerService] = None

def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    global _scheduler_service
    if _scheduler_service is None:
        settings = get_settings()
        _scheduler_service = SchedulerService(
            check_interval=getattr(settings, 'scheduler_check_interval', 30),
            tolerance_seconds=getattr(settings, 'scheduler_tolerance_seconds', 30)
        )
    return _scheduler_service

async def start_scheduler_service():
    """Start the global scheduler service."""
    scheduler = get_scheduler_service()
    await scheduler.start()
    logger.info("Global scheduler service started")

async def stop_scheduler_service():
    """Stop the global scheduler service."""
    scheduler = get_scheduler_service()
    await scheduler.stop()
    logger.info("Global scheduler service stopped")

def get_scheduler_stats() -> Dict[str, Any]:
    """Get statistics from the global scheduler service."""
    scheduler = get_scheduler_service()
    return scheduler.get_stats() 