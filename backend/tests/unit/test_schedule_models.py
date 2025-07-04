"""
Unit tests for schedule model validation and methods.

Tests the ScheduleCreate model with valid data combinations, field validation,
and edge cases for all configuration options.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from typing import Dict, Any

from models.schedule import (
    ScheduleCreate, 
    ScheduleUpdate,
    Schedule,
    ScheduleStatus,
    AgentConfigurationData, 
    AgentProfileEnum,
    AgentPerformanceModeEnum,
    AgentExecutionConfigData,
    AgentModelConfigData,
    AgentLoggingConfigData,
    AgentSecurityConfigData
)
from tests.fixtures.schedule_fixtures import ScheduleFixtures
# from tests.utils.time_utils import MockTimeProvider, CronTestHelper, TimeTestManager
from tests.utils.database_utils import DatabaseTestUtils


class TestScheduleCreateModel:
    """Test ScheduleCreate model validation and methods."""
    
    def test_minimal_valid_schedule_create(self):
        """Test ScheduleCreate with minimal required fields."""
        data = {
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "agent_config_data": {
                "name": "test_agent",
                "job_data": {"prompt": "Hello world"}
            }
        }
        
        schedule = ScheduleCreate(**data)
        
        assert schedule.title == "Test Schedule"
        assert schedule.agent_name == "test_agent"
        assert schedule.cron_expression == "0 9 * * *"
        assert schedule.enabled is True  # Default value
        assert schedule.timezone is None  # Default value
        assert schedule.description == "test_agent scheduled execution"  # Auto-generated
        assert schedule.agent_config_data.name == "test_agent"
        assert schedule.agent_config_data.job_data == {"prompt": "Hello world"}
    
    def test_complete_schedule_create_all_fields(self):
        """Test ScheduleCreate with all possible fields populated."""
        data = {
            "title": "Complete Test Schedule",
            "description": "A comprehensive test schedule with all fields",
            "agent_name": "comprehensive_agent",
            "cron_expression": "0 */6 * * *",
            "enabled": False,
            "timezone": "America/New_York",
            "agent_config_data": {
                "name": "comprehensive_agent",
                "description": "Comprehensive agent for testing",
                "profile": "quality",
                "performance_mode": "speed",
                "enabled": True,
                "result_format": "json",
                "execution": {
                    "timeout_seconds": 1800,
                    "max_retries": 5,
                    "retry_delay_base": 3.0,
                    "enable_caching": False,
                    "cache_ttl_seconds": 7200,
                    "priority": 8,
                    "memory_limit_mb": 2048,
                    "cpu_limit_percent": 80.0
                },
                "model": {
                    "model_name": "gpt-4",
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "top_p": 0.9,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.2,
                    "stop_sequences": ["END", "STOP"],
                    "custom_parameters": {"custom_param": "value"}
                },
                "logging": {
                    "log_level": "DEBUG",
                    "enable_performance_logging": True,
                    "enable_debug_logging": True,
                    "log_requests": True,
                    "log_responses": True,
                    "log_errors": True,
                    "metrics_enabled": True,
                    "trace_enabled": True
                },
                "security": {
                    "enable_input_validation": True,
                    "enable_output_sanitization": True,
                    "max_input_size_bytes": 2097152,
                    "max_output_size_bytes": 2097152,
                    "allowed_domains": ["api.openai.com", "example.com"],
                    "blocked_keywords": ["malicious", "harmful"],
                    "rate_limit_per_minute": 120
                },
                "job_data": {
                    "prompt": "Comprehensive test prompt",
                    "additional_params": {"param1": "value1", "param2": 42}
                },
                "custom_settings": {
                    "custom_flag": True,
                    "custom_value": 100
                }
            }
        }
        
        schedule = ScheduleCreate(**data)
        
        # Verify all basic fields
        assert schedule.title == "Complete Test Schedule"
        assert schedule.description == "A comprehensive test schedule with all fields"
        assert schedule.agent_name == "comprehensive_agent"
        assert schedule.cron_expression == "0 */6 * * *"
        assert schedule.enabled is False
        assert schedule.timezone == "America/New_York"
        
        # Verify agent configuration
        agent_config = schedule.agent_config_data
        assert agent_config.name == "comprehensive_agent"
        assert agent_config.description == "Comprehensive agent for testing"
        assert agent_config.profile == AgentProfileEnum.QUALITY
        assert agent_config.performance_mode == AgentPerformanceModeEnum.SPEED
        assert agent_config.enabled is True
        assert agent_config.result_format == "json"
        
        # Verify execution config
        exec_config = agent_config.execution
        assert exec_config.timeout_seconds == 1800
        assert exec_config.max_retries == 5
        assert exec_config.retry_delay_base == 3.0
        assert exec_config.enable_caching is False
        assert exec_config.cache_ttl_seconds == 7200
        assert exec_config.priority == 8
        assert exec_config.memory_limit_mb == 2048
        assert exec_config.cpu_limit_percent == 80.0
        
        # Verify model config
        model_config = agent_config.model
        assert model_config.model_name == "gpt-4"
        assert model_config.temperature == 0.3
        assert model_config.max_tokens == 4000
        assert model_config.top_p == 0.9
        assert model_config.frequency_penalty == 0.5
        assert model_config.presence_penalty == 0.2
        assert model_config.stop_sequences == ["END", "STOP"]
        assert model_config.custom_parameters == {"custom_param": "value"}
        
        # Verify logging config
        logging_config = agent_config.logging
        assert logging_config.log_level == "DEBUG"
        assert logging_config.enable_performance_logging is True
        assert logging_config.enable_debug_logging is True
        assert logging_config.log_requests is True
        assert logging_config.log_responses is True
        assert logging_config.log_errors is True
        assert logging_config.metrics_enabled is True
        assert logging_config.trace_enabled is True
        
        # Verify security config
        security_config = agent_config.security
        assert security_config.enable_input_validation is True
        assert security_config.enable_output_sanitization is True
        assert security_config.max_input_size_bytes == 2097152
        assert security_config.max_output_size_bytes == 2097152
        assert security_config.allowed_domains == ["api.openai.com", "example.com"]
        assert security_config.blocked_keywords == ["malicious", "harmful"]
        assert security_config.rate_limit_per_minute == 120
        
        # Verify job data and custom settings
        assert agent_config.job_data == {
            "prompt": "Comprehensive test prompt",
            "additional_params": {"param1": "value1", "param2": 42}
        }
        assert agent_config.custom_settings == {
            "custom_flag": True,
            "custom_value": 100
        }
    
    @pytest.mark.parametrize("profile", [
        AgentProfileEnum.FAST,
        AgentProfileEnum.BALANCED,
        AgentProfileEnum.QUALITY,
        AgentProfileEnum.CUSTOM
    ])
    def test_agent_profile_variations(self, profile):
        """Test ScheduleCreate with different agent profiles."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["agent_config_data"]["profile"] = profile.value
        
        schedule = ScheduleCreate(**data)
        assert schedule.agent_config_data.profile == profile
    
    @pytest.mark.parametrize("performance_mode", [
        AgentPerformanceModeEnum.SPEED,
        AgentPerformanceModeEnum.QUALITY,
        AgentPerformanceModeEnum.BALANCED,
        AgentPerformanceModeEnum.POWER_SAVE
    ])
    def test_performance_mode_variations(self, performance_mode):
        """Test ScheduleCreate with different performance modes."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["agent_config_data"]["performance_mode"] = performance_mode.value
        
        schedule = ScheduleCreate(**data)
        assert schedule.agent_config_data.performance_mode == performance_mode
    
    @pytest.mark.parametrize("cron_expression", [
        "0 9 * * *",        # Daily at 9 AM
        "0 */6 * * *",      # Every 6 hours
        "0 0 * * 0",        # Weekly on Sunday
        "0 0 1 * *",        # Monthly on 1st
        "*/15 * * * *",     # Every 15 minutes
        "0 9-17 * * 1-5",   # Weekdays 9 AM to 5 PM
        "0 8,12,16 * * *",  # Three times a day
        "0 2 */2 * *",      # Every other day at 2 AM
        "0 0 1,15 * *",     # 1st and 15th of month
        "0 0 * * 1,3,5"     # Monday, Wednesday, Friday
    ])
    def test_valid_cron_expressions(self, cron_expression):
        """Test ScheduleCreate with various valid cron expressions."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["cron_expression"] = cron_expression
        
        schedule = ScheduleCreate(**data)
        assert schedule.cron_expression == cron_expression
    
    @pytest.mark.parametrize("timezone", [
        "UTC",
        "America/New_York",
        "America/Los_Angeles",
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Australia/Sydney",
        None  # Default timezone
    ])
    def test_timezone_variations(self, timezone):
        """Test ScheduleCreate with different timezone values."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        if timezone is not None:
            data["timezone"] = timezone
        
        schedule = ScheduleCreate(**data)
        assert schedule.timezone == timezone
    
    @pytest.mark.parametrize("enabled", [True, False])
    def test_enabled_variations(self, enabled):
        """Test ScheduleCreate with enabled/disabled states."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["enabled"] = enabled
        
        schedule = ScheduleCreate(**data)
        assert schedule.enabled == enabled
    
    def test_title_edge_cases(self):
        """Test ScheduleCreate title field edge cases."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Single character title
        data = base_data.copy()
        data["title"] = "A"
        schedule = ScheduleCreate(**data)
        assert schedule.title == "A"
        
        # Maximum length title (200 characters)
        data = base_data.copy()
        long_title = "x" * 200
        data["title"] = long_title
        schedule = ScheduleCreate(**data)
        assert schedule.title == long_title
        
        # Title with special characters
        data = base_data.copy()
        data["title"] = "Test-Schedule_2024!@#$%"
        schedule = ScheduleCreate(**data)
        assert schedule.title == "Test-Schedule_2024!@#$%"
        
        # Title with whitespace (should be trimmed)
        data = base_data.copy()
        data["title"] = "  Trimmed Title  "
        schedule = ScheduleCreate(**data)
        assert schedule.title == "Trimmed Title"
    
    def test_description_variations(self):
        """Test ScheduleCreate description field variations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Explicit None description
        data = base_data.copy()
        data["description"] = None
        schedule = ScheduleCreate(**data)
        assert schedule.description == "simple_agent scheduled execution"  # Auto-generated
        
        # Empty string description (gets auto-generated too)
        data = base_data.copy()
        data["description"] = ""
        schedule = ScheduleCreate(**data)
        assert schedule.description == "simple_agent scheduled execution"  # Auto-generated
        
        # Explicit valid description
        data = base_data.copy()
        data["description"] = "Custom description"
        schedule = ScheduleCreate(**data)
        assert schedule.description == "Custom description"
        
        # Maximum length description (1000 characters)
        data = base_data.copy()
        long_description = "x" * 1000
        data["description"] = long_description
        schedule = ScheduleCreate(**data)
        assert schedule.description == long_description
        
        # Description with newlines and special characters
        data = base_data.copy()
        data["description"] = "Multi-line\ndescription with\nspecial chars: !@#$%^&*()"
        schedule = ScheduleCreate(**data)
        assert "\n" in schedule.description
    
    def test_agent_name_edge_cases(self):
        """Test ScheduleCreate agent_name field edge cases."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Single character agent name
        data = base_data.copy()
        data["agent_name"] = "a"
        data["agent_config_data"]["name"] = "a"
        schedule = ScheduleCreate(**data)
        assert schedule.agent_name == "a"
        
        # Maximum length agent name (100 characters)
        data = base_data.copy()
        long_name = "x" * 100
        data["agent_name"] = long_name
        data["agent_config_data"]["name"] = long_name
        schedule = ScheduleCreate(**data)
        assert schedule.agent_name == long_name
        
        # Agent name with underscores and numbers
        data = base_data.copy()
        data["agent_name"] = "agent_v2_test_123"
        data["agent_config_data"]["name"] = "agent_v2_test_123"
        schedule = ScheduleCreate(**data)
        assert schedule.agent_name == "agent_v2_test_123"
        
        # Agent name with whitespace (should be trimmed)
        data = base_data.copy()
        data["agent_name"] = "  trimmed_agent  "
        data["agent_config_data"]["name"] = "  trimmed_agent  "
        schedule = ScheduleCreate(**data)
        assert schedule.agent_name == "trimmed_agent"
    
    def test_execution_config_combinations(self):
        """Test different execution configuration combinations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # High performance configuration
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {
            "timeout_seconds": 3600,
            "max_retries": 10,
            "retry_delay_base": 1.0,
            "enable_caching": True,
            "cache_ttl_seconds": 0,  # No cache
            "priority": 10,
            "memory_limit_mb": 8192,
            "cpu_limit_percent": 100.0
        }
        
        schedule = ScheduleCreate(**data)
        exec_config = schedule.agent_config_data.execution
        assert exec_config.timeout_seconds == 3600
        assert exec_config.max_retries == 10
        assert exec_config.priority == 10
        assert exec_config.memory_limit_mb == 8192
        assert exec_config.cpu_limit_percent == 100.0
        
        # Minimal performance configuration
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {
            "timeout_seconds": 1,
            "max_retries": 0,
            "retry_delay_base": 0.1,
            "enable_caching": False,
            "priority": 0,
            "memory_limit_mb": 1,
            "cpu_limit_percent": 0.1
        }
        
        schedule = ScheduleCreate(**data)
        exec_config = schedule.agent_config_data.execution
        assert exec_config.timeout_seconds == 1
        assert exec_config.max_retries == 0
        assert exec_config.priority == 0
        assert exec_config.memory_limit_mb == 1
        assert exec_config.cpu_limit_percent == 0.1
    
    def test_model_config_variations(self):
        """Test different model configuration variations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Conservative model settings
        data = base_data.copy()
        data["agent_config_data"]["model"] = {
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.0,
            "max_tokens": 1,
            "top_p": 0.0,
            "frequency_penalty": -2.0,
            "presence_penalty": -2.0,
            "stop_sequences": [],
            "custom_parameters": {}
        }
        
        schedule = ScheduleCreate(**data)
        model_config = schedule.agent_config_data.model
        assert model_config.model_name == "gpt-3.5-turbo"
        assert model_config.temperature == 0.0
        assert model_config.max_tokens == 1
        assert model_config.frequency_penalty == -2.0
        assert model_config.presence_penalty == -2.0
        
        # Creative model settings
        data = base_data.copy()
        data["agent_config_data"]["model"] = {
            "model_name": "gpt-4-turbo",
            "temperature": 2.0,
            "max_tokens": 32000,
            "top_p": 1.0,
            "frequency_penalty": 2.0,
            "presence_penalty": 2.0,
            "stop_sequences": ["STOP", "END", "DONE", "COMPLETE"],
            "custom_parameters": {
                "advanced_setting": "value",
                "experimental_flag": True,
                "numeric_param": 123.456
            }
        }
        
        schedule = ScheduleCreate(**data)
        model_config = schedule.agent_config_data.model
        assert model_config.model_name == "gpt-4-turbo"
        assert model_config.temperature == 2.0
        assert model_config.max_tokens == 32000
        assert model_config.frequency_penalty == 2.0
        assert model_config.presence_penalty == 2.0
        assert len(model_config.stop_sequences) == 4
        assert "experimental_flag" in model_config.custom_parameters
    
    def test_logging_config_combinations(self):
        """Test different logging configuration combinations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # All logging disabled
        data = base_data.copy()
        data["agent_config_data"]["logging"] = {
            "log_level": "CRITICAL",
            "enable_performance_logging": False,
            "enable_debug_logging": False,
            "log_requests": False,
            "log_responses": False,
            "log_errors": False,
            "metrics_enabled": False,
            "trace_enabled": False
        }
        
        schedule = ScheduleCreate(**data)
        logging_config = schedule.agent_config_data.logging
        assert logging_config.log_level == "CRITICAL"
        assert not any([
            logging_config.enable_performance_logging,
            logging_config.enable_debug_logging,
            logging_config.log_requests,
            logging_config.log_responses,
            logging_config.log_errors,
            logging_config.metrics_enabled,
            logging_config.trace_enabled
        ])
        
        # All logging enabled
        data = base_data.copy()
        data["agent_config_data"]["logging"] = {
            "log_level": "DEBUG",
            "enable_performance_logging": True,
            "enable_debug_logging": True,
            "log_requests": True,
            "log_responses": True,
            "log_errors": True,
            "metrics_enabled": True,
            "trace_enabled": True
        }
        
        schedule = ScheduleCreate(**data)
        logging_config = schedule.agent_config_data.logging
        assert logging_config.log_level == "DEBUG"
        assert all([
            logging_config.enable_performance_logging,
            logging_config.enable_debug_logging,
            logging_config.log_requests,
            logging_config.log_responses,
            logging_config.log_errors,
            logging_config.metrics_enabled,
            logging_config.trace_enabled
        ])
    
    def test_security_config_variations(self):
        """Test different security configuration variations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Minimal security
        data = base_data.copy()
        data["agent_config_data"]["security"] = {
            "enable_input_validation": False,
            "enable_output_sanitization": False,
            "max_input_size_bytes": 1024,
            "max_output_size_bytes": 1024,
            "allowed_domains": [],
            "blocked_keywords": [],
            "rate_limit_per_minute": 1
        }
        
        schedule = ScheduleCreate(**data)
        security_config = schedule.agent_config_data.security
        assert not security_config.enable_input_validation
        assert not security_config.enable_output_sanitization
        assert security_config.max_input_size_bytes == 1024
        assert security_config.rate_limit_per_minute == 1
        assert len(security_config.allowed_domains) == 0
        
        # Maximum security
        data = base_data.copy()
        data["agent_config_data"]["security"] = {
            "enable_input_validation": True,
            "enable_output_sanitization": True,
            "max_input_size_bytes": 10485760,  # 10MB
            "max_output_size_bytes": 10485760,
            "allowed_domains": [
                "api.openai.com",
                "trusted-service.com",
                "internal-api.company.com"
            ],
            "blocked_keywords": [
                "malicious", "harmful", "dangerous", "exploit", "hack"
            ],
            "rate_limit_per_minute": 1000
        }
        
        schedule = ScheduleCreate(**data)
        security_config = schedule.agent_config_data.security
        assert security_config.enable_input_validation is True
        assert security_config.enable_output_sanitization is True
        assert security_config.max_input_size_bytes == 10485760
        assert security_config.rate_limit_per_minute == 1000
        assert len(security_config.allowed_domains) == 3
        assert len(security_config.blocked_keywords) == 5
    
    def test_complex_job_data_variations(self):
        """Test ScheduleCreate with complex job data variations."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Simple job data
        data = base_data.copy()
        data["agent_config_data"]["job_data"] = {"prompt": "Simple task"}
        
        schedule = ScheduleCreate(**data)
        assert schedule.agent_config_data.job_data == {"prompt": "Simple task"}
        
        # Complex nested job data
        data = base_data.copy()
        data["agent_config_data"]["job_data"] = {
            "prompt": "Complex analysis task",
            "input_files": ["file1.csv", "file2.json", "file3.txt"],
            "output_format": "structured_report",
            "analysis_params": {
                "method": "statistical",
                "confidence_level": 0.95,
                "include_visualizations": True,
                "chart_types": ["bar", "line", "scatter"]
            },
            "constraints": {
                "max_processing_time": 3600,
                "memory_limit": "4GB",
                "quality_threshold": 0.8
            },
            "metadata": {
                "created_by": "automated_system",
                "priority": "high",
                "tags": ["analysis", "reporting", "automated"]
            }
        }
        
        schedule = ScheduleCreate(**data)
        job_data = schedule.agent_config_data.job_data
        assert job_data["prompt"] == "Complex analysis task"
        assert len(job_data["input_files"]) == 3
        assert job_data["analysis_params"]["confidence_level"] == 0.95
        assert "memory_limit" in job_data["constraints"]
        assert "tags" in job_data["metadata"]
    
    def test_custom_settings_variations(self):
        """Test ScheduleCreate with different custom settings."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Empty custom settings
        data = base_data.copy()
        data["agent_config_data"]["custom_settings"] = {}
        
        schedule = ScheduleCreate(**data)
        assert schedule.agent_config_data.custom_settings == {}
        
        # Complex custom settings
        data = base_data.copy()
        data["agent_config_data"]["custom_settings"] = {
            "feature_flags": {
                "enable_beta_features": True,
                "use_experimental_api": False
            },
            "integrations": {
                "slack_webhook": "https://hooks.slack.com/services/...",
                "email_notifications": True,
                "webhook_timeout": 30
            },
            "performance_tuning": {
                "batch_size": 100,
                "parallel_processing": True,
                "cache_strategy": "aggressive"
            },
            "business_rules": {
                "max_cost_per_execution": 5.00,
                "allowed_regions": ["us-east-1", "us-west-2"],
                "compliance_level": "strict"
            }
        }
        
        schedule = ScheduleCreate(**data)
        custom_settings = schedule.agent_config_data.custom_settings
        assert custom_settings["feature_flags"]["enable_beta_features"] is True
        assert "slack_webhook" in custom_settings["integrations"]
        assert custom_settings["performance_tuning"]["batch_size"] == 100
        assert "compliance_level" in custom_settings["business_rules"]
    
    def test_get_next_run_time_method(self):
        """Test ScheduleCreate.get_next_run_time() method."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["cron_expression"] = "0 9 * * *"  # Daily at 9 AM
        data["timezone"] = "UTC"
        
        schedule = ScheduleCreate(**data)
        next_run = schedule.get_next_run_time()
        
        assert isinstance(next_run, datetime)
        assert next_run.tzinfo == timezone.utc
        assert next_run.hour == 9
        assert next_run.minute == 0
        
        # Test with different timezone
        data["timezone"] = "America/New_York"
        schedule = ScheduleCreate(**data)
        next_run_ny = schedule.get_next_run_time()
        
        assert isinstance(next_run_ny, datetime)
        assert next_run_ny.tzinfo == timezone.utc
    
    def test_get_cron_description_method(self):
        """Test ScheduleCreate.get_cron_description() method."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Test common cron expressions with actual expected outputs
        test_cases = [
            ("0 9 * * *", "Daily at 9:00 AM"),
            ("0 0 * * 0", "Every Sunday at midnight"),
            ("0 0 1 * *", "First day of every month at midnight"),
            ("*/15 * * * *", "Runs at minute */15")
        ]
        
        for cron_expr, expected_description in test_cases:
            data["cron_expression"] = cron_expr
            schedule = ScheduleCreate(**data)
            description = schedule.get_cron_description()
            
            assert isinstance(description, str)
            assert len(description) > 0
            # Check that the description matches what CronUtils actually returns
            assert description == expected_description
    
    def test_auto_description_generation(self):
        """Test automatic description generation from agent name."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Test with various agent names
        test_cases = [
            "simple_agent",
            "data_processor",
            "report_generator",
            "analytics_engine",
            "notification_service"
        ]
        
        for agent_name in test_cases:
            data["agent_name"] = agent_name
            data["agent_config_data"]["name"] = agent_name
            data.pop("description", None)  # Remove explicit description
            
            schedule = ScheduleCreate(**data)
            expected_description = f"{agent_name} scheduled execution"
            assert schedule.description == expected_description
    
    def test_field_defaults(self):
        """Test that all fields have appropriate default values."""
        minimal_data = {
            "title": "Test",
            "agent_name": "test",
            "cron_expression": "0 0 * * *",
            "agent_config_data": {
                "name": "test",
                "job_data": {"prompt": "test"}
            }
        }
        
        schedule = ScheduleCreate(**minimal_data)
        
        # Test schedule defaults
        assert schedule.enabled is True
        assert schedule.timezone is None
        assert schedule.description == "test scheduled execution"
        
        # Test agent config defaults
        agent_config = schedule.agent_config_data
        assert agent_config.profile == AgentProfileEnum.BALANCED
        assert agent_config.performance_mode == AgentPerformanceModeEnum.BALANCED
        assert agent_config.enabled is True
        assert agent_config.result_format is None
        assert agent_config.description is None
        assert agent_config.custom_settings == {}
        
        # Test sub-config defaults
        assert agent_config.execution.timeout_seconds == 300
        assert agent_config.execution.max_retries == 3
        assert agent_config.execution.enable_caching is True
        assert agent_config.execution.priority == 5
        
        assert agent_config.model.temperature == 0.7
        assert agent_config.model.top_p == 1.0
        assert agent_config.model.frequency_penalty == 0.0
        assert agent_config.model.presence_penalty == 0.0
        assert agent_config.model.stop_sequences == []
        
        assert agent_config.logging.log_level == "INFO"
        assert agent_config.logging.enable_performance_logging is True
        assert agent_config.logging.log_requests is True
        
        assert agent_config.security.enable_input_validation is True
        assert agent_config.security.enable_output_sanitization is True
        assert agent_config.security.rate_limit_per_minute == 60


class TestScheduleCreateValidationErrors:
    """Test ScheduleCreate model validation error cases."""
    
    def test_missing_required_fields(self):
        """Test ScheduleCreate with missing required fields."""
        # Missing title
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(
                agent_name="test",
                cron_expression="0 9 * * *",
                agent_config_data={"name": "test", "job_data": {"prompt": "test"}}
            )
        assert "title" in str(exc_info.value)
        
        # Missing agent_name
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(
                title="Test",
                cron_expression="0 9 * * *",
                agent_config_data={"name": "test", "job_data": {"prompt": "test"}}
            )
        assert "agent_name" in str(exc_info.value)
        
        # Missing cron_expression
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(
                title="Test",
                agent_name="test",
                agent_config_data={"name": "test", "job_data": {"prompt": "test"}}
            )
        assert "cron_expression" in str(exc_info.value)
        
        # Missing agent_config_data
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(
                title="Test",
                agent_name="test",
                cron_expression="0 9 * * *"
            )
        assert "agent_config_data" in str(exc_info.value)
    
    def test_empty_string_fields(self):
        """Test ScheduleCreate with empty string fields."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Empty title
        data = base_data.copy()
        data["title"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "title" in str(exc_info.value)
        
        # Whitespace-only title
        data = base_data.copy()
        data["title"] = "   "
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "title" in str(exc_info.value)
        
        # Empty agent_name
        data = base_data.copy()
        data["agent_name"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "agent_name" in str(exc_info.value)
        
        # Empty cron_expression
        data = base_data.copy()
        data["cron_expression"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "cron_expression" in str(exc_info.value)
    
    @pytest.mark.parametrize("invalid_cron", [
        "",                 # Empty
        "invalid",          # Not cron format
        "0 25 * * *",       # Invalid hour (25)
        "0 * * * 8",        # Invalid day of week (8)
        "0 * 32 * *",       # Invalid day of month (32)
        "0 * * 13 *",       # Invalid month (13)
        "0 *",              # Too few fields
        "60 0 * * *",       # Invalid minute (60)
        "0 0 0 * *",        # Invalid day (0)
        "0 0 * 0 *",        # Invalid month (0)
        "@invalid",         # Invalid special string
        "0-60 * * * *",     # Invalid range
    ])
    def test_invalid_cron_expressions(self, invalid_cron):
        """Test ScheduleCreate with invalid cron expressions."""
        data = ScheduleFixtures.valid_schedule_create_minimal()
        data["cron_expression"] = invalid_cron
        
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "cron" in str(exc_info.value).lower()
    
    def test_field_length_limits(self):
        """Test ScheduleCreate field length limit validation."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Title too long (over 200 characters)
        data = base_data.copy()
        data["title"] = "x" * 201
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "title" in str(exc_info.value)
        
        # Description too long (over 1000 characters)
        data = base_data.copy()
        data["description"] = "x" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "description" in str(exc_info.value)
        
        # Agent name too long (over 100 characters)
        data = base_data.copy()
        long_name = "x" * 101
        data["agent_name"] = long_name
        data["agent_config_data"]["name"] = long_name
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "agent_name" in str(exc_info.value)
        
        # Cron expression too long (over 100 characters)
        data = base_data.copy()
        data["cron_expression"] = "0 9 * * *" + ("x" * 96)
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        # This might fail on cron validation before length validation
        assert any(keyword in str(exc_info.value).lower() for keyword in ["cron", "length"])
        
        # Timezone too long (over 100 characters)
        data = base_data.copy()
        data["timezone"] = "x" * 101
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "timezone" in str(exc_info.value)
    
    def test_invalid_agent_config_data(self):
        """Test ScheduleCreate with invalid agent configuration data."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Missing agent name in config
        data = base_data.copy()
        data["agent_config_data"] = {"job_data": {"prompt": "test"}}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "name" in str(exc_info.value)
        
        # Missing job_data
        data = base_data.copy()
        data["agent_config_data"] = {"name": "test"}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "job_data" in str(exc_info.value)
        
        # Empty agent name in config
        data = base_data.copy()
        data["agent_config_data"]["name"] = ""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "name" in str(exc_info.value)
    
    def test_invalid_execution_config_values(self):
        """Test ScheduleCreate with invalid execution config values."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Invalid timeout_seconds (too low)
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {"timeout_seconds": 0}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "timeout_seconds" in str(exc_info.value)
        
        # Invalid timeout_seconds (too high)
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {"timeout_seconds": 3601}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "timeout_seconds" in str(exc_info.value)
        
        # Invalid max_retries (negative)
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {"max_retries": -1}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "max_retries" in str(exc_info.value)
        
        # Invalid priority (too high)
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {"priority": 11}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "priority" in str(exc_info.value)
        
        # Invalid cpu_limit_percent (too high)
        data = base_data.copy()
        data["agent_config_data"]["execution"] = {"cpu_limit_percent": 101.0}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "cpu_limit_percent" in str(exc_info.value)
    
    def test_invalid_model_config_values(self):
        """Test ScheduleCreate with invalid model config values."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Invalid temperature (too low)
        data = base_data.copy()
        data["agent_config_data"]["model"] = {"temperature": -0.1}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "temperature" in str(exc_info.value)
        
        # Invalid temperature (too high)
        data = base_data.copy()
        data["agent_config_data"]["model"] = {"temperature": 2.1}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "temperature" in str(exc_info.value)
        
        # Invalid max_tokens (zero)
        data = base_data.copy()
        data["agent_config_data"]["model"] = {"max_tokens": 0}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "max_tokens" in str(exc_info.value)
        
        # Invalid frequency_penalty (too low)
        data = base_data.copy()
        data["agent_config_data"]["model"] = {"frequency_penalty": -2.1}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "frequency_penalty" in str(exc_info.value)
        
        # Invalid top_p (too high)
        data = base_data.copy()
        data["agent_config_data"]["model"] = {"top_p": 1.1}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "top_p" in str(exc_info.value)
    
    def test_invalid_logging_config_values(self):
        """Test ScheduleCreate with invalid logging config values."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Invalid log_level
        data = base_data.copy()
        data["agent_config_data"]["logging"] = {"log_level": "INVALID"}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "log_level" in str(exc_info.value)
    
    def test_invalid_security_config_values(self):
        """Test ScheduleCreate with invalid security config values."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Invalid max_input_size_bytes (too small)
        data = base_data.copy()
        data["agent_config_data"]["security"] = {"max_input_size_bytes": 1023}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "max_input_size_bytes" in str(exc_info.value)
        
        # Invalid rate_limit_per_minute (too high)
        data = base_data.copy()
        data["agent_config_data"]["security"] = {"rate_limit_per_minute": 1001}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "rate_limit_per_minute" in str(exc_info.value)
        
        # Invalid rate_limit_per_minute (zero)
        data = base_data.copy()
        data["agent_config_data"]["security"] = {"rate_limit_per_minute": 0}
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "rate_limit_per_minute" in str(exc_info.value)
    
    def test_invalid_profile_and_performance_mode(self):
        """Test ScheduleCreate with invalid profile and performance mode values."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # Invalid profile
        data = base_data.copy()
        data["agent_config_data"]["profile"] = "invalid_profile"
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "profile" in str(exc_info.value)
        
        # Invalid performance_mode
        data = base_data.copy()
        data["agent_config_data"]["performance_mode"] = "invalid_mode"
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "performance_mode" in str(exc_info.value)
    
    def test_validation_with_none_values(self):
        """Test ScheduleCreate validation with None values for required fields."""
        base_data = ScheduleFixtures.valid_schedule_create_minimal()
        
        # None title
        data = base_data.copy()
        data["title"] = None
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "title" in str(exc_info.value)
        
        # None agent_config_data
        data = base_data.copy()
        data["agent_config_data"] = None
        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**data)
        assert "agent_config_data" in str(exc_info.value)


class TestScheduleUpdateModel:
    """Test ScheduleUpdate model with partial updates and validation."""
    
    def test_valid_partial_updates(self):
        """Test ScheduleUpdate with valid partial field updates."""
        # Update only title
        update = ScheduleUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None
        assert update.cron_expression is None
        assert update.enabled is None
        assert update.timezone is None
        assert update.agent_config_data is None
        
        # Update multiple fields
        update = ScheduleUpdate(
            title="New Title",
            description="New Description",
            enabled=False
        )
        assert update.title == "New Title"
        assert update.description == "New Description"
        assert update.enabled is False
        assert update.cron_expression is None
        
        # Update cron expression
        update = ScheduleUpdate(cron_expression="0 10 * * *")
        assert update.cron_expression == "0 10 * * *"
        
        # Update timezone
        update = ScheduleUpdate(timezone="America/New_York")
        assert update.timezone == "America/New_York"
    
    def test_valid_agent_config_update(self):
        """Test ScheduleUpdate with valid agent configuration updates."""
        agent_config = {
            "name": "updated_agent",
            "description": "Updated agent description",
            "job_data": {
                "prompt": "Updated prompt",
                "max_tokens": 2000
            },
            "execution": {
                "timeout_seconds": 600,
                "priority": 8
            }
        }
        
        update = ScheduleUpdate(agent_config_data=agent_config)
        assert update.agent_config_data.name == "updated_agent"
        assert update.agent_config_data.description == "Updated agent description"
        assert update.agent_config_data.job_data["prompt"] == "Updated prompt"
        assert update.agent_config_data.execution.timeout_seconds == 600
        assert update.agent_config_data.execution.priority == 8
    
    def test_all_fields_update(self):
        """Test ScheduleUpdate with all fields provided."""
        update_data = {
            "title": "Completely Updated Schedule",
            "description": "Completely updated description",
            "cron_expression": "0 */4 * * *",
            "enabled": False,
            "timezone": "Europe/London",
            "agent_config_data": {
                "name": "complete_update_agent",
                "profile": "quality",
                "performance_mode": "speed",
                "job_data": {
                    "prompt": "Complete update prompt"
                }
            }
        }
        
        update = ScheduleUpdate(**update_data)
        assert update.title == "Completely Updated Schedule"
        assert update.description == "Completely updated description"
        assert update.cron_expression == "0 */4 * * *"
        assert update.enabled is False
        assert update.timezone == "Europe/London"
        assert update.agent_config_data.name == "complete_update_agent"
    
    def test_empty_update(self):
        """Test ScheduleUpdate with no fields provided."""
        update = ScheduleUpdate()
        assert update.title is None
        assert update.description is None
        assert update.cron_expression is None
        assert update.enabled is None
        assert update.timezone is None
        assert update.agent_config_data is None
    
    def test_validation_errors_in_updates(self):
        """Test ScheduleUpdate validation errors."""
        # Empty title
        with pytest.raises(ValidationError) as exc_info:
            ScheduleUpdate(title="")
        assert "title" in str(exc_info.value)
        
        # Whitespace-only title
        with pytest.raises(ValidationError) as exc_info:
            ScheduleUpdate(title="   ")
        assert "title" in str(exc_info.value)
        
        # Invalid cron expression
        with pytest.raises(ValidationError) as exc_info:
            ScheduleUpdate(cron_expression="invalid_cron")
        assert "cron" in str(exc_info.value).lower()
        
        # Title too long
        with pytest.raises(ValidationError) as exc_info:
            ScheduleUpdate(title="x" * 201)
        assert "title" in str(exc_info.value)
        
        # Description too long
        with pytest.raises(ValidationError) as exc_info:
            ScheduleUpdate(description="x" * 1001)
        assert "description" in str(exc_info.value)
    
    def test_cron_expression_validation_in_updates(self):
        """Test cron expression validation in ScheduleUpdate."""
        # Valid cron expressions
        valid_expressions = [
            "0 9 * * *",
            "*/30 * * * *",
            "0 0 1 * *",
            "0 9-17 * * 1-5"
        ]
        
        for expr in valid_expressions:
            update = ScheduleUpdate(cron_expression=expr)
            assert update.cron_expression == expr
        
        # Invalid cron expressions
        invalid_expressions = [
            "",
            "invalid",
            "0 25 * * *",
            "0 * * * 8",
            "* * * * * *"
        ]
        
        for expr in invalid_expressions:
            with pytest.raises(ValidationError):
                ScheduleUpdate(cron_expression=expr)
    
    def test_optional_field_behavior(self):
        """Test that optional fields behave correctly in updates."""
        # Test that None is preserved for optional fields
        update = ScheduleUpdate(
            title="Test",
            description=None,
            timezone=None
        )
        assert update.title == "Test"
        assert update.description is None
        assert update.timezone is None
        
        # Test explicit empty string for description (should be allowed)
        update = ScheduleUpdate(description="")
        assert update.description == ""


class TestScheduleModel:
    """Test Schedule model methods and properties."""
    
    def test_update_next_run_time_method(self):
        """Test Schedule.update_next_run_time() method."""
        # Create a basic schedule
        schedule_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "timezone": "UTC",
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        schedule = Schedule(**schedule_data)
        
        # Test updating next run time
        next_run = schedule.update_next_run_time()
        
        assert isinstance(next_run, datetime)
        assert next_run.tzinfo == timezone.utc
        assert next_run.hour == 9
        assert next_run.minute == 0
        assert schedule.next_run == next_run
        
        # Test with timezone
        schedule.timezone = "America/New_York"
        next_run_ny = schedule.update_next_run_time()
        
        assert isinstance(next_run_ny, datetime)
        assert next_run_ny.tzinfo == timezone.utc
        assert schedule.next_run == next_run_ny
    
    def test_get_cron_description_method(self):
        """Test Schedule.get_cron_description() method."""
        schedule_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        schedule = Schedule(**schedule_data)
        description = schedule.get_cron_description()
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "9:00" in description or "9" in description
    
    def test_is_due_method(self):
        """Test Schedule.is_due() method."""
        schedule_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        schedule = Schedule(**schedule_data)
        
        # Test with no last run (should use reasonable default)
        is_due = schedule.is_due()
        assert isinstance(is_due, bool)
        
        # Test with recent last run (should not be due)
        schedule.last_run = datetime.now(timezone.utc)
        is_due = schedule.is_due()
        assert isinstance(is_due, bool)
        
        # Test with tolerance
        is_due_strict = schedule.is_due(tolerance_seconds=1)
        is_due_loose = schedule.is_due(tolerance_seconds=3600)
        assert isinstance(is_due_strict, bool)
        assert isinstance(is_due_loose, bool)
    
    def test_success_rate_property(self):
        """Test Schedule.success_rate property."""
        schedule_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Test with no executions
        schedule = Schedule(**schedule_data)
        assert schedule.success_rate == 0.0
        
        # Test with all successful executions
        schedule.total_executions = 10
        schedule.successful_executions = 10
        schedule.failed_executions = 0
        assert schedule.success_rate == 100.0
        
        # Test with partial success
        schedule.total_executions = 10
        schedule.successful_executions = 8
        schedule.failed_executions = 2
        assert schedule.success_rate == 80.0
        
        # Test with no successful executions
        schedule.total_executions = 5
        schedule.successful_executions = 0
        schedule.failed_executions = 5
        assert schedule.success_rate == 0.0
    
    def test_schedule_status_enum_values(self):
        """Test Schedule with different status enum values."""
        base_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Test each status value
        for status in ScheduleStatus:
            schedule_data = base_data.copy()
            schedule_data["status"] = status
            schedule = Schedule(**schedule_data)
            assert schedule.status == status
    
    def test_schedule_with_execution_history(self):
        """Test Schedule model with execution statistics."""
        schedule_data = {
            "id": "test-id",
            "user_id": "user-id",
            "title": "Test Schedule",
            "agent_name": "test_agent",
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "agent_config_data": AgentConfigurationData(
                name="test_agent",
                job_data={"prompt": "test"}
            ),
            "next_run": datetime.now(timezone.utc),
            "last_run": datetime.now(timezone.utc) - timedelta(days=1),
            "created_at": datetime.now(timezone.utc) - timedelta(days=30),
            "updated_at": datetime.now(timezone.utc),
            "total_executions": 30,
            "successful_executions": 28,
            "failed_executions": 2
        }
        
        schedule = Schedule(**schedule_data)
        
        assert schedule.total_executions == 30
        assert schedule.successful_executions == 28
        assert schedule.failed_executions == 2
        assert schedule.success_rate == pytest.approx(93.33, rel=1e-2)
        assert schedule.next_run is not None
        assert schedule.last_run is not None


class TestAgentConfigurationDataValidation:
    """Test AgentConfigurationData validation within schedule context."""
    
    def test_minimal_valid_agent_config(self):
        """Test AgentConfigurationData with minimal valid data."""
        config_data = {
            "name": "test_agent",
            "job_data": {"prompt": "Hello world"}
        }
        
        config = AgentConfigurationData(**config_data)
        
        assert config.name == "test_agent"
        assert config.job_data == {"prompt": "Hello world"}
        assert config.profile == AgentProfileEnum.BALANCED  # Default
        assert config.performance_mode == AgentPerformanceModeEnum.BALANCED  # Default
        assert config.enabled is True  # Default
        assert config.description is None  # Default
        assert config.result_format is None  # Default
        assert config.custom_settings == {}  # Default
    
    def test_complete_agent_config_validation(self):
        """Test AgentConfigurationData with all fields populated."""
        config_data = {
            "name": "comprehensive_agent",
            "description": "A comprehensive test agent",
            "profile": "quality",
            "performance_mode": "speed",
            "enabled": True,
            "result_format": "json",
            "execution": {
                "timeout_seconds": 1800,
                "max_retries": 5,
                "retry_delay_base": 2.5,
                "enable_caching": False,
                "cache_ttl_seconds": 7200,
                "priority": 9,
                "memory_limit_mb": 4096,
                "cpu_limit_percent": 90.0
            },
            "model": {
                "model_name": "gpt-4",
                "temperature": 0.2,
                "max_tokens": 8000,
                "top_p": 0.95,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.1,
                "stop_sequences": ["END", "STOP", "DONE"],
                "custom_parameters": {
                    "custom_setting": "value",
                    "numeric_setting": 42
                }
            },
            "logging": {
                "log_level": "DEBUG",
                "enable_performance_logging": True,
                "enable_debug_logging": True,
                "log_requests": True,
                "log_responses": True,
                "log_errors": True,
                "metrics_enabled": True,
                "trace_enabled": True
            },
            "security": {
                "enable_input_validation": True,
                "enable_output_sanitization": True,
                "max_input_size_bytes": 5242880,  # 5MB
                "max_output_size_bytes": 5242880,
                "allowed_domains": ["api.openai.com", "secure-api.com"],
                "blocked_keywords": ["malicious", "harmful", "dangerous"],
                "rate_limit_per_minute": 200
            },
            "job_data": {
                "prompt": "Complex processing task",
                "input_data": {
                    "source": "database",
                    "format": "json",
                    "filters": ["active", "recent"]
                },
                "output_requirements": {
                    "format": "structured",
                    "include_metadata": True,
                    "compression": "gzip"
                }
            },
            "custom_settings": {
                "advanced_features": {
                    "enable_experimental": True,
                    "beta_mode": False
                },
                "integrations": {
                    "webhook_url": "https://api.example.com/webhook",
                    "api_key_ref": "secret_key_123"
                }
            }
        }
        
        config = AgentConfigurationData(**config_data)
        
        # Verify basic fields
        assert config.name == "comprehensive_agent"
        assert config.description == "A comprehensive test agent"
        assert config.profile == AgentProfileEnum.QUALITY
        assert config.performance_mode == AgentPerformanceModeEnum.SPEED
        assert config.enabled is True
        assert config.result_format == "json"
        
        # Verify execution config
        assert config.execution.timeout_seconds == 1800
        assert config.execution.max_retries == 5
        assert config.execution.priority == 9
        assert config.execution.memory_limit_mb == 4096
        
        # Verify model config
        assert config.model.model_name == "gpt-4"
        assert config.model.temperature == 0.2
        assert config.model.max_tokens == 8000
        assert len(config.model.stop_sequences) == 3
        
        # Verify logging config
        assert config.logging.log_level == "DEBUG"
        assert config.logging.enable_debug_logging is True
        
        # Verify security config
        assert config.security.max_input_size_bytes == 5242880
        assert len(config.security.allowed_domains) == 2
        assert len(config.security.blocked_keywords) == 3
        
        # Verify job data and custom settings
        assert "input_data" in config.job_data
        assert "advanced_features" in config.custom_settings
    
    def test_agent_config_validation_errors(self):
        """Test AgentConfigurationData validation errors."""
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            AgentConfigurationData(job_data={"prompt": "test"})
        assert "name" in str(exc_info.value)
        
        # Missing job_data
        with pytest.raises(ValidationError) as exc_info:
            AgentConfigurationData(name="test")
        assert "job_data" in str(exc_info.value)
        
        # Empty name
        with pytest.raises(ValidationError) as exc_info:
            AgentConfigurationData(name="", job_data={"prompt": "test"})
        assert "name" in str(exc_info.value)
        
        # Name too long
        with pytest.raises(ValidationError) as exc_info:
            AgentConfigurationData(name="x" * 101, job_data={"prompt": "test"})
        assert "name" in str(exc_info.value)
        
        # Description too long
        with pytest.raises(ValidationError) as exc_info:
            AgentConfigurationData(
                name="test",
                description="x" * 501,
                job_data={"prompt": "test"}
            )
        assert "description" in str(exc_info.value)
    
    def test_agent_config_sub_configurations(self):
        """Test AgentConfigurationData sub-configuration validation."""
        base_config = {
            "name": "test_agent",
            "job_data": {"prompt": "test"}
        }
        
        # Test with custom execution config
        config_data = base_config.copy()
        config_data["execution"] = {
            "timeout_seconds": 600,
            "max_retries": 2,
            "priority": 7
        }
        config = AgentConfigurationData(**config_data)
        assert config.execution.timeout_seconds == 600
        assert config.execution.max_retries == 2
        assert config.execution.priority == 7
        # Other fields should have defaults
        assert config.execution.enable_caching is True
        assert config.execution.retry_delay_base == 2.0
        
        # Test with custom model config
        config_data = base_config.copy()
        config_data["model"] = {
            "temperature": 0.5,
            "max_tokens": 1500
        }
        config = AgentConfigurationData(**config_data)
        assert config.model.temperature == 0.5
        assert config.model.max_tokens == 1500
        # Other fields should have defaults
        assert config.model.top_p == 1.0
        assert config.model.frequency_penalty == 0.0
    
    def test_agent_config_with_schedule_create(self):
        """Test AgentConfigurationData integration with ScheduleCreate."""
        agent_config = {
            "name": "integration_test_agent",
            "description": "Agent for testing integration",
            "profile": "fast",
            "performance_mode": "speed",
            "job_data": {
                "prompt": "Integration test prompt",
                "parameters": {"test": True}
            },
            "execution": {"priority": 8},
            "model": {"temperature": 0.1}
        }
        
        schedule_data = {
            "title": "Integration Test Schedule",
            "agent_name": "integration_test_agent",
            "cron_expression": "0 12 * * *",
            "agent_config_data": agent_config
        }
        
        schedule = ScheduleCreate(**schedule_data)
        
        assert schedule.agent_config_data.name == "integration_test_agent"
        assert schedule.agent_config_data.profile == AgentProfileEnum.FAST
        assert schedule.agent_config_data.performance_mode == AgentPerformanceModeEnum.SPEED
        assert schedule.agent_config_data.execution.priority == 8
        assert schedule.agent_config_data.model.temperature == 0.1
        assert schedule.agent_config_data.job_data["parameters"]["test"] is True 