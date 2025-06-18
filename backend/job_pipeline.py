"""
Job Processing Pipeline with Status Updates

This module provides:
- Asynchronous job queue management
- Job execution pipeline with status tracking
- Real-time status updates to database
- Error handling and retry mechanisms
- Job prioritization and scheduling
"""

import asyncio
import json
import time
import uuid
from asyncio import Queue, Task
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, field

from models import JobStatus
from database import get_database_operations
from agent import BaseAgent, AgentExecutionResult, get_agent_registry
from agent_framework import get_registered_agents, validate_job_data
from logging_system import get_logger

logger = get_logger(__name__)

class JobPriority(int, Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10

@dataclass
class JobTask:
    """Internal job task representation for pipeline processing"""
    job_id: str
    user_id: str
    agent_name: str
    job_data: Dict[str, Any]
    priority: int = JobPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.scheduled_at is None:
            self.scheduled_at = self.created_at

    @property
    def is_ready(self) -> bool:
        """Check if job is ready to execute"""
        return datetime.now(timezone.utc) >= self.scheduled_at

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries

class JobExecutionStatus:
    """Track job execution status and metrics"""
    
    def __init__(self):
        self.active_jobs: Set[str] = set()
        self.completed_jobs: int = 0
        self.failed_jobs: int = 0
        self.retried_jobs: int = 0
        self.start_time: datetime = datetime.now(timezone.utc)
        self.job_metrics: Dict[str, Dict[str, Any]] = {}

    def start_job(self, job_id: str):
        """Mark job as started"""
        self.active_jobs.add(job_id)
        self.job_metrics[job_id] = {
            'start_time': datetime.now(timezone.utc),
            'status': JobStatus.running
        }

    def complete_job(self, job_id: str, success: bool, execution_time: float):
        """Mark job as completed"""
        self.active_jobs.discard(job_id)
        if success:
            self.completed_jobs += 1
        else:
            self.failed_jobs += 1
        
        if job_id in self.job_metrics:
            self.job_metrics[job_id].update({
                'end_time': datetime.now(timezone.utc),
                'success': success,
                'execution_time': execution_time,
                'status': JobStatus.completed if success else JobStatus.failed
            })

    def retry_job(self, job_id: str):
        """Mark job as retried"""
        self.retried_jobs += 1
        if job_id in self.job_metrics:
            self.job_metrics[job_id]['retries'] = self.job_metrics[job_id].get('retries', 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current pipeline metrics"""
        uptime = datetime.now(timezone.utc) - self.start_time
        return {
            'active_jobs': len(self.active_jobs),
            'completed_jobs': self.completed_jobs,
            'failed_jobs': self.failed_jobs,
            'retried_jobs': self.retried_jobs,
            'total_processed': self.completed_jobs + self.failed_jobs,
            'success_rate': (self.completed_jobs / max(1, self.completed_jobs + self.failed_jobs)) * 100,
            'uptime_seconds': uptime.total_seconds(),
            'jobs_per_minute': (self.completed_jobs + self.failed_jobs) / max(1, uptime.total_seconds() / 60)
        }

class JobPipeline:
    """
    Asynchronous job processing pipeline with status updates.
    
    Features:
    - Priority-based job queuing
    - Concurrent job execution with configurable limits
    - Real-time status updates to database
    - Automatic retry mechanism for failed jobs
    - Comprehensive error handling and logging
    - Job scheduling and delayed execution
    - Performance monitoring and metrics
    """

    def __init__(
        self,
        max_concurrent_jobs: int = 5,
        max_queue_size: int = 1000,
        cleanup_interval: int = 300,  # 5 minutes
        retry_delay_base: float = 2.0  # exponential backoff base
    ):
        """
        Initialize the job pipeline.
        
        Args:
            max_concurrent_jobs: Maximum number of jobs to execute concurrently
            max_queue_size: Maximum size of the job queue
            cleanup_interval: Interval in seconds for cleanup operations
            retry_delay_base: Base delay for exponential backoff on retries
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_queue_size = max_queue_size
        self.cleanup_interval = cleanup_interval
        self.retry_delay_base = retry_delay_base
        
        # Job queue with priority support
        self.job_queue: Queue[JobTask] = Queue(maxsize=max_queue_size)
        self.scheduled_jobs: List[JobTask] = []
        
        # Active job tracking
        self.active_tasks: Dict[str, Task] = {}
        self.status_tracker = JobExecutionStatus()
        
        # Pipeline state
        self.is_running = False
        self.is_shutdown = False
        self.worker_tasks: List[Task] = []
        self.cleanup_task: Optional[Task] = None
        
        # Dependencies
        self.db_ops = get_database_operations()
        self.agent_registry = get_agent_registry()
        self.registered_agents = get_registered_agents()
        
        logger.info(
            "Job pipeline initialized",
            max_concurrent=max_concurrent_jobs,
            max_queue_size=max_queue_size
        )

    async def start(self):
        """Start the job pipeline workers"""
        if self.is_running:
            logger.warning("Job pipeline is already running")
            return

        logger.info("Starting job pipeline")
        self.is_running = True
        self.is_shutdown = False

        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)

        # Start scheduler task
        scheduler_task = asyncio.create_task(self._scheduler())
        self.worker_tasks.append(scheduler_task)

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())

        logger.info(f"Job pipeline started with {self.max_concurrent_jobs} workers")

    async def stop(self, timeout: float = 30.0):
        """Stop the job pipeline gracefully"""
        if not self.is_running:
            logger.warning("Job pipeline is not running")
            return

        logger.info("Stopping job pipeline")
        self.is_shutdown = True

        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()

        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.worker_tasks, self.cleanup_task, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Pipeline shutdown timeout reached, forcing stop")

        # Cancel any remaining active job tasks
        for job_id, task in self.active_tasks.items():
            if not task.done():
                logger.warning(f"Cancelling active job: {job_id}")
                task.cancel()

        self.worker_tasks.clear()
        self.active_tasks.clear()
        self.is_running = False

        logger.info("Job pipeline stopped")

    async def submit_job(
        self,
        job_id: str,
        user_id: str,
        agent_name: str,
        job_data: Dict[str, Any],
        priority: int = JobPriority.NORMAL,
        max_retries: int = 3,
        scheduled_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Submit a job to the processing pipeline.
        
        Args:
            job_id: Unique job identifier
            user_id: User ID who submitted the job
            agent_name: Name of the agent to execute the job
            job_data: Job data payload
            priority: Job priority (0-10, higher = more priority)
            max_retries: Maximum number of retry attempts
            scheduled_at: When to execute the job (None = immediately)
            tags: Optional job tags
            metadata: Optional job metadata
            
        Returns:
            True if job was queued successfully, False otherwise
        """
        try:
            # Validate agent exists
            if agent_name not in self.registered_agents:
                logger.error(f"Unknown agent: {agent_name}")
                await self._update_job_status(job_id, JobStatus.failed, 
                                            error_message=f"Unknown agent: {agent_name}")
                return False

            # Create job task
            job_task = JobTask(
                job_id=job_id,
                user_id=user_id,
                agent_name=agent_name,
                job_data=job_data,
                priority=priority,
                max_retries=max_retries,
                scheduled_at=scheduled_at,
                tags=tags,
                metadata=metadata
            )

            # Check if job should be scheduled for later
            if scheduled_at and scheduled_at > datetime.now(timezone.utc):
                self.scheduled_jobs.append(job_task)
                self.scheduled_jobs.sort(key=lambda x: x.scheduled_at)
                logger.info(f"Job {job_id} scheduled for {scheduled_at}")
            else:
                # Add to immediate execution queue
                await self.job_queue.put(job_task)
                logger.info(f"Job {job_id} queued for immediate execution")

            return True

        except Exception as e:
            logger.error(f"Failed to submit job {job_id}", exception=e)
            await self._update_job_status(job_id, JobStatus.failed, 
                                        error_message=f"Job submission failed: {str(e)}")
            return False

    async def _worker(self, worker_name: str):
        """Job processing worker"""
        logger.info(f"Worker {worker_name} started")
        
        while not self.is_shutdown:
            try:
                # Get next job from queue
                job_task = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                # Execute the job
                await self._execute_job_task(job_task, worker_name)
                
            except asyncio.TimeoutError:
                # No jobs in queue, continue polling
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error", exception=e)
                # Continue working despite errors

        logger.info(f"Worker {worker_name} stopped")

    async def _scheduler(self):
        """Scheduled job processor"""
        logger.info("Job scheduler started")
        
        while not self.is_shutdown:
            try:
                current_time = datetime.now(timezone.utc)
                ready_jobs = []
                
                # Find jobs ready for execution
                remaining_jobs = []
                for job_task in self.scheduled_jobs:
                    if job_task.is_ready:
                        ready_jobs.append(job_task)
                    else:
                        remaining_jobs.append(job_task)
                
                self.scheduled_jobs = remaining_jobs
                
                # Queue ready jobs
                for job_task in ready_jobs:
                    try:
                        await self.job_queue.put(job_task)
                        logger.info(f"Scheduled job {job_task.job_id} moved to execution queue")
                    except Exception as e:
                        logger.error(f"Failed to queue scheduled job {job_task.job_id}", exception=e)
                
                # Sleep for a short interval
                await asyncio.sleep(5.0)
                
            except Exception as e:
                logger.error("Scheduler error", exception=e)
                await asyncio.sleep(10.0)

        logger.info("Job scheduler stopped")

    async def _execute_job_task(self, job_task: JobTask, worker_name: str):
        """Execute a single job task"""
        job_id = job_task.job_id
        start_time = time.time()
        
        try:
            logger.info(
                f"Executing job {job_id}",
                worker=worker_name,
                agent=job_task.agent_name,
                user_id=job_task.user_id,
                priority=job_task.priority,
                retry_count=job_task.retry_count
            )
            
            # Update job status to running
            await self._update_job_status(job_id, JobStatus.running)
            self.status_tracker.start_job(job_id)
            
            # Get the agent instance
            agent = self.registered_agents[job_task.agent_name]
            
            # Validate and parse job data
            agent_models = agent.get_models()
            if not agent_models:
                raise ValueError(f"No job models defined for agent {job_task.agent_name}")
            
            # Use the first available model for validation (agents should define one primary model)
            model_class = next(iter(agent_models.values()))
            validated_data = validate_job_data(job_task.job_data, model_class)
            
            # Execute the job
            logger.info("Starting job execution", job_id=job_task.job_id, agent_name=job_task.agent_name)
            
            try:
                result = await agent.execute_job(job_task.job_id, validated_data)
                
                logger.info("Job execution completed", job_id=job_task.job_id, agent_name=job_task.agent_name)
                
            except Exception as e:
                logger.error("Job execution failed", exception=e, job_id=job_task.job_id)
                raise
            
            execution_time = result.execution_time
            
            if result.success:
                # Job completed successfully - properly serialize the result as JSON
                result_text = None
                if result.result:
                    if isinstance(result.result, dict):
                        # If result is a dictionary, convert to proper JSON
                        result_text = json.dumps(result.result, ensure_ascii=False, default=str)
                    else:
                        # If result is already a string, use it directly
                        result_text = str(result.result)
                
                await self._update_job_status(
                    job_id, 
                    JobStatus.completed, 
                    result=result_text,
                    result_format=result.result_format
                )
                
                self.status_tracker.complete_job(job_id, True, execution_time)
                
                logger.info(
                    f"Job {job_id} completed successfully",
                    worker=worker_name,
                    execution_time=execution_time,
                    agent=job_task.agent_name
                )
                
            else:
                # Job failed, check if we should retry
                if job_task.can_retry:
                    await self._retry_job(job_task, result.error_message)
                else:
                    await self._update_job_status(
                        job_id,
                        JobStatus.failed,
                        error_message=result.error_message
                    )
                    
                    self.status_tracker.complete_job(job_id, False, execution_time)
                    
                    logger.error(
                        f"Job {job_id} failed permanently",
                        worker=worker_name,
                        error=result.error_message,
                        retry_count=job_task.retry_count
                    )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Job execution error: {str(e)}"
            
            # Check if we should retry
            if job_task.can_retry:
                await self._retry_job(job_task, error_message)
            else:
                await self._update_job_status(job_id, JobStatus.failed, error_message=error_message)
                self.status_tracker.complete_job(job_id, False, execution_time)
                
                logger.error(
                    f"Job {job_id} failed with exception",
                    worker=worker_name,
                    exception=e,
                    retry_count=job_task.retry_count
                )
        
        finally:
            # Remove from active tasks
            self.active_tasks.pop(job_id, None)

    async def _retry_job(self, job_task: JobTask, error_message: str):
        """Retry a failed job with exponential backoff"""
        job_task.retry_count += 1
        
        # Calculate retry delay with exponential backoff
        delay = self.retry_delay_base ** job_task.retry_count
        retry_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
        job_task.scheduled_at = retry_time
        
        self.status_tracker.retry_job(job_task.job_id)
        
        # Add back to scheduled jobs
        self.scheduled_jobs.append(job_task)
        self.scheduled_jobs.sort(key=lambda x: x.scheduled_at)
        
        logger.info(
            f"Job {job_task.job_id} scheduled for retry {job_task.retry_count}",
            retry_delay=delay,
            retry_time=retry_time,
            error=error_message
        )

    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        result_format: Optional[str] = None
    ):
        """Update job status in the database"""
        try:
            await self.db_ops.update_job_status(
                job_id=job_id,
                status=status.value,
                result=result,
                error_message=error_message,
                result_format=result_format
            )
        except Exception as e:
            logger.error(f"Failed to update job status for {job_id}", exception=e)

    async def _cleanup_worker(self):
        """Periodic cleanup of old job metrics and completed tasks"""
        logger.info("Cleanup worker started")
        
        while not self.is_shutdown:
            try:
                # Clean up old job metrics (keep last 1000)
                if len(self.status_tracker.job_metrics) > 1000:
                    # Sort by end_time and keep newest 1000
                    sorted_jobs = sorted(
                        self.status_tracker.job_metrics.items(),
                        key=lambda x: x[1].get('end_time', datetime.min),
                        reverse=True
                    )
                    
                    # Keep only the newest 1000
                    self.status_tracker.job_metrics = dict(sorted_jobs[:1000])
                    
                    logger.debug("Cleaned up old job metrics")
                
                # Sleep until next cleanup
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error("Cleanup worker error", exception=e)
                await asyncio.sleep(60.0)  # Sleep longer on error

        logger.info("Cleanup worker stopped")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        return {
            'is_running': self.is_running,
            'queue_size': self.job_queue.qsize(),
            'scheduled_jobs': len(self.scheduled_jobs),
            'active_jobs': len(self.active_tasks),
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'worker_count': len(self.worker_tasks),
            'metrics': self.status_tracker.get_metrics()
        }

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        return self.status_tracker.job_metrics.get(job_id)

# Global pipeline instance
_job_pipeline: Optional[JobPipeline] = None

def get_job_pipeline() -> JobPipeline:
    """Get or create the global job pipeline instance"""
    global _job_pipeline
    
    if _job_pipeline is None:
        _job_pipeline = JobPipeline()
    
    return _job_pipeline

async def start_job_pipeline():
    """Start the global job pipeline"""
    pipeline = get_job_pipeline()
    await pipeline.start()

async def stop_job_pipeline():
    """Stop the global job pipeline"""
    global _job_pipeline
    
    if _job_pipeline and _job_pipeline.is_running:
        await _job_pipeline.stop() 