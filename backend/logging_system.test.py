"""
Unit tests for the comprehensive logging system.
"""

import pytest
import json
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from logging_system import (
    StructuredLogger, RequestLoggingMiddleware, PerformanceLogger,
    SecurityLogger, DatabaseLogger, AgentLogger,
    get_logger, get_performance_logger, get_security_logger,
    get_database_logger, get_agent_logger, setup_logging_middleware,
    log_function_calls, log_startup_info, log_shutdown_info
)

class TestStructuredLogger:
    """Test StructuredLogger functionality"""

    def setup_method(self):
        """Set up test logger"""
        self.logger = StructuredLogger('test')
        self.mock_logging = Mock()
        self.logger.logger = self.mock_logging

    def test_set_context(self):
        """Test setting logging context"""
        self.logger.set_context(user_id="test", request_id="123")
        
        assert self.logger.context["user_id"] == "test"
        assert self.logger.context["request_id"] == "123"

    def test_clear_context(self):
        """Test clearing logging context"""
        self.logger.set_context(user_id="test")
        self.logger.clear_context()
        
        assert len(self.logger.context) == 0

    def test_info_logging(self):
        """Test info level logging"""
        self.logger.info("Test message", extra_field="value")
        
        self.mock_logging.info.assert_called_once()
        call_args = self.mock_logging.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["message"] == "Test message"
        assert log_data["extra"]["extra_field"] == "value"
        assert "timestamp" in log_data

    def test_error_logging_with_exception(self):
        """Test error logging with exception"""
        exception = ValueError("Test error")
        self.logger.error("Error occurred", exception=exception, context="test")
        
        self.mock_logging.error.assert_called_once()
        call_args = self.mock_logging.error.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["message"] == "Error occurred"
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test error"
        assert "traceback" in log_data["exception"]

    def test_context_in_logs(self):
        """Test that context is included in log messages"""
        self.logger.set_context(user_id="test-user")
        self.logger.info("Test with context")
        
        call_args = self.mock_logging.info.call_args[0][0]
        log_data = json.loads(call_args)
        
        assert log_data["context"]["user_id"] == "test-user"

class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware functionality"""

    def setup_method(self):
        """Set up test middleware"""
        self.app = FastAPI()
        self.logger = Mock(spec=StructuredLogger)
        self.middleware = RequestLoggingMiddleware(self.app, self.logger)

    def test_get_client_ip_forwarded_for(self):
        """Test client IP extraction from X-Forwarded-For header"""
        request = Mock()
        request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        
        ip = self.middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_real_ip(self):
        """Test client IP extraction from X-Real-IP header"""
        request = Mock()
        request.headers = {"x-real-ip": "192.168.1.1"}
        
        ip = self.middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_fallback(self):
        """Test client IP fallback to request.client"""
        request = Mock()
        request.headers = {}
        request.client.host = "127.0.0.1"
        
        ip = self.middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_filter_sensitive_headers(self):
        """Test filtering of sensitive headers"""
        headers = {
            "authorization": "Bearer token123",
            "x-api-key": "secret-key",
            "content-type": "application/json",
            "user-agent": "test-client"
        }
        
        filtered = self.middleware._filter_headers(headers)
        
        assert filtered["authorization"] == "[REDACTED]"
        assert filtered["x-api-key"] == "[REDACTED]"
        assert filtered["content-type"] == "application/json"
        assert filtered["user-agent"] == "test-client"

    @pytest.mark.asyncio
    async def test_middleware_success_flow(self):
        """Test middleware with successful request"""
        # Mock request
        request = Mock()
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/test"
        request.url.__str__ = lambda self: "http://test.com/test"
        request.query_params = {}
        request.headers = {"user-agent": "test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock response
        response = Mock()
        response.status_code = 200
        response.headers = {"content-length": "100"}
        
        # Mock call_next
        async def mock_call_next(req):
            return response
        
        result = await self.middleware.dispatch(request, mock_call_next)
        
        assert result == response
        assert self.logger.set_context.called
        assert self.logger.info.call_count >= 2  # Request and response logs
        assert self.logger.clear_context.called

    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test middleware with exception in request processing"""
        request = Mock()
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/error"
        request.url.__str__ = lambda self: "http://test.com/error"
        request.query_params = {}
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Mock call_next that raises exception
        async def mock_call_next(req):
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await self.middleware.dispatch(request, mock_call_next)
        
        # Should log error
        assert self.logger.error.called
        assert self.logger.clear_context.called

class TestPerformanceLogger:
    """Test PerformanceLogger functionality"""

    def setup_method(self):
        """Set up test performance logger"""
        self.structured_logger = Mock(spec=StructuredLogger)
        self.perf_logger = PerformanceLogger(self.structured_logger)

    def test_time_operation_success(self):
        """Test timing successful operation"""
        with self.perf_logger.time_operation("test_operation", context="test"):
            time.sleep(0.01)  # Small delay
        
        assert "test_operation" in self.perf_logger.metrics
        assert len(self.perf_logger.metrics["test_operation"]) == 1
        assert self.perf_logger.metrics["test_operation"][0] >= 0.01
        
        # Should log operation completion
        assert self.structured_logger.info.called

    def test_time_operation_failure(self):
        """Test timing failed operation"""
        with pytest.raises(ValueError):
            with self.perf_logger.time_operation("failing_operation"):
                raise ValueError("Test error")
        
        # Should log operation failure
        assert self.structured_logger.error.called

    def test_slow_operation_warning(self):
        """Test warning for slow operations"""
        with patch('time.time', side_effect=[0, 2.0]):  # 2 second operation
            with self.perf_logger.time_operation("slow_operation"):
                pass
        
        # Should log warning for slow operation
        assert self.structured_logger.warning.called

    def test_get_metrics_summary(self):
        """Test metrics summary generation"""
        # Add some mock metrics
        self.perf_logger.metrics["operation1"] = [0.1, 0.2, 0.3]
        self.perf_logger.metrics["operation2"] = [0.5, 1.0]
        
        summary = self.perf_logger.get_metrics_summary()
        
        assert "operation1" in summary
        assert summary["operation1"]["count"] == 3
        assert summary["operation1"]["average_time"] == 0.2
        assert summary["operation1"]["min_time"] == 0.1
        assert summary["operation1"]["max_time"] == 0.3

class TestSecurityLogger:
    """Test SecurityLogger functionality"""

    def setup_method(self):
        """Set up test security logger"""
        self.structured_logger = Mock(spec=StructuredLogger)
        self.security_logger = SecurityLogger(self.structured_logger)

    def test_log_auth_success(self):
        """Test logging successful authentication"""
        self.security_logger.log_auth_success(
            user_id="user123",
            method="jwt",
            ip_address="192.168.1.1"
        )
        
        self.structured_logger.info.assert_called_once()
        call_args = self.structured_logger.info.call_args
        
        assert "Authentication successful" in call_args[0]
        assert call_args[1]["user_id"] == "user123"
        assert call_args[1]["auth_method"] == "jwt"
        assert call_args[1]["event_type"] == "auth_success"

    def test_log_auth_failure(self):
        """Test logging authentication failure"""
        self.security_logger.log_auth_failure(
            reason="invalid_token",
            method="jwt",
            ip_address="192.168.1.1"
        )
        
        self.structured_logger.warning.assert_called_once()
        call_args = self.structured_logger.warning.call_args
        
        assert "Authentication failed" in call_args[0]
        assert call_args[1]["reason"] == "invalid_token"
        assert call_args[1]["event_type"] == "auth_failure"

    def test_log_suspicious_activity(self):
        """Test logging suspicious activity"""
        details = {"attempts": 5, "timeframe": "1 minute"}
        
        self.security_logger.log_suspicious_activity(
            activity_type="brute_force",
            details=details,
            ip_address="192.168.1.1"
        )
        
        self.structured_logger.warning.assert_called_once()
        call_args = self.structured_logger.warning.call_args
        
        assert "Suspicious activity detected" in call_args[0]
        assert call_args[1]["activity_type"] == "brute_force"
        assert call_args[1]["details"] == details

class TestDatabaseLogger:
    """Test DatabaseLogger functionality"""

    def setup_method(self):
        """Set up test database logger"""
        self.structured_logger = Mock(spec=StructuredLogger)
        self.db_logger = DatabaseLogger(self.structured_logger)

    def test_log_query(self):
        """Test logging database query"""
        self.db_logger.log_query(
            operation="SELECT",
            table="jobs",
            duration=0.1,
            rows_affected=5
        )
        
        self.structured_logger.debug.assert_called_once()
        call_args = self.structured_logger.debug.call_args
        
        assert "Database query executed" in call_args[0]
        assert call_args[1]["operation"] == "SELECT"
        assert call_args[1]["table"] == "jobs"
        assert call_args[1]["duration_seconds"] == 0.1

    def test_log_slow_query_warning(self):
        """Test warning for slow database queries"""
        self.db_logger.log_query(
            operation="SELECT",
            table="jobs",
            duration=1.0  # Slow query
        )
        
        # Should log both debug and warning
        assert self.structured_logger.debug.called
        assert self.structured_logger.warning.called

    def test_log_connection_error(self):
        """Test logging database connection error"""
        error = ConnectionError("Database unavailable")
        
        self.db_logger.log_connection_error(error, database="primary")
        
        self.structured_logger.error.assert_called_once()
        call_args = self.structured_logger.error.call_args
        
        assert "Database connection error" in call_args[0]
        assert call_args[1]["exception"] == error
        assert call_args[1]["event_type"] == "db_connection_error"

class TestAgentLogger:
    """Test AgentLogger functionality"""

    def setup_method(self):
        """Set up test agent logger"""
        self.structured_logger = Mock(spec=StructuredLogger)
        self.agent_logger = AgentLogger(self.structured_logger)

    def test_log_job_created(self):
        """Test logging job creation"""
        self.agent_logger.log_job_created(
            job_id="job123",
            job_type="text_processing",
            user_id="user456",
            priority=1
        )
        
        self.structured_logger.info.assert_called_once()
        call_args = self.structured_logger.info.call_args
        
        assert "Agent job created" in call_args[0]
        assert call_args[1]["job_id"] == "job123"
        assert call_args[1]["job_type"] == "text_processing"
        assert call_args[1]["user_id"] == "user456"
        assert call_args[1]["event_type"] == "job_created"

    def test_log_job_failed(self):
        """Test logging job failure"""
        error = RuntimeError("Processing failed")
        
        self.agent_logger.log_job_failed(
            job_id="job123",
            error=error,
            duration=30.5
        )
        
        self.structured_logger.error.assert_called_once()
        call_args = self.structured_logger.error.call_args
        
        assert "Agent job failed" in call_args[0]
        assert call_args[1]["job_id"] == "job123"
        assert call_args[1]["exception"] == error
        assert call_args[1]["duration_seconds"] == 30.5

class TestGlobalLoggerFunctions:
    """Test global logger factory functions"""

    def test_get_logger_singleton(self):
        """Test that get_logger returns singleton instances"""
        # Reset global state
        import logging_system
        logging_system._main_logger = None
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
        assert isinstance(logger1, StructuredLogger)

    def test_get_performance_logger(self):
        """Test performance logger factory"""
        perf_logger = get_performance_logger()
        assert isinstance(perf_logger, PerformanceLogger)

    def test_get_security_logger(self):
        """Test security logger factory"""
        sec_logger = get_security_logger()
        assert isinstance(sec_logger, SecurityLogger)

    def test_get_database_logger(self):
        """Test database logger factory"""
        db_logger = get_database_logger()
        assert isinstance(db_logger, DatabaseLogger)

    def test_get_agent_logger(self):
        """Test agent logger factory"""
        agent_logger = get_agent_logger()
        assert isinstance(agent_logger, AgentLogger)

class TestLoggingDecorator:
    """Test function logging decorator"""

    def test_sync_function_logging(self):
        """Test logging decorator with synchronous function"""
        mock_logger = Mock(spec=StructuredLogger)
        
        @log_function_calls(mock_logger)
        def test_function(x, y=None):
            return x + (y or 0)
        
        result = test_function(1, y=2)
        
        assert result == 3
        assert mock_logger.debug.call_count >= 2  # Start and end logs

    def test_sync_function_exception_logging(self):
        """Test logging decorator with synchronous function that raises exception"""
        mock_logger = Mock(spec=StructuredLogger)
        
        @log_function_calls(mock_logger)
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Should log error
        assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_async_function_logging(self):
        """Test logging decorator with asynchronous function"""
        mock_logger = Mock(spec=StructuredLogger)
        
        @log_function_calls(mock_logger)
        async def async_test_function(x):
            return x * 2
        
        result = await async_test_function(5)
        
        assert result == 10
        assert mock_logger.debug.call_count >= 2  # Start and end logs

class TestLoggingMiddlewareIntegration:
    """Test logging middleware integration with FastAPI"""

    def test_setup_logging_middleware(self):
        """Test setting up logging middleware on FastAPI app"""
        app = FastAPI()
        
        # Mock the middleware addition
        with patch.object(app, 'add_middleware') as mock_add:
            setup_logging_middleware(app)
            
            mock_add.assert_called_once()
            args = mock_add.call_args[0]
            assert args[0] == RequestLoggingMiddleware

class TestStartupShutdownLogging:
    """Test startup and shutdown logging functions"""

    @patch('logging_system.get_settings')
    def test_log_startup_info(self, mock_get_settings):
        """Test logging startup information"""
        # Mock settings
        mock_settings = Mock()
        mock_settings.app_name = "Test API"
        mock_settings.app_version = "1.0.0"
        mock_settings.environment.value = "development"
        mock_settings.debug = True
        mock_settings.log_level.value = "INFO"
        mock_get_settings.return_value = mock_settings
        
        with patch('logging_system.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            log_startup_info()
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Application starting" in call_args[0]

    def test_log_shutdown_info(self):
        """Test logging shutdown information"""
        with patch('logging_system.get_logger') as mock_get_logger, \
             patch('logging_system.get_performance_logger') as mock_get_perf:
            
            mock_logger = Mock()
            mock_perf_logger = Mock()
            mock_get_logger.return_value = mock_logger
            mock_get_perf.return_value = mock_perf_logger
            
            log_shutdown_info()
            
            mock_logger.info.assert_called_once()
            mock_perf_logger.log_metrics_summary.assert_called_once()

class TestLoggingIntegration:
    """Integration tests for the complete logging system"""

    def test_full_logging_flow(self):
        """Test complete logging flow with all components"""
        # Create loggers
        main_logger = get_logger('integration_test')
        perf_logger = get_performance_logger()
        security_logger = get_security_logger()
        
        # Test that they're all working
        assert isinstance(main_logger, StructuredLogger)
        assert isinstance(perf_logger, PerformanceLogger)
        assert isinstance(security_logger, SecurityLogger)
        
        # Test context sharing
        main_logger.set_context(test_id="integration")
        
        # This would work in a real scenario with proper logging configuration
        # Here we're just testing that the objects are created correctly 