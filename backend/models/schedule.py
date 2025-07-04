"""
Pydantic models for Schedule management in the AI Agent Platform.

Provides models for:
- Schedule creation, updates, and responses
- Agent configuration data validation
- Cron expression validation using croniter
- Next run time calculation with timezone support

These models integrate with the existing job system and agent configuration
framework to provide reliable scheduled agent execution.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

# Import cron utilities
from utils.cron_utils import CronUtils, CronValidationError

class ScheduleStatus(str, Enum):
    """Schedule status enumeration"""
    enabled = "enabled"
    disabled = "disabled"
    paused = "paused"
    error = "error"

class ExecutionSource(str, Enum):
    """Job execution source enumeration"""
    manual = "manual"
    scheduled = "scheduled"

# Agent Configuration Validation Models
class AgentExecutionConfigData(BaseModel):
    """Validation model for agent execution configuration"""
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Execution timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_base: float = Field(default=2.0, ge=0.1, le=60.0, description="Base delay for exponential backoff")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    cache_ttl_seconds: int = Field(default=3600, ge=0, description="Cache time-to-live in seconds")
    priority: int = Field(default=5, ge=0, le=10, description="Execution priority")
    memory_limit_mb: Optional[int] = Field(default=None, ge=1, description="Memory limit in MB")
    cpu_limit_percent: Optional[float] = Field(default=None, ge=0.1, le=100.0, description="CPU usage limit percentage")

class AgentModelConfigData(BaseModel):
    """Validation model for agent model configuration"""
    model_name: Optional[str] = Field(default=None, description="AI model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop_sequences: List[str] = Field(default_factory=list, description="Stop sequences for generation")
    custom_parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom model parameters")

class AgentLoggingConfigData(BaseModel):
    """Validation model for agent logging configuration"""
    log_level: str = Field(default="INFO", description="Logging level", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    enable_performance_logging: bool = Field(default=True, description="Enable performance metrics logging")
    enable_debug_logging: bool = Field(default=False, description="Enable detailed debug logging")
    log_requests: bool = Field(default=True, description="Log incoming requests")
    log_responses: bool = Field(default=False, description="Log outgoing responses")
    log_errors: bool = Field(default=True, description="Log error messages")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    trace_enabled: bool = Field(default=False, description="Enable tracing")

class AgentSecurityConfigData(BaseModel):
    """Validation model for agent security configuration"""
    enable_input_validation: bool = Field(default=True, description="Enable input validation")
    enable_output_sanitization: bool = Field(default=True, description="Enable output sanitization")
    max_input_size_bytes: int = Field(default=1024*1024, ge=1024, description="Maximum input size in bytes")
    max_output_size_bytes: int = Field(default=1024*1024, ge=1024, description="Maximum output size in bytes")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for requests")
    blocked_keywords: List[str] = Field(default_factory=list, description="Blocked keywords in input")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000, description="Rate limit per minute")

class AgentProfileEnum(str, Enum):
    """Agent profile enumeration"""
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"
    CUSTOM = "custom"

class AgentPerformanceModeEnum(str, Enum):
    """Agent performance mode enumeration"""
    SPEED = "speed"
    QUALITY = "quality"
    BALANCED = "balanced"
    POWER_SAVE = "power_save"

class AgentConfigurationData(BaseModel):
    """Complete agent configuration validation model for schedules"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(default=None, max_length=500, description="Agent description")
    profile: AgentProfileEnum = Field(default=AgentProfileEnum.BALANCED, description="Agent performance profile")
    performance_mode: AgentPerformanceModeEnum = Field(default=AgentPerformanceModeEnum.BALANCED, description="Performance optimization mode")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    result_format: Optional[str] = Field(default=None, description="Expected result format")
    
    # Sub-configurations
    execution: AgentExecutionConfigData = Field(default_factory=AgentExecutionConfigData, description="Execution configuration")
    model: AgentModelConfigData = Field(default_factory=AgentModelConfigData, description="Model configuration")
    logging: AgentLoggingConfigData = Field(default_factory=AgentLoggingConfigData, description="Logging configuration")
    security: AgentSecurityConfigData = Field(default_factory=AgentSecurityConfigData, description="Security configuration")
    
    # Job data and custom settings
    job_data: Dict[str, Any] = Field(..., description="Job data to be passed to the agent")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration settings")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate agent name format"""
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "simple_prompt",
                "description": "Simple prompt processing agent",
                "profile": "balanced",
                "performance_mode": "balanced",
                "enabled": True,
                "result_format": "markdown",
                "execution": {
                    "timeout_seconds": 300,
                    "max_retries": 3,
                    "enable_caching": True
                },
                "model": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "job_data": {
                    "prompt": "Hello, world!",
                    "max_tokens": 1000
                },
                "custom_settings": {}
            }
        }
    )

# Schedule Models
class ScheduleBase(BaseModel):
    """Base schedule model with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Schedule title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Schedule description")
    agent_name: str = Field(..., min_length=1, max_length=100, description="Target agent identifier")
    cron_expression: str = Field(..., min_length=1, max_length=100, description="Cron expression for scheduling")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    timezone: Optional[str] = Field(default=None, max_length=100, description="Timezone for cron expression (e.g., 'America/New_York')")
    agent_config_data: AgentConfigurationData = Field(..., description="Complete agent configuration and job data")

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v):
        """Validate cron expression using croniter"""
        if not v or not v.strip():
            raise ValueError('Cron expression cannot be empty')
        
        try:
            # Use croniter for comprehensive validation
            CronUtils.validate_cron_expression(v.strip())
            return v.strip()
        except CronValidationError as e:
            raise ValueError(str(e))

    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v):
        """Validate agent name format"""
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate schedule title"""
        if not v or not v.strip():
            raise ValueError('Schedule title cannot be empty')
        return v.strip()

class ScheduleCreate(ScheduleBase):
    """Model for creating new schedules"""
    
    @model_validator(mode='after')
    def set_defaults_from_agent_name(self):
        """Set default title and description based on agent name if not provided"""
        if not self.description:
            self.description = f"{self.agent_name} scheduled execution"
        return self

    def get_next_run_time(self, timezone_str: Optional[str] = None) -> datetime:
        """Calculate the next run time for this schedule"""
        try:
            # Use the schedule's timezone if not specified
            tz = timezone_str or self.timezone
            return CronUtils.get_next_run_time(self.cron_expression, timezone_str=tz)
        except CronValidationError as e:
            raise ValueError(f"Could not calculate next run time: {str(e)}")

    def get_cron_description(self) -> str:
        """Get human-readable description of the cron expression"""
        try:
            return CronUtils.describe_cron_expression(self.cron_expression)
        except CronValidationError:
            return f"Cron expression: {self.cron_expression}"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Daily Report Generation",
                "description": "Generate daily reports every morning at 9 AM",
                "agent_name": "report_generator",
                "cron_expression": "0 9 * * *",
                "enabled": True,
                "agent_config_data": {
                    "name": "report_generator",
                    "description": "Generates daily reports",
                    "profile": "balanced",
                    "performance_mode": "balanced",
                    "enabled": True,
                    "result_format": "pdf",
                    "job_data": {
                        "report_type": "daily",
                        "include_charts": True
                    }
                }
            }
        }
    )

class ScheduleUpdate(BaseModel):
    """Model for updating existing schedules"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Schedule title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Schedule description")
    cron_expression: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Cron expression for scheduling")
    enabled: Optional[bool] = Field(default=None, description="Whether schedule is enabled")
    timezone: Optional[str] = Field(default=None, max_length=100, description="Timezone for cron expression (e.g., 'America/New_York')")
    agent_config_data: Optional[AgentConfigurationData] = Field(default=None, description="Complete agent configuration and job data")

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v):
        """Validate cron expression using croniter"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Cron expression cannot be empty')
            
            try:
                # Use croniter for comprehensive validation
                CronUtils.validate_cron_expression(v.strip())
                return v.strip()
            except CronValidationError as e:
                raise ValueError(str(e))
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate schedule title"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Schedule title cannot be empty')
        return v.strip() if v else v

class Schedule(ScheduleBase):
    """Complete schedule model for responses"""
    id: str = Field(..., description="Schedule UUID")
    user_id: str = Field(..., description="Owner user ID")
    status: ScheduleStatus = Field(default=ScheduleStatus.enabled, description="Schedule status")
    next_run: Optional[datetime] = Field(default=None, description="Next scheduled execution time")
    last_run: Optional[datetime] = Field(default=None, description="Last execution time")
    created_at: datetime = Field(..., description="Schedule creation timestamp")
    updated_at: datetime = Field(..., description="Schedule last update timestamp")
    total_executions: int = Field(default=0, description="Total number of executions")
    successful_executions: int = Field(default=0, description="Number of successful executions")
    failed_executions: int = Field(default=0, description="Number of failed executions")

    def update_next_run_time(self, timezone_str: Optional[str] = None) -> datetime:
        """Update and return the next run time for this schedule"""
        try:
            # Use the schedule's timezone if not specified
            tz = timezone_str or self.timezone
            next_time = CronUtils.get_next_run_time(self.cron_expression, timezone_str=tz)
            self.next_run = next_time
            return next_time
        except CronValidationError as e:
            raise ValueError(f"Could not calculate next run time: {str(e)}")

    def get_cron_description(self) -> str:
        """Get human-readable description of the cron expression"""
        try:
            return CronUtils.describe_cron_expression(self.cron_expression)
        except CronValidationError:
            return f"Cron expression: {self.cron_expression}"

    def is_due(self, tolerance_seconds: int = 60) -> bool:
        """Check if this schedule is due to run"""
        try:
            return CronUtils.is_due(self.cron_expression, self.last_run, tolerance_seconds)
        except Exception:
            return False

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user_123",
                "title": "Daily Report Generation",
                "description": "Generate daily reports every morning at 9 AM",
                "agent_name": "report_generator",
                "cron_expression": "0 9 * * *",
                "enabled": True,
                "status": "enabled",
                "next_run": "2024-01-02T09:00:00Z",
                "last_run": "2024-01-01T09:00:00Z",
                "created_at": "2024-01-01T08:00:00Z",
                "updated_at": "2024-01-01T08:00:00Z",
                "total_executions": 1,
                "successful_executions": 1,
                "failed_executions": 0,
                "agent_config_data": {
                    "name": "report_generator",
                    "description": "Generates daily reports",
                    "profile": "balanced",
                    "performance_mode": "balanced",
                    "enabled": True,
                    "result_format": "pdf",
                    "job_data": {
                        "report_type": "daily",
                        "include_charts": True
                    }
                }
            }
        }
    )

class ScheduleStats(BaseModel):
    """Schedule statistics model"""
    total_schedules: int = Field(..., description="Total number of schedules")
    enabled_schedules: int = Field(..., description="Number of enabled schedules")
    disabled_schedules: int = Field(..., description="Number of disabled schedules")
    paused_schedules: int = Field(..., description="Number of paused schedules")
    error_schedules: int = Field(..., description="Number of schedules with errors")
    total_executions: int = Field(..., description="Total executions across all schedules")
    successful_executions: int = Field(..., description="Total successful executions")
    failed_executions: int = Field(..., description="Total failed executions")
    success_rate: float = Field(..., description="Overall success rate percentage")
    next_executions: List[Dict[str, Any]] = Field(default_factory=list, description="Upcoming executions")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_schedules": 10,
                "enabled_schedules": 8,
                "disabled_schedules": 1,
                "paused_schedules": 1,
                "error_schedules": 0,
                "total_executions": 150,
                "successful_executions": 142,
                "failed_executions": 8,
                "success_rate": 94.7,
                "next_executions": [
                    {
                        "schedule_id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Daily Report Generation",
                        "next_run": "2024-01-02T09:00:00Z"
                    }
                ]
            }
        }
    )

class ScheduleExecutionHistory(BaseModel):
    """Model for schedule execution history"""
    schedule_id: str = Field(..., description="Schedule UUID")
    job_id: str = Field(..., description="Job UUID")
    execution_time: datetime = Field(..., description="Execution timestamp")
    status: str = Field(..., description="Execution status")
    duration_seconds: Optional[float] = Field(default=None, description="Execution duration in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    result_preview: Optional[str] = Field(default=None, max_length=500, description="Preview of execution result")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schedule_id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "job_456",
                "execution_time": "2024-01-01T09:00:00Z",
                "status": "completed",
                "duration_seconds": 45.2,
                "error_message": None,
                "result_preview": "Daily report generated successfully with 25 records processed..."
            }
        }
    ) 