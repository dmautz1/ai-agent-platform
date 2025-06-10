"""
Agent Configuration Compatibility Layer

This module provides compatibility imports for the test suite.
Re-exports agent configuration classes with the expected names.
"""

from .agent_config import (
    AgentConfig,
    AgentProfile,
    AgentPerformanceMode as PerformanceMode,
    AgentExecutionConfig,
    AgentModelConfig,
    AgentLoggingConfig,
    AgentSecurityConfig,
    AgentConfigManager,
    get_agent_config_manager,
    get_agent_config,
    update_agent_config
)

# Add compatibility for profile values that tests expect
AgentProfile.standard = AgentProfile.BALANCED  # Compatibility alias
AgentProfile.high_performance = AgentProfile.QUALITY  # Compatibility alias
PerformanceMode.standard = PerformanceMode.BALANCED  # Compatibility alias
PerformanceMode.high_throughput = PerformanceMode.SPEED  # Compatibility alias

# Export all the classes that tests might need
__all__ = [
    'AgentConfig',
    'AgentProfile',
    'PerformanceMode',
    'AgentExecutionConfig',
    'AgentModelConfig',
    'AgentLoggingConfig',
    'AgentSecurityConfig',
    'AgentConfigManager',
    'get_agent_config_manager',
    'get_agent_config',
    'update_agent_config'
] 