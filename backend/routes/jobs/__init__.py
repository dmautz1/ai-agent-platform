"""
Jobs routes module - Modular job management endpoints.

Combines multiple specialized routers for better organization:
- creation: Job creation and validation
- management: Job CRUD operations
- operations: Job retry, rerun, delete operations
- monitoring: Status, logs, and metrics
"""

from fastapi import APIRouter

# Import specialized sub-routers
from .creation import router as creation_router
from .management import router as management_router
from .operations import router as operations_router
from .monitoring import router as monitoring_router

# Create main jobs router
router = APIRouter(prefix="/jobs", tags=["jobs"])

# Include all sub-routers
router.include_router(creation_router)
router.include_router(management_router)
router.include_router(operations_router)
router.include_router(monitoring_router)

# Export the combined router
__all__ = ["router"] 