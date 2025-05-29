"""
Agent Configuration System for Easy Customization

This module provides a comprehensive configuration system for agents that allows:
- Per-agent configuration with inheritance
- Environment-based configuration overrides  
- Runtime configuration updates
- Validation and type checking
- Default fallbacks and profiles
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from pydantic import BaseModel, Field, validator

from config.environment import get_settings
from logging_system import get_logger

logger = get_logger(__name__)

class AgentProfile(str, Enum):
    """Predefined agent configuration profiles"""
    FAST = "fast"              # Fast execution, lower quality
    BALANCED = "balanced"      # Balanced speed and quality
    QUALITY = "quality"        # High quality, slower execution
    CUSTOM = "custom"          # Custom configuration

class AgentPerformanceMode(str, Enum):
    """Agent performance optimization modes"""
    SPEED = "speed"           # Prioritize speed over quality
    QUALITY = "quality"       # Prioritize quality over speed
    BALANCED = "balanced"     # Balance speed and quality
    POWER_SAVE = "power_save" # Conservative resource usage

@dataclass
class AgentExecutionConfig:
    """Configuration for agent execution behavior"""
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_base: float = 2.0
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    priority: int = 5
    memory_limit_mb: Optional[int] = None
    cpu_limit_percent: Optional[float] = None

@dataclass
class AgentModelConfig:
    """Configuration for AI model settings"""
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentLoggingConfig:
    """Configuration for agent logging and monitoring"""
    log_level: str = "INFO"
    enable_performance_logging: bool = True
    enable_debug_logging: bool = False
    log_requests: bool = True
    log_responses: bool = False
    log_errors: bool = True
    metrics_enabled: bool = True
    trace_enabled: bool = False

@dataclass
class AgentSecurityConfig:
    """Configuration for agent security settings"""
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    max_input_size_bytes: int = 1024 * 1024  # 1MB
    max_output_size_bytes: int = 1024 * 1024  # 1MB
    allowed_domains: List[str] = field(default_factory=list)
    blocked_keywords: List[str] = field(default_factory=list)
    rate_limit_per_minute: int = 60

@dataclass
class AgentConfig:
    """Comprehensive agent configuration"""
    # Basic agent settings
    name: str
    description: Optional[str] = None
    profile: AgentProfile = AgentProfile.BALANCED
    performance_mode: AgentPerformanceMode = AgentPerformanceMode.BALANCED
    enabled: bool = True
    
    # Sub-configurations
    execution: AgentExecutionConfig = field(default_factory=AgentExecutionConfig)
    model: AgentModelConfig = field(default_factory=AgentModelConfig)
    logging: AgentLoggingConfig = field(default_factory=AgentLoggingConfig)
    security: AgentSecurityConfig = field(default_factory=AgentSecurityConfig)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create configuration from dictionary"""
        # Handle nested dataclasses
        if 'execution' in data and isinstance(data['execution'], dict):
            data['execution'] = AgentExecutionConfig(**data['execution'])
        if 'model' in data and isinstance(data['model'], dict):
            data['model'] = AgentModelConfig(**data['model'])
        if 'logging' in data and isinstance(data['logging'], dict):
            data['logging'] = AgentLoggingConfig(**data['logging'])
        if 'security' in data and isinstance(data['security'], dict):
            data['security'] = AgentSecurityConfig(**data['security'])
        
        return cls(**data)

class AgentConfigManager:
    """
    Centralized agent configuration management system.
    
    Provides:
    - Configuration loading from files and environment
    - Runtime configuration updates
    - Profile-based defaults
    - Validation and type checking
    - Configuration inheritance and overrides
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing agent configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config/agents")
        self.configs: Dict[str, AgentConfig] = {}
        self.profiles: Dict[AgentProfile, Dict[str, Any]] = {}
        self.settings = get_settings()
        
        # Initialize default profiles
        self._initialize_default_profiles()
        
        # Load configurations
        self._load_configurations()
        
        logger.info(f"AgentConfigManager initialized with {len(self.configs)} configurations")
    
    def _initialize_default_profiles(self):
        """Initialize default configuration profiles"""
        self.profiles = {
            AgentProfile.FAST: {
                "execution": {
                    "timeout_seconds": 60,
                    "max_retries": 1,
                    "enable_caching": True,
                    "cache_ttl_seconds": 1800
                },
                "model": {
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                "logging": {
                    "log_level": "WARNING",
                    "enable_debug_logging": False,
                    "log_responses": False
                }
            },
            AgentProfile.BALANCED: {
                "execution": {
                    "timeout_seconds": 300,
                    "max_retries": 3,
                    "enable_caching": True,
                    "cache_ttl_seconds": 3600
                },
                "model": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "logging": {
                    "log_level": "INFO",
                    "enable_debug_logging": False,
                    "log_responses": False
                }
            },
            AgentProfile.QUALITY: {
                "execution": {
                    "timeout_seconds": 600,
                    "max_retries": 5,
                    "enable_caching": False,
                    "cache_ttl_seconds": 7200
                },
                "model": {
                    "temperature": 0.9,
                    "max_tokens": 4000
                },
                "logging": {
                    "log_level": "DEBUG",
                    "enable_debug_logging": True,
                    "log_responses": True
                }
            }
        }
    
    def _load_configurations(self):
        """Load agent configurations from files and environment"""
        try:
            # Load from config files
            if self.config_dir.exists():
                self._load_from_files()
            
            # Load from environment variables
            self._load_from_environment()
            
            # Apply profile defaults
            self._apply_profile_defaults()
            
        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}")
    
    def _load_from_files(self):
        """Load configurations from JSON/YAML files"""
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                agent_name = config_file.stem
                config = AgentConfig.from_dict({**data, "name": agent_name})
                self.configs[agent_name] = config
                
                logger.debug(f"Loaded configuration for agent: {agent_name}")
                
            except Exception as e:
                logger.error(f"Error loading config file {config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration overrides from environment variables"""
        # Pattern: AGENT_{AGENT_NAME}_{CONFIG_PATH}
        # Example: AGENT_TEXT_PROCESSING_EXECUTION_TIMEOUT_SECONDS=120
        
        for key, value in os.environ.items():
            if key.startswith("AGENT_"):
                try:
                    parts = key.split("_")
                    if len(parts) >= 4:
                        agent_name = parts[1].lower()
                        config_path = "_".join(parts[2:]).lower()
                        
                        # Parse value
                        parsed_value = self._parse_env_value(value)
                        
                        # Apply to configuration
                        self._set_config_value(agent_name, config_path, parsed_value)
                        
                except Exception as e:
                    logger.warning(f"Error parsing environment variable {key}: {e}")
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Boolean values
        if value.upper() in ("TRUE", "FALSE"):
            return value.upper() == "TRUE"
        
        # Numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON values
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # String value
        return value
    
    def _set_config_value(self, agent_name: str, config_path: str, value: Any):
        """Set a nested configuration value"""
        if agent_name not in self.configs:
            self.configs[agent_name] = AgentConfig(name=agent_name)
        
        config = self.configs[agent_name]
        path_parts = config_path.split("_")
        
        # Navigate to the correct config section
        current = config
        for part in path_parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return  # Invalid path
        
        # Set the value
        final_key = path_parts[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
            logger.debug(f"Set {agent_name}.{config_path} = {value}")
    
    def _apply_profile_defaults(self):
        """Apply profile defaults to configurations"""
        for agent_name, config in self.configs.items():
            if config.profile in self.profiles:
                profile_defaults = self.profiles[config.profile]
                self._merge_defaults(config, profile_defaults)
    
    def _merge_defaults(self, config: AgentConfig, defaults: Dict[str, Any]):
        """Merge profile defaults into configuration"""
        for section, values in defaults.items():
            if hasattr(config, section):
                section_config = getattr(config, section)
                for key, value in values.items():
                    if hasattr(section_config, key) and getattr(section_config, key) is None:
                        setattr(section_config, key, value)
    
    def get_config(self, agent_name: str) -> AgentConfig:
        """
        Get configuration for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentConfig instance with merged defaults
        """
        if agent_name in self.configs:
            return self.configs[agent_name]
        
        # Create default configuration
        config = AgentConfig(name=agent_name)
        self.configs[agent_name] = config
        
        logger.info(f"Created default configuration for agent: {agent_name}")
        return config
    
    def update_config(self, agent_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update configuration for an agent.
        
        Args:
            agent_name: Name of the agent
            updates: Configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_name not in self.configs:
                self.configs[agent_name] = AgentConfig(name=agent_name)
            
            config = self.configs[agent_name]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    config.custom_settings[key] = value
            
            logger.info(f"Updated configuration for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration for {agent_name}: {e}")
            return False
    
    def save_config(self, agent_name: str, config_file: Optional[str] = None) -> bool:
        """
        Save agent configuration to file.
        
        Args:
            agent_name: Name of the agent
            config_file: Optional file path (defaults to config_dir/agent_name.json)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_name not in self.configs:
                logger.warning(f"No configuration found for agent: {agent_name}")
                return False
            
            config = self.configs[agent_name]
            
            # Determine file path
            if config_file is None:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                config_file = self.config_dir / f"{agent_name}.json"
            
            # Save configuration
            with open(config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            logger.info(f"Saved configuration for agent {agent_name} to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration for {agent_name}: {e}")
            return False
    
    def list_configs(self) -> List[str]:
        """Get list of all configured agent names"""
        return list(self.configs.keys())
    
    def get_profile_defaults(self, profile: AgentProfile) -> Dict[str, Any]:
        """Get default settings for a profile"""
        return self.profiles.get(profile, {}).copy()
    
    def validate_config(self, config: AgentConfig) -> List[str]:
        """
        Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation
        if not config.name:
            errors.append("Agent name is required")
        
        # Execution validation
        if config.execution.timeout_seconds <= 0:
            errors.append("Execution timeout must be positive")
        
        if config.execution.max_retries < 0:
            errors.append("Max retries cannot be negative")
        
        # Model validation
        if config.model.temperature < 0 or config.model.temperature > 2:
            errors.append("Model temperature must be between 0 and 2")
        
        if config.model.max_tokens is not None and config.model.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        
        # Security validation
        if config.security.max_input_size_bytes <= 0:
            errors.append("Max input size must be positive")
        
        if config.security.rate_limit_per_minute <= 0:
            errors.append("Rate limit must be positive")
        
        return errors

# Global configuration manager instance
_config_manager: Optional[AgentConfigManager] = None

def get_agent_config_manager() -> AgentConfigManager:
    """Get or create the global agent configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager()
    return _config_manager

def get_agent_config(agent_name: str) -> AgentConfig:
    """
    Convenience function to get agent configuration.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        AgentConfig instance
    """
    manager = get_agent_config_manager()
    return manager.get_config(agent_name)

def update_agent_config(agent_name: str, updates: Dict[str, Any]) -> bool:
    """
    Convenience function to update agent configuration.
    
    Args:
        agent_name: Name of the agent
        updates: Configuration updates
        
    Returns:
        True if successful, False otherwise
    """
    manager = get_agent_config_manager()
    return manager.update_config(agent_name, updates) 