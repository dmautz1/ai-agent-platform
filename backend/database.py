"""
Supabase database client and operations with comprehensive logging.
Provides database connection management and query monitoring.
"""

import os
import uuid
import time
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from config import get_settings
from logging_system import get_database_logger, get_logger, get_performance_logger

# Initialize loggers
db_logger = get_database_logger()
logger = get_logger(__name__)
perf_logger = get_performance_logger()

# Global Supabase client instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance with connection logging.
    
    Returns:
        Supabase client instance
        
    Raises:
        Exception: If unable to connect to database
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            settings = get_settings()
            
            logger.info("Initializing Supabase client connection")
            
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Supabase client", exception=e)
            db_logger.log_connection_error(e)
            raise
    
    return _supabase_client

class DatabaseOperations:
    """Database operations with comprehensive logging and monitoring"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new job in the database.
        
        Args:
            job_data: Job information to insert
            
        Returns:
            Created job data
            
        Raises:
            Exception: If job creation fails
        """
        start_time = time.time()
        
        try:
            logger.info("Creating new job", job_type=job_data.get("type"), user_id=job_data.get("user_id"))
            
            with perf_logger.time_operation("db_create_job"):
                response = self.client.table("jobs").insert(job_data).execute()
            
            duration = time.time() - start_time
            
            if response.data:
                created_job = response.data[0]
                logger.info("Job created successfully", job_id=created_job["id"], user_id=job_data.get("user_id"))
                db_logger.log_query("INSERT", "jobs", duration, rows_affected=1)
                return created_job
            else:
                error_msg = "No data returned from job creation"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job creation failed", exception=e, job_data=job_data)
            db_logger.log_query("INSERT", "jobs", duration, error=str(e))
            raise
    
    async def get_job(self, job_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a job by ID with optional user filtering.
        
        Args:
            job_id: ID of the job to retrieve
            user_id: Optional user ID for access control
            
        Returns:
            Job data if found, None otherwise
        """
        start_time = time.time()
        
        try:
            logger.debug("Retrieving job", job_id=job_id, user_id=user_id)
            
            with perf_logger.time_operation("db_get_job", job_id=job_id):
                query = self.client.table("jobs").select("*").eq("id", job_id)
                
                if user_id:
                    query = query.eq("user_id", user_id)
                
                response = query.execute()
            
            duration = time.time() - start_time
            
            if response.data:
                job = response.data[0]
                logger.debug("Job retrieved successfully", job_id=job_id)
                db_logger.log_query("SELECT", "jobs", duration, rows_returned=1)
                return job
            else:
                logger.debug("Job not found", job_id=job_id, user_id=user_id)
                db_logger.log_query("SELECT", "jobs", duration, rows_returned=0)
                return None
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job retrieval failed", exception=e, job_id=job_id)
            db_logger.log_query("SELECT", "jobs", duration, error=str(e))
            raise
    
    async def get_user_jobs(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve jobs for a specific user with pagination.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of job data
        """
        start_time = time.time()
        
        try:
            logger.debug("Retrieving user jobs", user_id=user_id, limit=limit, offset=offset)
            
            with perf_logger.time_operation("db_get_user_jobs", user_id=user_id):
                response = (
                    self.client.table("jobs")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
            
            duration = time.time() - start_time
            
            jobs = response.data or []
            logger.debug("User jobs retrieved", user_id=user_id, count=len(jobs))
            db_logger.log_query("SELECT", "jobs", duration, rows_returned=len(jobs))
            
            return jobs
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("User jobs retrieval failed", exception=e, user_id=user_id)
            db_logger.log_query("SELECT", "jobs", duration, error=str(e))
            raise
    
    async def update_job_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Update job status and optionally set result or error.
        
        Args:
            job_id: ID of the job to update
            status: New status for the job
            result: Optional result data for completed jobs
            error_message: Optional error message for failed jobs
            
        Returns:
            Updated job data
        """
        start_time = time.time()
        
        try:
            logger.info("Updating job status", job_id=job_id, status=status)
            
            update_data = {
                "status": status,
                "updated_at": "now()"
            }
            
            if result is not None:
                update_data["result"] = result
                update_data["completed_at"] = "now()"
            
            if error_message is not None:
                update_data["error_message"] = error_message
                update_data["failed_at"] = "now()"
            
            with perf_logger.time_operation("db_update_job_status", job_id=job_id):
                response = (
                    self.client.table("jobs")
                    .update(update_data)
                    .eq("id", job_id)
                    .execute()
                )
            
            duration = time.time() - start_time
            
            if response.data:
                updated_job = response.data[0]
                logger.info("Job status updated successfully", job_id=job_id, status=status)
                db_logger.log_query("UPDATE", "jobs", duration, rows_affected=1)
                return updated_job
            else:
                error_msg = f"Job {job_id} not found for status update"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job status update failed", exception=e, job_id=job_id, status=status)
            db_logger.log_query("UPDATE", "jobs", duration, error=str(e))
            raise
    
    async def delete_job(self, job_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a job by ID with optional user filtering.
        
        Args:
            job_id: ID of the job to delete
            user_id: Optional user ID for access control
            
        Returns:
            True if job was deleted, False if not found
        """
        start_time = time.time()
        
        try:
            logger.info("Deleting job", job_id=job_id, user_id=user_id)
            
            with perf_logger.time_operation("db_delete_job", job_id=job_id):
                query = self.client.table("jobs").delete().eq("id", job_id)
                
                if user_id:
                    query = query.eq("user_id", user_id)
                
                response = query.execute()
            
            duration = time.time() - start_time
            
            deleted_count = len(response.data) if response.data else 0
            
            if deleted_count > 0:
                logger.info("Job deleted successfully", job_id=job_id)
                db_logger.log_query("DELETE", "jobs", duration, rows_affected=deleted_count)
                return True
            else:
                logger.warning("Job not found for deletion", job_id=job_id, user_id=user_id)
                db_logger.log_query("DELETE", "jobs", duration, rows_affected=0)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job deletion failed", exception=e, job_id=job_id)
            db_logger.log_query("DELETE", "jobs", duration, error=str(e))
            raise
    
    async def get_job_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get job statistics, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter statistics
            
        Returns:
            Dictionary containing job statistics
        """
        start_time = time.time()
        
        try:
            logger.debug("Retrieving job statistics", user_id=user_id)
            
            with perf_logger.time_operation("db_get_job_stats", user_id=user_id):
                # Get total jobs count
                query = self.client.table("jobs").select("status", count="exact")
                if user_id:
                    query = query.eq("user_id", user_id)
                
                response = query.execute()
                
                # Count jobs by status
                status_counts = {}
                for job in response.data:
                    status = job["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            duration = time.time() - start_time
            
            total_jobs = len(response.data)
            statistics = {
                "total_jobs": total_jobs,
                "pending_jobs": status_counts.get("pending", 0),
                "running_jobs": status_counts.get("running", 0),
                "completed_jobs": status_counts.get("completed", 0),
                "failed_jobs": status_counts.get("failed", 0),
                "status_breakdown": status_counts
            }
            
            logger.debug("Job statistics retrieved", user_id=user_id, total_jobs=total_jobs)
            db_logger.log_query("SELECT", "jobs", duration, rows_returned=total_jobs)
            
            return statistics
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job statistics retrieval failed", exception=e, user_id=user_id)
            db_logger.log_query("SELECT", "jobs", duration, error=str(e))
            raise
    
    async def cleanup_old_jobs(self, older_than_days: int = 30) -> int:
        """
        Clean up old completed jobs to manage database size.
        
        Args:
            older_than_days: Delete jobs completed more than this many days ago
            
        Returns:
            Number of jobs deleted
        """
        start_time = time.time()
        
        try:
            logger.info("Starting job cleanup", older_than_days=older_than_days)
            
            with perf_logger.time_operation("db_cleanup_jobs"):
                # Delete completed jobs older than specified days
                cutoff_date = f"NOW() - INTERVAL '{older_than_days} days'"
                
                response = (
                    self.client.table("jobs")
                    .delete()
                    .eq("status", "completed")
                    .lt("completed_at", cutoff_date)
                    .execute()
                )
            
            duration = time.time() - start_time
            
            deleted_count = len(response.data) if response.data else 0
            logger.info("Job cleanup completed", deleted_count=deleted_count, older_than_days=older_than_days)
            db_logger.log_query("DELETE", "jobs", duration, rows_affected=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("Job cleanup failed", exception=e, older_than_days=older_than_days)
            db_logger.log_query("DELETE", "jobs", duration, error=str(e))
            raise

# Global database operations instance
_db_operations: Optional[DatabaseOperations] = None

def get_database_operations() -> DatabaseOperations:
    """
    Get or create database operations instance.
    
    Returns:
        DatabaseOperations instance
    """
    global _db_operations
    if _db_operations is None:
        _db_operations = DatabaseOperations()
    return _db_operations

# Health check function
async def check_database_health() -> Dict[str, Any]:
    """
    Check database connection health.
    
    Returns:
        Dictionary containing health status and metrics
    """
    start_time = time.time()
    
    try:
        logger.debug("Checking database health")
        
        with perf_logger.time_operation("db_health_check"):
            # Simple query to test connection
            client = get_supabase_client()
            response = client.table("jobs").select("id", count="exact").limit(1).execute()
        
        duration = time.time() - start_time
        
        health_status = {
            "status": "healthy",
            "connection_time_ms": round(duration * 1000, 2),
            "timestamp": time.time()
        }
        
        logger.debug("Database health check passed", connection_time_ms=health_status["connection_time_ms"])
        db_logger.log_query("SELECT", "jobs", duration, rows_returned=1)
        
        return health_status
        
    except Exception as e:
        duration = time.time() - start_time
        
        health_status = {
            "status": "unhealthy",
            "error": str(e),
            "connection_time_ms": round(duration * 1000, 2),
            "timestamp": time.time()
        }
        
        logger.error("Database health check failed", exception=e)
        db_logger.log_connection_error(e)
        
        return health_status

# Create global database client instance
_db_client: Optional[DatabaseClient] = None

def get_database_client() -> DatabaseClient:
    """Get or create database client instance"""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client 