"""
Models package for the AI Agent Platform.

This package contains all Pydantic models used throughout the application,
including schedule models, job models, and API response models.
"""

# Import from parent models module using absolute path
import sys
sys.path.append('..')

# Import models from the parent models.py file 
try:
    # First try relative import from parent
    from ..models import (
        ApiResponse, JobResponse, JobStatus, JobStats, UserInfo, JobDataBase, T,
        JobCreateRequest, JobStatusUpdate, HealthResponse
    )
except ImportError:
    # Fallback to importing from the module file directly
    import importlib.util
    import os
    
    models_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.py')
    spec = importlib.util.spec_from_file_location("models", models_file)
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)
    
    ApiResponse = models_module.ApiResponse
    JobResponse = models_module.JobResponse
    JobStatus = models_module.JobStatus
    JobStats = models_module.JobStats
    UserInfo = models_module.UserInfo
    JobDataBase = models_module.JobDataBase
    T = models_module.T
    JobCreateRequest = models_module.JobCreateRequest
    JobStatusUpdate = models_module.JobStatusUpdate
    HealthResponse = models_module.HealthResponse

# Import schedule models from this package
from .schedule import Schedule, ScheduleStatus

__all__ = [
    "ApiResponse",
    "JobResponse", 
    "JobStatus",
    "JobStats",
    "UserInfo",
    "JobDataBase",
    "T",
    "JobCreateRequest",
    "JobStatusUpdate",
    "HealthResponse",
    "Schedule",
    "ScheduleStatus",
] 