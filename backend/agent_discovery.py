"""
Agent Discovery System

This module provides automatic discovery and metadata extraction for agents
in the agents/ directory. Implements caching, lifecycle management, and 
graceful error handling to support the agent framework.
"""

import os
import inspect
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Type, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging
from enum import Enum

from agent import BaseAgent
from logging_system import get_logger

logger = get_logger(__name__)

class AgentEnvironment(str, Enum):
    """Agent environment enumeration"""
    DEV = "dev"
    TEST = "test" 
    PROD = "prod"
    ALL = "all"

class AgentLifecycleState(str, Enum):
    """Agent lifecycle state enumeration"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"

@dataclass
class AgentMetadata:
    """Agent metadata container with comprehensive agent information"""
    identifier: str
    name: str
    description: str
    class_name: str
    module_path: str
    agent_class: Optional[Type[BaseAgent]]
    lifecycle_state: AgentLifecycleState
    supported_environments: List[AgentEnvironment]
    version: str
    created_at: datetime
    last_updated: datetime
    load_error: Optional[str] = None
    metadata_extras: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result['created_at'] = self.created_at.isoformat()
        result['last_updated'] = self.last_updated.isoformat()
        # Remove agent_class from serialization
        result.pop('agent_class', None)
        return result

@dataclass 
class AgentDiscoveryCache:
    """Cache container for discovered agents with statistics"""
    agents: Dict[str, AgentMetadata]
    last_scan: datetime
    scan_duration: float
    total_agents: int
    failed_loads: int

class AgentDiscoverySystem:
    """
    Automatic agent discovery system that scans the agents/ directory
    and extracts metadata from BaseAgent subclasses.
    """
    
    def __init__(
        self, 
        agents_directory: str = "agents",
        cache_ttl_minutes: int = 30,
        auto_scan_on_init: bool = True
    ):
        """
        Initialize the agent discovery system.
        
        Args:
            agents_directory: Directory to scan for agents
            cache_ttl_minutes: Cache time-to-live in minutes
            auto_scan_on_init: Whether to scan on initialization
        """
        self.agents_directory = agents_directory
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.auto_scan_on_init = auto_scan_on_init
        
        # Cache management
        self._cache: Optional[AgentDiscoveryCache] = None
        self._scan_lock = False
        
        # Configuration
        self.current_environment = self._detect_current_environment()
        
        logger.info(
            f"Initialized AgentDiscoverySystem",
            agents_directory=agents_directory,
            cache_ttl_minutes=cache_ttl_minutes,
            current_environment=self.current_environment
        )
        
        if auto_scan_on_init:
            try:
                self.discover_agents()
            except Exception as e:
                logger.error(f"Failed initial agent discovery: {e}")
    
    def _detect_current_environment(self) -> AgentEnvironment:
        """Detect current runtime environment"""
        env = os.getenv("ENVIRONMENT", "dev").lower()
        try:
            return AgentEnvironment(env)
        except ValueError:
            logger.warning(f"Unknown environment '{env}', defaulting to dev")
            return AgentEnvironment.DEV
    
    def _is_cache_valid(self) -> bool:
        """Check if current cache is still valid"""
        if not self._cache:
            return False
        
        cache_age = datetime.now(timezone.utc) - self._cache.last_scan
        return cache_age < self.cache_ttl
    
    def _derive_agent_identifier(self, class_name: str) -> str:
        """
        Convert agent class name to identifier using smart naming logic.
        
        Supports multiple naming patterns:
        - CamelCase: SimpleExampleAgent -> simple_example
        - PascalCase: MyCustomAgent -> my_custom  
        - Underscore: Custom_Research_Agent -> custom_research
        
        Examples:
            SimpleExampleAgent -> simple_example
            MyCustomAgent -> my_custom
        """
        # Remove 'Agent' suffix if present
        if class_name.endswith('Agent'):
            class_name = class_name[:-5]
        
        # Convert CamelCase to snake_case
        result = ""
        for i, char in enumerate(class_name):
            if i > 0 and char.isupper():
                result += "_"
            result += char.lower()
        
        return result
    
    def _get_agent_lifecycle_config(self, agent_class: Type[BaseAgent]) -> Dict[str, Any]:
        """Get agent lifecycle configuration from class metadata"""
        config = {
            'lifecycle_state': AgentLifecycleState.ENABLED,
            'supported_environments': [AgentEnvironment.ALL],
            'version': '1.0.0'
        }
        
        # Check for class-level configuration
        if hasattr(agent_class, '_agent_config'):
            class_config = agent_class._agent_config
            if isinstance(class_config, dict):
                config.update(class_config)
        
        # Check for environment-specific configuration
        if hasattr(agent_class, '_environments'):
            config['supported_environments'] = agent_class._environments
        
        # Check for version information
        if hasattr(agent_class, '__version__'):
            config['version'] = agent_class.__version__
        elif hasattr(agent_class, '_version'):
            config['version'] = agent_class._version
        
        return config
    
    def _load_agent_module(self, file_path: Path) -> Optional[Type[BaseAgent]]:
        """Load agent module and extract BaseAgent subclass"""
        try:
            # Create module name from file path
            module_name = file_path.stem
            if module_name.startswith('__'):
                return None  # Skip __init__ and __pycache__ files
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find BaseAgent subclasses in the module
            agent_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != BaseAgent and 
                    issubclass(obj, BaseAgent) and 
                    obj.__module__ == module.__name__):
                    agent_classes.append(obj)
            
            if len(agent_classes) == 1:
                return agent_classes[0]
            elif len(agent_classes) > 1:
                logger.warning(f"Multiple agent classes found in {file_path}, using first: {agent_classes[0].__name__}")
                return agent_classes[0]
            else:
                logger.debug(f"No agent classes found in {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load agent module {file_path}: {e}")
            return None
    
    def _scan_agents_directory(self) -> Dict[str, AgentMetadata]:
        """Scan the agents directory and extract metadata"""
        agents = {}
        failed_loads = 0
        
        agents_path = Path(self.agents_directory)
        if not agents_path.exists():
            logger.warning(f"Agents directory not found: {agents_path}")
            return agents
        
        logger.info(f"Scanning agents directory: {agents_path}")
        
        # Scan Python files in agents directory
        for file_path in agents_path.glob("*.py"):
            if file_path.name.startswith('__'):
                continue
                
            try:
                agent_class = self._load_agent_module(file_path)
                if not agent_class:
                    continue
                
                # Extract metadata
                identifier = self._derive_agent_identifier(agent_class.__name__)
                lifecycle_config = self._get_agent_lifecycle_config(agent_class)
                
                # Create metadata object
                metadata = AgentMetadata(
                    identifier=identifier,
                    name=getattr(agent_class, 'name', agent_class.__name__),
                    description=getattr(agent_class, '__doc__', '') or f"Agent: {agent_class.__name__}",
                    class_name=agent_class.__name__,
                    module_path=str(file_path),
                    agent_class=agent_class,
                    lifecycle_state=lifecycle_config.get('lifecycle_state', AgentLifecycleState.ENABLED),
                    supported_environments=lifecycle_config.get('supported_environments', [AgentEnvironment.ALL]),
                    version=lifecycle_config.get('version', '1.0.0'),
                    created_at=datetime.now(timezone.utc),
                    last_updated=datetime.now(timezone.utc),
                    metadata_extras=lifecycle_config.get('metadata_extras', {})
                )
                
                agents[identifier] = metadata
                logger.info(f"Discovered agent: {identifier} ({agent_class.__name__})")
                
            except Exception as e:
                failed_loads += 1
                error_msg = f"Failed to process agent file {file_path}: {e}"
                logger.error(error_msg)
                
                # Create error metadata entry
                identifier = f"error_{file_path.stem}"
                agents[identifier] = AgentMetadata(
                    identifier=identifier,
                    name=f"Failed: {file_path.stem}",
                    description="Agent failed to load",
                    class_name=file_path.stem,
                    module_path=str(file_path),
                    agent_class=None,
                    lifecycle_state=AgentLifecycleState.DISABLED,
                    supported_environments=[],
                    version="0.0.0",
                    created_at=datetime.now(timezone.utc),
                    last_updated=datetime.now(timezone.utc),
                    load_error=error_msg
                )
        
        logger.info(f"Agent discovery completed: {len(agents)} agents found, {failed_loads} failed loads")
        return agents
    
    def discover_agents(self, force_refresh: bool = False) -> Dict[str, AgentMetadata]:
        """
        Discover agents in the agents directory.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Dictionary of agent metadata keyed by agent identifier
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached agent discovery results")
            return self._cache.agents
        
        if self._scan_lock:
            logger.warning("Agent discovery already in progress")
            return self._cache.agents if self._cache else {}
        
        try:
            self._scan_lock = True
            start_time = datetime.now(timezone.utc)
            
            logger.info("Starting agent discovery scan")
            agents = self._scan_agents_directory()
            
            scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            failed_loads = sum(1 for agent in agents.values() if agent.load_error)
            
            # Update cache
            self._cache = AgentDiscoveryCache(
                agents=agents,
                last_scan=datetime.now(timezone.utc),
                scan_duration=scan_duration,
                total_agents=len(agents),
                failed_loads=failed_loads
            )
            
            logger.info(
                f"Agent discovery completed",
                total_agents=len(agents),
                failed_loads=failed_loads,
                scan_duration=scan_duration
            )
            
            return agents
            
        finally:
            self._scan_lock = False
    
    def get_agent_metadata(self, identifier: str) -> Optional[AgentMetadata]:
        """Get metadata for a specific agent"""
        agents = self.discover_agents()
        return agents.get(identifier)
    
    def get_agents_by_environment(self, environment: AgentEnvironment = None) -> Dict[str, AgentMetadata]:
        """Get agents filtered by environment"""
        if environment is None:
            environment = self.current_environment
            
        agents = self.discover_agents()
        filtered_agents = {}
        
        for identifier, metadata in agents.items():
            if (AgentEnvironment.ALL in metadata.supported_environments or 
                environment in metadata.supported_environments):
                filtered_agents[identifier] = metadata
        
        return filtered_agents
    
    def get_enabled_agents(self) -> Dict[str, AgentMetadata]:
        """Get only enabled agents in current environment"""
        agents = self.get_agents_by_environment()
        return {
            identifier: metadata
            for identifier, metadata in agents.items()
            if metadata.lifecycle_state == AgentLifecycleState.ENABLED and not metadata.load_error
        }
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery system statistics"""
        if not self._cache:
            return {
                "cache_status": "empty",
                "last_scan": None,
                "total_agents": 0,
                "enabled_agents": 0,
                "failed_loads": 0
            }
        
        enabled_count = len(self.get_enabled_agents())
        
        return {
            "cache_status": "valid" if self._is_cache_valid() else "expired",
            "last_scan": self._cache.last_scan.isoformat(),
            "scan_duration": self._cache.scan_duration,
            "total_agents": self._cache.total_agents,
            "enabled_agents": enabled_count,
            "failed_loads": self._cache.failed_loads,
            "current_environment": self.current_environment.value,
            "cache_ttl_minutes": int(self.cache_ttl.total_seconds() / 60)
        }
    
    def invalidate_cache(self) -> None:
        """Invalidate the current cache"""
        self._cache = None
        logger.info("Agent discovery cache invalidated")

# Global instance
_discovery_system: Optional[AgentDiscoverySystem] = None

def get_agent_discovery_system() -> AgentDiscoverySystem:
    """Get the global agent discovery system instance"""
    global _discovery_system
    if _discovery_system is None:
        _discovery_system = AgentDiscoverySystem()
    return _discovery_system 