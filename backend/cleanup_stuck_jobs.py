#!/usr/bin/env python3
"""
Cleanup script for stuck scheduled jobs.

This script identifies and cleans up jobs that were created by the scheduler
but never submitted to the job pipeline due to the bug in SchedulerService.

Usage:
    python cleanup_stuck_jobs.py --dry-run    # Preview what would be fixed
    python cleanup_stuck_jobs.py --execute     # Actually fix the jobs
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from database import get_supabase_client
from job_pipeline import get_job_pipeline
from logging_system import get_logger

logger = get_logger(__name__)

class JobCleanupService:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.supabase = get_supabase_client()
        
    async def find_stuck_scheduled_jobs(self, hours_old: int = 1) -> List[Dict[str, Any]]:
        """Find scheduled jobs that have been pending for too long."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)
        
        result = self.supabase.table("jobs").select(
            "id, user_id, agent_identifier, title, data, priority, tags, created_at, schedule_id"
        ).eq("status", "pending").eq("execution_source", "scheduled").lt(
            "created_at", cutoff_time.isoformat()
        ).execute()
        
        return result.data or []
    
    async def resubmit_job_to_pipeline(self, job: Dict[str, Any]) -> bool:
        """Resubmit a job to the pipeline."""
        try:
            pipeline = get_job_pipeline()
            
            success = await pipeline.submit_job(
                job_id=job["id"],
                user_id=job["user_id"],
                agent_name=job["agent_identifier"],
                job_data=job["data"] or {},
                priority=job.get("priority", 5),
                tags=job.get("tags", [])
            )
            
            if success:
                logger.info(f"Successfully resubmitted job {job['id']} to pipeline")
            else:
                logger.error(f"Failed to resubmit job {job['id']} to pipeline")
                
            return success
            
        except Exception as e:
            logger.error(f"Error resubmitting job {job['id']}: {e}")
            return False
    
    async def mark_job_failed(self, job_id: str, reason: str) -> bool:
        """Mark a job as failed."""
        try:
            update_data = {
                "status": "failed",
                "error_message": reason,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("jobs").update(update_data).eq("id", job_id).execute()
            
            if result.data:
                logger.info(f"Marked job {job_id} as failed: {reason}")
                return True
            else:
                logger.error(f"Failed to update job {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error marking job {job_id} as failed: {e}")
            return False
    
    async def cleanup_stuck_jobs(self):
        """Main cleanup process."""
        logger.info("Starting cleanup of stuck scheduled jobs")
        
        # Find jobs stuck for more than 1 hour
        stuck_jobs = await self.find_stuck_scheduled_jobs(hours_old=1)
        
        if not stuck_jobs:
            logger.info("No stuck jobs found")
            return
        
        logger.info(f"Found {len(stuck_jobs)} stuck scheduled jobs")
        
        resubmitted = 0
        failed = 0
        errors = 0
        
        for job in stuck_jobs:
            job_id = job["id"]
            created_at = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
            
            logger.info(f"Processing stuck job {job_id} (age: {age_hours:.1f} hours)")
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would process job {job_id}")
                continue
            
            try:
                # If job is less than 6 hours old, try to resubmit
                if age_hours < 6:
                    if await self.resubmit_job_to_pipeline(job):
                        resubmitted += 1
                    else:
                        # If resubmission fails, mark as failed
                        if await self.mark_job_failed(job_id, "Failed to resubmit stuck job to pipeline"):
                            failed += 1
                        else:
                            errors += 1
                else:
                    # If job is too old, mark as failed
                    if await self.mark_job_failed(job_id, f"Job stuck in pending status for {age_hours:.1f} hours"):
                        failed += 1  
                    else:
                        errors += 1
                        
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                errors += 1
        
        logger.info(
            f"Cleanup completed. Resubmitted: {resubmitted}, Failed: {failed}, Errors: {errors}"
        )

async def main():
    """Main entry point."""
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        logger.info("Running in DRY RUN mode. Use --execute to actually fix jobs.")
    else:
        logger.info("Running in EXECUTE mode. Jobs will be modified.")
    
    cleanup_service = JobCleanupService(dry_run=dry_run)
    await cleanup_service.cleanup_stuck_jobs()

if __name__ == "__main__":
    asyncio.run(main()) 