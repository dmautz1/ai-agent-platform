"""
Schedule management API endpoints for the AI Agent Platform.

Provides CRUD operations for schedules with:
- Schedule creation, retrieval, updating, and deletion
- Enable/disable schedule functionality
- Upcoming scheduled jobs retrieval
- Individual schedule job history
- Statistics and analytics
- Proper error handling and validation
- Row-level security integration

Follows the established ApiResponse pattern and integrates with 
the existing authentication and database systems.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone, timedelta
import uuid
import logging
from supabase import Client

# Import models and dependencies
from models.schedule import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleStats, 
    ScheduleExecutionHistory, ScheduleStatus
)
from models import ApiResponse
from database import get_supabase_client
from auth import get_current_user
from utils.cron_utils import CronUtils, CronValidationError
from utils.responses import (
    create_success_response,
    create_error_response,
    create_validation_error_response,
    api_response_validator
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/schedules", tags=["schedules"])

# Type aliases for API responses
ScheduleListResponse = List[Schedule]
ScheduleResponse = Schedule
ScheduleCreateResponse = Schedule
ScheduleUpdateResponse = Schedule
ScheduleStatsResponse = ScheduleStats
ScheduleHistoryResponse = List[ScheduleExecutionHistory]
UpcomingJobsResponse = List[Dict[str, Any]]

@router.post("/", response_model=ApiResponse[ScheduleCreateResponse])
@api_response_validator(result_type=ScheduleCreateResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new schedule.
    
    Creates a new schedule with the provided configuration and calculates
    the next run time. The schedule is created in enabled state by default.
    
    Args:
        schedule_data: Schedule creation data with agent configuration
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Schedule]: Created schedule with calculated next run time
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Generate unique ID
        schedule_id = str(uuid.uuid4())
        user_id = user.get("id")
        
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "create_schedule"
                }
            )
        
        # Calculate next run time
        try:
            next_run = schedule_data.get_next_run_time()
        except ValueError as e:
            return create_error_response(
                error_message=f"Invalid cron expression: {str(e)}",
                message="Schedule validation failed",
                metadata={
                    "error_code": "CRON_VALIDATION_ERROR",
                    "endpoint": "create_schedule"
                }
            )
        
        # Prepare schedule data for database
        current_time = datetime.now(timezone.utc)
        schedule_db_data = {
            "id": schedule_id,
            "user_id": user_id,
            "title": schedule_data.title,
            "description": schedule_data.description,
            "agent_name": schedule_data.agent_name,
            "cron_expression": schedule_data.cron_expression,
            "enabled": schedule_data.enabled,
            "timezone": schedule_data.timezone,
            "agent_config_data": schedule_data.agent_config_data.model_dump(),
            "next_run": next_run.isoformat(),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        # Insert into database
        result = supabase.table("schedules").insert(schedule_db_data).execute()
        
        if not result.data or len(result.data) == 0:
            return create_error_response(
                error_message="Failed to create schedule",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "endpoint": "create_schedule"
                }
            )
        
        # Convert to response model
        schedule_record = result.data[0]
        schedule_response = Schedule(
            id=schedule_record["id"],
            user_id=schedule_record["user_id"],
            title=schedule_record["title"],
            description=schedule_record["description"],
            agent_name=schedule_record["agent_name"],
            cron_expression=schedule_record["cron_expression"],
            enabled=schedule_record["enabled"],
            timezone=schedule_record.get("timezone"),
            agent_config_data=schedule_data.agent_config_data,
            status=ScheduleStatus.enabled if schedule_record["enabled"] else ScheduleStatus.disabled,
            next_run=datetime.fromisoformat(schedule_record["next_run"].replace('Z', '+00:00')),
            created_at=datetime.fromisoformat(schedule_record["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(schedule_record["updated_at"].replace('Z', '+00:00')),
            total_executions=0,
            successful_executions=0,
            failed_executions=0
        )
        
        logger.info(f"Created schedule {schedule_id} for user {user_id}")
        
        return create_success_response(
            result=schedule_response,
            message=f"Schedule '{schedule_data.title}' created successfully",
            metadata={
                "schedule_id": schedule_id,
                "next_run": next_run.isoformat(),
                "cron_description": schedule_data.get_cron_description(),
                "endpoint": "create_schedule"
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        return create_error_response(
            error_message="Internal server error creating schedule",
            message="Schedule creation failed",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "endpoint": "create_schedule"
            }
        )

@router.get("/", response_model=ApiResponse[ScheduleListResponse])
@api_response_validator(result_type=ScheduleListResponse)
async def list_schedules(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of schedules to return"),
    offset: int = Query(0, ge=0, description="Number of schedules to skip"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List user's schedules with optional filtering.
    
    Retrieves all schedules for the current user with optional filtering
    by enabled status and agent name. Results are paginated.
    
    Args:
        enabled: Filter by enabled status (optional)
        agent_name: Filter by agent name (optional)
        limit: Maximum number of results to return
        offset: Number of results to skip (pagination)
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[List[Schedule]]: List of schedules matching criteria
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "list_schedules"
                }
            )
        
        # Build query with user filter
        query = supabase.table("schedules").select("*").eq("user_id", user_id)
        
        # Apply optional filters
        if enabled is not None:
            query = query.eq("enabled", enabled)
        
        if agent_name:
            query = query.eq("agent_name", agent_name)
        
        # Apply ordering and pagination
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Convert to response models
        schedules = []
        for record in result.data:
            # Get execution statistics
            stats_result = supabase.table("schedule_job_stats").select("*").eq("schedule_id", record["id"]).execute()
            stats = stats_result.data[0] if stats_result.data else {}
            
            schedule = Schedule(
                id=record["id"],
                user_id=record["user_id"],
                title=record["title"],
                description=record["description"],
                agent_name=record["agent_name"],
                cron_expression=record["cron_expression"],
                enabled=record["enabled"],
                timezone=record.get("timezone"),
                agent_config_data=record["agent_config_data"],
                status=ScheduleStatus.enabled if record["enabled"] else ScheduleStatus.disabled,
                next_run=datetime.fromisoformat(record["next_run"].replace('Z', '+00:00')) if record["next_run"] else None,
                last_run=datetime.fromisoformat(record["last_run"].replace('Z', '+00:00')) if record.get("last_run") else None,
                created_at=datetime.fromisoformat(record["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(record["updated_at"].replace('Z', '+00:00')),
                total_executions=stats.get("total_jobs", 0),
                successful_executions=stats.get("completed_jobs", 0),
                failed_executions=stats.get("failed_jobs", 0)
            )
            schedules.append(schedule)
        
        logger.info(f"Retrieved {len(schedules)} schedules for user {user_id}")
        
        return create_success_response(
            result=schedules,
            message=f"Retrieved {len(schedules)} schedules",
            metadata={
                "count": len(schedules),
                "total_count": len(schedules),
                "enabled_count": len([s for s in schedules if s.enabled]),
                "disabled_count": len([s for s in schedules if not s.enabled]),
                "filters": {
                    "enabled": enabled,
                    "agent_name": agent_name
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                },
                "endpoint": "list_schedules"
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        
        # Check if it's a database/table error
        error_str = str(e).lower()
        if "relation" in error_str and "does not exist" in error_str:
            # Schedules table doesn't exist
            return create_error_response(
                error_message="Database schema not initialized",
                message="Schedules table not found. Please run database migrations first.",
                metadata={
                    "database_error": True,
                    "setup_required": True,
                    "endpoint": "list_schedules"
                }
            )
        elif "column" in error_str and "does not exist" in error_str:
            # Missing columns in schedules table
            return create_error_response(
                error_message="Database schema outdated",
                message="Schedules table schema is incomplete. Please run database migrations.",
                metadata={
                    "database_error": True,
                    "migration_required": True,
                    "endpoint": "list_schedules"
                }
            )
        
        # Generic error
        return create_error_response(
            error_message="Internal server error listing schedules",
            message="Failed to retrieve schedules",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "endpoint": "list_schedules"
            }
        )

@router.get("/upcoming", response_model=ApiResponse[UpcomingJobsResponse])
@api_response_validator(result_type=UpcomingJobsResponse)
async def get_upcoming_schedules(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of upcoming jobs to return"),
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours ahead to look for upcoming jobs"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get upcoming scheduled jobs for dashboard display.
    
    Retrieves the next scheduled executions across all enabled schedules
    for the current user within the specified time window.
    
    Args:
        limit: Maximum number of upcoming jobs to return
        hours_ahead: Hours ahead to look for upcoming jobs
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[List[Dict]]: List of upcoming scheduled executions
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "get_upcoming_schedules"
                }
            )
        
        # Calculate time window
        current_time = datetime.now(timezone.utc)
        end_time = current_time + timedelta(hours=hours_ahead)
        
        # Get enabled schedules with next_run within the time window
        result = supabase.table("schedules").select(
            "id, title, description, agent_name, cron_expression, enabled, next_run"
        ).eq("user_id", user_id).eq("enabled", True).not_.is_(
            "next_run", "null"
        ).lte("next_run", end_time.isoformat()).order(
            "next_run", desc=False
        ).limit(limit).execute()
        
        # Format upcoming jobs
        upcoming_jobs = []
        for record in result.data:
            try:
                next_run = datetime.fromisoformat(record["next_run"].replace('Z', '+00:00'))
                
                # Get cron description
                try:
                    cron_description = CronUtils.describe_cron_expression(record["cron_expression"])
                except:
                    cron_description = f"Cron: {record['cron_expression']}"
                
                upcoming_job = {
                    "id": record["id"],
                    "schedule_id": record["id"],
                    "title": record["title"],
                    "description": record.get("description"),
                    "agent_name": record["agent_name"],
                    "cron_expression": record["cron_expression"],
                    "enabled": record["enabled"],
                    "next_run": next_run.isoformat(),
                    "time_until_run": (next_run - current_time).total_seconds(),
                    "cron_description": cron_description,
                    "is_overdue": next_run < current_time
                }
                upcoming_jobs.append(upcoming_job)
            except Exception as e:
                logger.warning(f"Error processing upcoming job for schedule {record['id']}: {e}")
                continue
        
        logger.info(f"Retrieved {len(upcoming_jobs)} upcoming jobs for user {user_id}")
        
        return create_success_response(
            result=upcoming_jobs,
            message=f"Retrieved {len(upcoming_jobs)} upcoming jobs",
            metadata={
                "count": len(upcoming_jobs),
                "time_window_hours": hours_ahead,
                "current_time": current_time.isoformat(),
                "end_time": end_time.isoformat(),
                "endpoint": "get_upcoming_schedules"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving upcoming jobs: {e}")
        
        # Check if it's a database/table error
        error_str = str(e).lower()
        if "relation" in error_str and "does not exist" in error_str:
            # Schedules table doesn't exist
            return create_error_response(
                error_message="Database schema not initialized",
                message="Schedules table not found. Please run database migrations first.",
                metadata={
                    "database_error": True,
                    "setup_required": True,
                    "endpoint": "get_upcoming_schedules"
                }
            )
        elif "column" in error_str and "does not exist" in error_str:
            # Missing columns in schedules table
            return create_error_response(
                error_message="Database schema outdated",
                message="Schedules table schema is incomplete. Please run database migrations.",
                metadata={
                    "database_error": True,
                    "migration_required": True,
                    "endpoint": "get_upcoming_schedules"
                }
            )
        
        # Generic error
        return create_error_response(
            error_message="Internal server error retrieving upcoming jobs",
            message="Failed to retrieve upcoming jobs",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "endpoint": "get_upcoming_schedules"
            }
        )

@router.get("/upcoming-jobs", response_model=ApiResponse[UpcomingJobsResponse])
@api_response_validator(result_type=UpcomingJobsResponse)
async def get_upcoming_jobs(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of upcoming jobs to return"),
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours ahead to look for upcoming jobs"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get upcoming scheduled jobs for dashboard display (alternative endpoint).
    
    This is an alias for the /upcoming endpoint to maintain backward compatibility.
    Retrieves the next scheduled executions across all enabled schedules
    for the current user within the specified time window.
    
    Args:
        limit: Maximum number of upcoming jobs to return
        hours_ahead: Hours ahead to look for upcoming jobs
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[List[Dict]]: List of upcoming scheduled executions
    """
    # Delegate to the main upcoming function
    return await get_upcoming_schedules(limit, hours_ahead, user, supabase)

@router.get("/{schedule_id}", response_model=ApiResponse[ScheduleResponse])
@api_response_validator(result_type=ScheduleResponse)
async def get_schedule(
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a specific schedule by ID.
    
    Retrieves detailed information about a specific schedule including
    execution statistics and next run time.
    
    Args:
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Schedule]: Schedule details with statistics
        
    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "get_schedule"
                }
            )
        
        # Get schedule
        result = supabase.table("schedules").select("*").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "get_schedule"
                }
            )
        
        record = result.data[0]
        
        # Get execution statistics
        stats_result = supabase.table("schedule_job_stats").select("*").eq("schedule_id", schedule_id).execute()
        stats = stats_result.data[0] if stats_result.data else {}
        
        # Create response model
        schedule = Schedule(
            id=record["id"],
            user_id=record["user_id"],
            title=record["title"],
            description=record["description"],
            agent_name=record["agent_name"],
            cron_expression=record["cron_expression"],
            enabled=record["enabled"],
            timezone=record.get("timezone"),
            agent_config_data=record["agent_config_data"],
            status=ScheduleStatus.enabled if record["enabled"] else ScheduleStatus.disabled,
            next_run=datetime.fromisoformat(record["next_run"].replace('Z', '+00:00')) if record["next_run"] else None,
            last_run=datetime.fromisoformat(record["last_run"].replace('Z', '+00:00')) if record.get("last_run") else None,
            created_at=datetime.fromisoformat(record["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(record["updated_at"].replace('Z', '+00:00')),
            total_executions=stats.get("total_jobs", 0),
            successful_executions=stats.get("completed_jobs", 0),
            failed_executions=stats.get("failed_jobs", 0)
        )
        
        logger.info(f"Retrieved schedule {schedule_id} for user {user_id}")
        
        return create_success_response(
            result=schedule,
            message=f"Retrieved schedule '{schedule.title}'",
            metadata={
                "schedule_id": schedule_id,
                "cron_description": schedule.get_cron_description(),
                "success_rate": schedule.success_rate,
                "endpoint": "get_schedule"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving schedule {schedule_id}: {e}")
        return create_error_response(
            error_message=f"Internal server error retrieving schedule",
            message="Failed to retrieve schedule",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "get_schedule"
            }
        )

@router.put("/{schedule_id}", response_model=ApiResponse[ScheduleUpdateResponse])
@api_response_validator(result_type=ScheduleUpdateResponse)
async def update_schedule(
    update_data: ScheduleUpdate,
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update an existing schedule.
    
    Updates schedule properties and recalculates next run time if 
    cron expression is changed.
    
    Args:
        update_data: Schedule update data
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Schedule]: Updated schedule
        
    Raises:
        HTTPException: If schedule not found, access denied, or validation fails
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "update_schedule"
                }
            )
        
        # Check if schedule exists and belongs to user
        existing_result = supabase.table("schedules").select("*").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not existing_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "update_schedule"
                }
            )
        
        existing_schedule = existing_result.data[0]
        
        # Build update data
        update_dict = {}
        recalculate_next_run = False
        
        # Update fields that are provided
        if update_data.title is not None:
            update_dict["title"] = update_data.title
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.cron_expression is not None:
            update_dict["cron_expression"] = update_data.cron_expression
            recalculate_next_run = True
        if update_data.enabled is not None:
            update_dict["enabled"] = update_data.enabled
            recalculate_next_run = True
        if update_data.timezone is not None:
            update_dict["timezone"] = update_data.timezone
            recalculate_next_run = True
        if update_data.agent_config_data is not None:
            update_dict["agent_config_data"] = update_data.agent_config_data.model_dump()
        
        # Recalculate next run time if needed
        if recalculate_next_run:
            cron_expr = update_data.cron_expression or existing_schedule["cron_expression"]
            enabled = update_data.enabled if update_data.enabled is not None else existing_schedule["enabled"]
            timezone_str = update_data.timezone if update_data.timezone is not None else existing_schedule.get("timezone")
            
            if enabled:
                try:
                    next_run = CronUtils.get_next_run_time(cron_expr, timezone_str=timezone_str)
                    update_dict["next_run"] = next_run.isoformat()
                except CronValidationError as e:
                    return create_error_response(
                        error_message=f"Invalid cron expression: {str(e)}",
                        message="Schedule validation failed",
                        metadata={
                            "error_code": "CRON_VALIDATION_ERROR",
                            "schedule_id": schedule_id,
                            "endpoint": "update_schedule"
                        }
                    )
            else:
                update_dict["next_run"] = None
        
        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Perform update
        result = supabase.table("schedules").update(update_dict).eq("id", schedule_id).execute()
        
        if not result.data:
            return create_error_response(
                error_message="Failed to update schedule",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "update_schedule"
                }
            )
        
        # Get updated schedule with statistics
        return await get_schedule(schedule_id, user, supabase)
        
    except Exception as e:
        logger.error(f"Error updating schedule {schedule_id}: {e}")
        return create_error_response(
            error_message="Internal server error updating schedule",
            message="Failed to update schedule",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "update_schedule"
            }
        )

@router.delete("/{schedule_id}", response_model=ApiResponse[Dict[str, str]])
@api_response_validator(result_type=Dict[str, str])
async def delete_schedule(
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a schedule.
    
    Permanently deletes a schedule and all associated data.
    This operation cannot be undone.
    
    Args:
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Dict[str, str]]: Deletion confirmation
        
    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "delete_schedule"
                }
            )
        
        # Check if schedule exists and belongs to user
        existing_result = supabase.table("schedules").select("id, title").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not existing_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "delete_schedule"
                }
            )
        
        schedule_title = existing_result.data[0]["title"]
        
        # Delete the schedule (cascade will handle related jobs via foreign key constraints)
        result = supabase.table("schedules").delete().eq("id", schedule_id).execute()
        
        if not result.data:
            return create_error_response(
                error_message="Failed to delete schedule",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "delete_schedule"
                }
            )
        
        logger.info(f"Deleted schedule {schedule_id} for user {user_id}")
        
        return create_success_response(
            result={"schedule_id": schedule_id, "title": schedule_title},
            message=f"Schedule '{schedule_title}' deleted successfully",
            metadata={
                "schedule_id": schedule_id,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "endpoint": "delete_schedule"
            }
        )
        
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {e}")
        return create_error_response(
            error_message="Internal server error deleting schedule",
            message="Failed to delete schedule",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "delete_schedule"
            }
        )

# Additional endpoints for Tasks 2.2-2.4

@router.post("/{schedule_id}/enable", response_model=ApiResponse[ScheduleResponse])
@api_response_validator(result_type=ScheduleResponse)
async def enable_schedule(
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Enable a schedule.
    
    Enables a disabled schedule and calculates the next run time.
    
    Args:
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Schedule]: Updated schedule with next run time
        
    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "enable_schedule"
                }
            )
        
        # Check if schedule exists and belongs to user
        existing_result = supabase.table("schedules").select("*").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not existing_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "enable_schedule"
                }
            )
        
        existing_schedule = existing_result.data[0]
        
        if existing_schedule["enabled"]:
            return create_error_response(
                error_message="Schedule is already enabled",
                message="Schedule is already in enabled state",
                metadata={
                    "error_code": "SCHEDULE_ALREADY_ENABLED",
                    "schedule_id": schedule_id,
                    "endpoint": "enable_schedule"
                }
            )
        
        # Calculate next run time
        try:
            # Use the schedule's timezone if available
            schedule_timezone = existing_schedule.get("timezone")
            next_run = CronUtils.get_next_run_time(existing_schedule["cron_expression"], timezone_str=schedule_timezone)
        except CronValidationError as e:
            return create_error_response(
                error_message=f"Invalid cron expression: {str(e)}",
                message="Schedule validation failed",
                metadata={
                    "error_code": "CRON_VALIDATION_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "enable_schedule"
                }
            )
        
        # Update schedule
        update_data = {
            "enabled": True,
            "next_run": next_run.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("schedules").update(update_data).eq("id", schedule_id).execute()
        
        if not result.data:
            return create_error_response(
                error_message="Failed to enable schedule",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "enable_schedule"
                }
            )
        
        logger.info(f"Enabled schedule {schedule_id} for user {user_id}")
        
        # Return updated schedule
        return await get_schedule(schedule_id, user, supabase)
        
    except Exception as e:
        logger.error(f"Error enabling schedule {schedule_id}: {e}")
        return create_error_response(
            error_message="Internal server error enabling schedule",
            message="Failed to enable schedule",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "enable_schedule"
            }
        )

@router.post("/{schedule_id}/disable", response_model=ApiResponse[ScheduleResponse])
@api_response_validator(result_type=ScheduleResponse)
async def disable_schedule(
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Disable a schedule.
    
    Disables an enabled schedule and clears the next run time.
    
    Args:
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Schedule]: Updated schedule with cleared next run time
        
    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "disable_schedule"
                }
            )
        
        # Check if schedule exists and belongs to user
        existing_result = supabase.table("schedules").select("*").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not existing_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "disable_schedule"
                }
            )
        
        existing_schedule = existing_result.data[0]
        
        if not existing_schedule["enabled"]:
            return create_error_response(
                error_message="Schedule is already disabled",
                message="Schedule is already in disabled state",
                metadata={
                    "error_code": "SCHEDULE_ALREADY_DISABLED",
                    "schedule_id": schedule_id,
                    "endpoint": "disable_schedule"
                }
            )
        
        # Update schedule
        update_data = {
            "enabled": False,
            "next_run": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("schedules").update(update_data).eq("id", schedule_id).execute()
        
        if not result.data:
            return create_error_response(
                error_message="Failed to disable schedule",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "disable_schedule"
                }
            )
        
        logger.info(f"Disabled schedule {schedule_id} for user {user_id}")
        
        # Return updated schedule
        return await get_schedule(schedule_id, user, supabase)
        
    except Exception as e:
        logger.error(f"Error disabling schedule {schedule_id}: {e}")
        return create_error_response(
            error_message="Internal server error disabling schedule",
            message="Failed to disable schedule",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "disable_schedule"
            }
        )

@router.post("/{schedule_id}/run-now", response_model=ApiResponse[Dict[str, Any]])
@api_response_validator(result_type=Dict[str, Any])
async def run_schedule_now(
    schedule_id: str = Path(..., description="Schedule ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Run a schedule immediately.
    
    Creates a new job using the schedule's configuration and submits it
    for immediate execution, bypassing the normal schedule timing.
    
    Args:
        schedule_id: Unique schedule identifier
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[Dict]: Created job information
        
    Raises:
        HTTPException: If schedule not found or job creation fails
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "run_schedule_now"
                }
            )
        
        # Check if schedule exists and belongs to user
        existing_result = supabase.table("schedules").select("*").eq("id", schedule_id).eq("user_id", user_id).execute()
        
        if not existing_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "run_schedule_now"
                }
            )
        
        schedule = existing_result.data[0]
        agent_config = schedule["agent_config_data"]
        
        # Extract job data from agent configuration
        job_data = agent_config.get("job_data", {})
        agent_name = schedule["agent_name"]
        schedule_title = schedule["title"]
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        # Prepare job data for database
        job_db_data = {
            "id": job_id,
            "user_id": user_id,
            "agent_identifier": agent_name,
            "title": f"{schedule_title} (Manual Run)",
            "status": "pending",
            "priority": 5,
            "tags": ["manual", "schedule-triggered"],
            "data": job_data,
            "schedule_id": schedule_id,
            "execution_source": "manual",
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        # Insert job into database
        job_result = supabase.table("jobs").insert(job_db_data).execute()
        
        if not job_result.data or len(job_result.data) == 0:
            return create_error_response(
                error_message="Failed to create job",
                message="Database operation failed",
                metadata={
                    "error_code": "DATABASE_ERROR",
                    "schedule_id": schedule_id,
                    "endpoint": "run_schedule_now"
                }
            )
        
        created_job = job_result.data[0]
        
        # Submit job to pipeline for processing
        from job_pipeline import get_job_pipeline
        
        pipeline_submitted = False
        pipeline = get_job_pipeline()
        if pipeline and pipeline.is_running:
            try:
                pipeline_submitted = await pipeline.submit_job(
                    job_id=job_id,
                    user_id=user_id,
                    agent_name=agent_name,
                    job_data=job_data,
                    priority=5,
                    tags=["manual", "schedule-triggered"]
                )
                
                if pipeline_submitted:
                    logger.info(f"Manual job {job_id} submitted to pipeline for immediate execution")
                else:
                    logger.warning(f"Manual job {job_id} created but failed to submit to pipeline")
            except Exception as e:
                logger.warning(f"Failed to submit manual job {job_id} to pipeline: {e}")
        else:
            logger.warning(f"Manual job {job_id} created but pipeline not running")
        
        logger.info(f"Created manual job {job_id} from schedule {schedule_id} for user {user_id}")
        
        return create_success_response(
            result={
                "job_id": job_id,
                "schedule_id": schedule_id,
                "title": created_job["title"],
                "status": created_job["status"],
                "agent_identifier": agent_name,
                "created_at": created_job["created_at"],
                "execution_source": "manual",
                "pipeline_submitted": pipeline_submitted
            },
            message=f"Job '{created_job['title']}' created and {'queued for immediate execution' if pipeline_submitted else 'saved (pipeline not available)'}",
            metadata={
                "job_id": job_id,
                "schedule_id": schedule_id,
                "schedule_title": schedule_title,
                "agent_name": agent_name,
                "pipeline_submitted": pipeline_submitted,
                "endpoint": "run_schedule_now"
            }
        )
        
    except Exception as e:
        logger.error(f"Error running schedule {schedule_id} immediately: {e}")
        return create_error_response(
            error_message="Internal server error creating immediate job",
            message="Failed to run schedule immediately",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "run_schedule_now"
            }
        )

@router.get("/{schedule_id}/history", response_model=ApiResponse[ScheduleHistoryResponse])
@api_response_validator(result_type=ScheduleHistoryResponse)
async def get_schedule_history(
    schedule_id: str = Path(..., description="Schedule ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of history records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get execution history for a specific schedule.
    
    Retrieves the job execution history for a schedule with optional
    filtering by status and pagination.
    
    Args:
        schedule_id: Unique schedule identifier
        limit: Maximum number of history records to return
        offset: Number of records to skip for pagination
        status: Filter by job status (optional)
        user: Current authenticated user
        supabase: Supabase client instance
        
    Returns:
        ApiResponse[List[ScheduleExecutionHistory]]: Schedule execution history
        
    Raises:
        HTTPException: If schedule not found or access denied
    """
    try:
        user_id = user.get("id")
        if not user_id:
            return create_error_response(
                error_message="User ID not found",
                message="Authentication failed",
                metadata={
                    "error_code": "AUTH_ERROR",
                    "endpoint": "get_schedule_history"
                }
            )
        
        # Verify schedule exists and belongs to user
        schedule_result = supabase.table("schedules").select("id, title").eq(
            "id", schedule_id
        ).eq("user_id", user_id).execute()
        
        if not schedule_result.data:
            return create_error_response(
                error_message="Schedule not found",
                message="The requested schedule could not be found",
                metadata={
                    "error_code": "SCHEDULE_NOT_FOUND",
                    "schedule_id": schedule_id,
                    "endpoint": "get_schedule_history"
                }
            )
        
        schedule_title = schedule_result.data[0]["title"]
        
        # Build jobs query
        query = supabase.table("jobs").select(
            "id, status, created_at, completed_at, failed_at, updated_at, result, error_message"
        ).eq("schedule_id", schedule_id)
        
        # Apply status filter
        if status:
            query = query.eq("status", status)
        
        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Convert to history records
        history = []
        for job in result.data:
            # Calculate duration
            duration_seconds = None
            if job["status"] == "completed" and job["completed_at"]:
                start_time = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(job["completed_at"].replace('Z', '+00:00'))
                duration_seconds = (end_time - start_time).total_seconds()
            elif job["status"] == "failed" and job["failed_at"]:
                start_time = datetime.fromisoformat(job["created_at"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(job["failed_at"].replace('Z', '+00:00'))
                duration_seconds = (end_time - start_time).total_seconds()
            
            # Create result preview
            result_preview = None
            if job["result"]:
                result_text = str(job["result"])
                if len(result_text) > 500:
                    result_preview = result_text[:497] + "..."  # 497 + 3 = 500 characters total
                else:
                    result_preview = result_text
            
            history_record = ScheduleExecutionHistory(
                schedule_id=schedule_id,
                job_id=job["id"],
                execution_time=datetime.fromisoformat(job["created_at"].replace('Z', '+00:00')),
                status=job["status"],
                duration_seconds=duration_seconds,
                error_message=job["error_message"],
                result_preview=result_preview
            )
            history.append(history_record)
        
        logger.info(f"Retrieved {len(history)} history records for schedule {schedule_id}")
        
        return create_success_response(
            result=history,
            message=f"Retrieved {len(history)} execution records for '{schedule_title}'",
            metadata={
                "schedule_id": schedule_id,
                "schedule_title": schedule_title,
                "count": len(history),
                "limit": limit,
                "offset": offset,
                "status_filter": status,
                "endpoint": "get_schedule_history"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving history for schedule {schedule_id}: {e}")
        return create_error_response(
            error_message="Internal server error retrieving schedule history",
            message="Failed to retrieve schedule history",
            metadata={
                "error_code": "INTERNAL_ERROR",
                "schedule_id": schedule_id,
                "endpoint": "get_schedule_history"
            }
        ) 