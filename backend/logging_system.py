"""
Comprehensive logging system for the AI Agent Template.

This module provides:
- Structured logging with multiple loggers
- Performance monitoring and metrics
- Security event logging
- Middleware for request/response logging
- Development and production configurations
"""

import asyncio
import inspect
import json
import logging
import logging.config
import os
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from functools import wraps
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.environment import get_settings

class StructuredLogger:
    """Structured logger with context management and formatting"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set logging context that will be included in all log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all logging context"""
        self.context.clear()
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format log message with context and metadata"""
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message,
            'context': self.context.copy()
        }
        
        if extra:
            log_data['extra'] = extra
            
        return log_data
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        log_data = self._format_message(message, kwargs)
        self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        log_data = self._format_message(message, kwargs)
        self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        log_data = self._format_message(message, kwargs)
        self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with structured data and optional exception"""
        log_data = self._format_message(message, kwargs)
        
        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self.logger.error(json.dumps(log_data))
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with structured data and optional exception"""
        log_data = self._format_message(message, kwargs)
        
        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self.logger.critical(json.dumps(log_data))

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, logger: StructuredLogger):
        super().__init__(app)
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Set request context
        self.logger.set_context(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get('user-agent'),
            client_ip=self._get_client_ip(request)
        )
        
        # Log incoming request
        self.logger.info(
            "Incoming request",
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=self._filter_headers(dict(request.headers))
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                "Request processed",
                status_code=response.status_code,
                process_time_seconds=round(process_time, 4),
                response_size=response.headers.get('content-length')
            )
            
            # Add performance warning for slow requests
            if process_time > 5.0:  # More than 5 seconds
                self.logger.warning(
                    "Slow request detected",
                    process_time_seconds=round(process_time, 4),
                    threshold_seconds=5.0
                )
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time
            
            # Log error
            self.logger.error(
                "Request failed",
                exception=e,
                process_time_seconds=round(process_time, 4)
            )
            
            raise
        finally:
            # Clear request context
            self.logger.clear_context()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        forwarded = request.headers.get('x-forwarded')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        return request.client.host if request.client else 'unknown'
    
    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter sensitive headers from logging"""
        sensitive_headers = {
            'authorization', 'x-api-key', 'cookie', 'set-cookie',
            'x-auth-token', 'x-csrf-token'
        }
        
        filtered = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = '[REDACTED]'
            else:
                filtered[key] = value
        
        return filtered

class PerformanceLogger:
    """Logger for performance monitoring and metrics"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.metrics: Dict[str, List[float]] = {}
    
    @contextmanager
    def time_operation(self, operation_name: str, **context):
        """Context manager for timing operations"""
        start_time = time.time()
        self.logger.set_context(operation=operation_name, **context)
        
        try:
            yield
            duration = time.time() - start_time
            
            # Store metric
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(duration)
            
            # Log operation
            self.logger.info(
                f"Operation completed: {operation_name}",
                duration_seconds=round(duration, 4)
            )
            
            # Warn on slow operations
            if duration > 1.0:
                self.logger.warning(
                    f"Slow operation: {operation_name}",
                    duration_seconds=round(duration, 4),
                    threshold_seconds=1.0
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Operation failed: {operation_name}",
                exception=e,
                duration_seconds=round(duration, 4)
            )
            raise
        finally:
            self.logger.clear_context()
    
    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all tracked operations"""
        summary = {}
        
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'average_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        return summary
    
    def log_metrics_summary(self):
        """Log performance metrics summary"""
        summary = self.get_metrics_summary()
        self.logger.info("Performance metrics summary", metrics=summary)

class SecurityLogger:
    """Logger for security events and monitoring"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_auth_success(self, user_id: str, method: str = "jwt", **context):
        """Log successful authentication"""
        self.logger.info(
            "Authentication successful",
            user_id=user_id,
            auth_method=method,
            event_type="auth_success",
            **context
        )
    
    def log_auth_failure(self, reason: str, method: str = "jwt", **context):
        """Log authentication failure"""
        self.logger.warning(
            "Authentication failed",
            reason=reason,
            auth_method=method,
            event_type="auth_failure",
            **context
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, **context):
        """Log authorization failure"""
        self.logger.warning(
            "Authorization denied",
            user_id=user_id,
            resource=resource,
            action=action,
            event_type="authz_failure",
            **context
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any], **context):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity detected: {activity_type}",
            activity_type=activity_type,
            details=details,
            event_type="suspicious_activity",
            **context
        )
    
    def log_rate_limit_exceeded(self, identifier: str, limit: str, **context):
        """Log rate limit exceeded"""
        self.logger.warning(
            "Rate limit exceeded",
            identifier=identifier,
            limit=limit,
            event_type="rate_limit_exceeded",
            **context
        )

class DatabaseLogger:
    """Logger for database operations and monitoring"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_query(self, operation: str, table: str, duration: Optional[float] = None, **context):
        """Log database query"""
        log_data = {
            "operation": operation,
            "table": table,
            "event_type": "db_query"
        }
        
        if duration:
            log_data["duration_seconds"] = round(duration, 4)
            
        self.logger.debug("Database query executed", **log_data, **context)
        
        # Warn on slow queries
        if duration and duration > 0.5:
            self.logger.warning(
                "Slow database query",
                **log_data,
                threshold_seconds=0.5,
                **context
            )
    
    def log_connection_error(self, error: Exception, **context):
        """Log database connection error"""
        self.logger.error(
            "Database connection error",
            exception=error,
            event_type="db_connection_error",
            **context
        )
    
    def log_migration(self, migration_name: str, success: bool, duration: float, **context):
        """Log database migration"""
        if success:
            self.logger.info(
                "Database migration completed",
                migration=migration_name,
                duration_seconds=round(duration, 4),
                event_type="db_migration_success",
                **context
            )
        else:
            self.logger.error(
                "Database migration failed",
                migration=migration_name,
                duration_seconds=round(duration, 4),
                event_type="db_migration_failure",
                **context
            )

class AgentLogger:
    """Logger for AI agent operations and monitoring"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_job_created(self, job_id: str, agent_identifier: str, user_id: str, **context):
        """Log job creation"""
        self.logger.info(
            "Agent job created",
            job_id=job_id,
            agent_identifier=agent_identifier,
            user_id=user_id,
            event_type="job_created",
            **context
        )
    
    def log_job_started(self, job_id: str, agent_identifier: str, **context):
        """Log job start"""
        self.logger.info(
            "Agent job started",
            job_id=job_id,
            agent_identifier=agent_identifier,
            event_type="job_started",
            **context
        )
    
    def log_job_completed(self, job_id: str, duration: float, **context):
        """Log job completion"""
        self.logger.info(
            "Agent job completed",
            job_id=job_id,
            duration_seconds=round(duration, 4),
            event_type="job_completed",
            **context
        )
    
    def log_job_failed(self, job_id: str, error: Exception, duration: float, **context):
        """Log job failure"""
        self.logger.error(
            "Agent job failed",
            job_id=job_id,
            exception=error,
            duration_seconds=round(duration, 4),
            event_type="job_failed",
            **context
        )
    
    def log_agent_error(self, agent_identifier: str, error: Exception, **context):
        """Log agent-specific error"""
        self.logger.error(
            "Agent error",
            agent_identifier=agent_identifier,
            exception=error,
            event_type="agent_error",
            **context
        )

# Global logger instances
_main_logger: Optional[StructuredLogger] = None
_performance_logger: Optional[PerformanceLogger] = None
_security_logger: Optional[SecurityLogger] = None
_database_logger: Optional[DatabaseLogger] = None
_agent_logger: Optional[AgentLogger] = None

def get_logger(name: str = __name__) -> StructuredLogger:
    """Get or create structured logger instance"""
    global _main_logger
    if _main_logger is None:
        _main_logger = StructuredLogger(name)
    return _main_logger

def get_performance_logger() -> PerformanceLogger:
    """Get or create performance logger instance"""
    global _performance_logger
    if _performance_logger is None:
        logger = get_logger('performance')
        _performance_logger = PerformanceLogger(logger)
    return _performance_logger

def get_security_logger() -> SecurityLogger:
    """Get or create security logger instance"""
    global _security_logger
    if _security_logger is None:
        logger = get_logger('security')
        _security_logger = SecurityLogger(logger)
    return _security_logger

def get_database_logger() -> DatabaseLogger:
    """Get or create database logger instance"""
    global _database_logger
    if _database_logger is None:
        logger = get_logger('database')
        _database_logger = DatabaseLogger(logger)
    return _database_logger

def get_agent_logger() -> AgentLogger:
    """Get or create agent logger instance"""
    global _agent_logger
    if _agent_logger is None:
        logger = get_logger('agent')
        _agent_logger = AgentLogger(logger)
    return _agent_logger

def setup_logging_middleware(app):
    """Set up logging middleware for FastAPI app"""
    logger = get_logger('request')
    app.add_middleware(RequestLoggingMiddleware, logger=logger)

def log_function_calls(logger: Optional[StructuredLogger] = None):
    """Decorator to log function calls and performance"""
    if logger is None:
        logger = get_logger()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger.debug(f"Function called: {func_name}", args=len(args), kwargs=list(kwargs.keys()))
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Function completed: {func_name}", duration_seconds=round(duration, 4))
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function failed: {func_name}", exception=e, duration_seconds=round(duration, 4))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger.debug(f"Function called: {func_name}", args=len(args), kwargs=list(kwargs.keys()))
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Function completed: {func_name}", duration_seconds=round(duration, 4))
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function failed: {func_name}", exception=e, duration_seconds=round(duration, 4))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def log_startup_info():
    """Log application startup information"""
    logger = get_logger('startup')
    settings = get_settings()
    
    logger.info(
        "Application starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        debug=settings.debug,
        log_level=settings.log_level.value
    )

def log_shutdown_info():
    """Log application shutdown information"""
    logger = get_logger('shutdown')
    logger.info("Application shutting down")
    
    # Log final performance metrics
    perf_logger = get_performance_logger()
    perf_logger.log_metrics_summary() 