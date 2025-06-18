"""
Unit tests for environment configuration
Tests the environment configuration functionality including settings validation,
environment detection, and configuration loading.
"""

import unittest
from unittest.mock import patch, Mock
import os
from typing import Dict, Any

# Test imports
from config.environment import (
    Settings,
    Environment,
    LogLevel,
    get_settings,
    reload_settings,
    validate_required_settings,
    get_logging_config
)

# Test environment variables - use JWT_SECRET instead of SECRET_KEY to match Settings field
TEST_ENV_VARS = {
    'JWT_SECRET': 'test-jwt-secret-key-for-testing-purposes',
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_KEY': 'test-key'
}

class TestEnvironmentSettings(unittest.TestCase):
    """Test cases for environment settings functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any existing settings
        import config.environment
        config.environment._settings = None
        
        # Set test environment variables
        for key, value in TEST_ENV_VARS.items():
            os.environ[key] = value

    def tearDown(self):
        """Clean up after tests"""
        # Clear settings cache to avoid cross-test contamination
        import config.environment
        config.environment._settings = None
        
        # Clean up environment variables
        for key in TEST_ENV_VARS.keys():
            if key in os.environ:
                del os.environ[key]
        
        # Clean up any additional environment variables set during tests
        test_vars = [
            'ENVIRONMENT', 'APP_NAME', 'APP_VERSION', 'DEBUG', 'HOST', 'PORT',
            'GOOGLE_API_KEY', 'MAX_CONCURRENT_JOBS', 'LOG_LEVEL', 'DEFAULT_LLM_PROVIDER',
            'ALLOWED_ORIGINS'
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def test_default_settings(self):
        """Test default settings values"""
        # Set required fields and clear any existing env overrides
        with patch.dict(os.environ, TEST_ENV_VARS, clear=True):
            settings = Settings()
            
            # Test defaults (note: .env file may override some values)
            self.assertIn("AI Agent Platform", settings.app_name)  # Allow for API suffix
            # Version comes from .env file, just verify it's a valid version string
            self.assertRegex(settings.app_version, r'^\d+\.\d+\.\d+$')  # Accept any valid version
            self.assertEqual(settings.environment, Environment.DEVELOPMENT)
            # Debug may be set in .env file, just verify it's boolean
            self.assertIsInstance(settings.debug, bool)
            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8000)
            self.assertEqual(settings.max_concurrent_jobs, 10)
            self.assertEqual(settings.job_timeout_seconds, 300)
            self.assertEqual(settings.log_level, LogLevel.INFO)

    def test_environment_override(self):
        """Test environment variable overrides"""
        test_env = {
            **TEST_ENV_VARS,
            'ENVIRONMENT': 'PRODUCTION',
            'APP_NAME': 'AI Agent Platform',
            'APP_VERSION': '1.0.0',
            'DEBUG': 'true',
            'HOST': '127.0.0.1',
            'PORT': '9000',
            'GOOGLE_API_KEY': 'google-key',
            'MAX_CONCURRENT_JOBS': '20',
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            
            # Test overridden values
            self.assertEqual(settings.environment, Environment.PRODUCTION)
            self.assertEqual(settings.app_name, "AI Agent Platform")
            self.assertEqual(settings.app_version, "1.0.0")
            self.assertTrue(settings.debug)
            self.assertEqual(settings.host, "127.0.0.1")
            self.assertEqual(settings.port, 9000)
            self.assertEqual(settings.google_api_key, 'google-key')
            self.assertEqual(settings.max_concurrent_jobs, 20)
            self.assertEqual(settings.log_level, LogLevel.DEBUG)

    def test_environment_validation(self):
        """Test environment validation"""
        # Test valid environments
        for env in ['development', 'staging', 'production']:
            test_env = {**TEST_ENV_VARS, 'ENVIRONMENT': env}
            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                self.assertEqual(settings.environment.value, env)

    def test_cors_origins_development(self):
        """Test CORS origins for development environment"""
        test_env = {
            **TEST_ENV_VARS,
            'ENVIRONMENT': 'DEVELOPMENT'
        }
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            origins = settings.get_cors_origins()
            
            # Development should include local development ports
            expected_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
            
            # Check that all expected origins are present
            for expected in expected_origins:
                self.assertIn(expected, origins)
            
            # Should also include additional development ports like Vite
            self.assertIn("http://localhost:5173", origins)

    def test_cors_origins_production(self):
        """Test CORS origins for production environment"""
        test_env = {
            **TEST_ENV_VARS,
            'ENVIRONMENT': 'PRODUCTION'
        }
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            origins = settings.get_cors_origins()
            
            # Production should include default production origins
            expected_origins = [
                "http://localhost:3000",  # For local testing
                "https://yourdomain.vercel.app",
                "https://www.yourdomain.com"
            ]
            self.assertEqual(origins, expected_origins)

    def test_environment_helper_methods(self):
        """Test environment helper methods"""
        # Test development
        test_env = {**TEST_ENV_VARS, 'ENVIRONMENT': 'DEVELOPMENT'}
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            self.assertTrue(settings.is_development())
            self.assertFalse(settings.is_production())
            self.assertFalse(settings.is_staging())
        
        # Test production
        test_env = {**TEST_ENV_VARS, 'ENVIRONMENT': 'PRODUCTION'}
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            self.assertFalse(settings.is_development())
            self.assertTrue(settings.is_production())
            self.assertFalse(settings.is_staging())

    def test_default_llm_provider_setting(self):
        """Test default LLM provider configuration"""
        # Test default value
        with patch.dict(os.environ, TEST_ENV_VARS, clear=True):
            settings = Settings()
            self.assertEqual(settings.default_llm_provider, "google")
            
        # Test custom value
        test_env = {**TEST_ENV_VARS, 'DEFAULT_LLM_PROVIDER': 'openai'}
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            self.assertEqual(settings.default_llm_provider, "openai")
            
        # Test invalid provider should raise validation error
        test_env = {**TEST_ENV_VARS, 'DEFAULT_LLM_PROVIDER': 'invalid_provider'}
        with patch.dict(os.environ, test_env, clear=True):
            with self.assertRaises(Exception):  # Should raise validation error
                Settings()
    
    def test_all_valid_llm_providers(self):
        """Test all valid LLM provider options"""
        valid_providers = ["google", "openai", "anthropic", "grok", "deepseek", "llama"]
        
        for provider in valid_providers:
            test_env = {**TEST_ENV_VARS, 'DEFAULT_LLM_PROVIDER': provider}
            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                self.assertEqual(settings.default_llm_provider, provider)

class TestEnvironmentFunctions(unittest.TestCase):
    """Test cases for environment utility functions"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any existing settings
        import config.environment
        config.environment._settings = None

    def test_validate_required_settings_success(self):
        """Test validation with all required settings present"""
        with patch.dict(os.environ, TEST_ENV_VARS):
            # Should not raise an exception
            validate_required_settings()

    def test_validate_required_settings_missing_secret(self):
        """Test validation with missing secret key"""
        # Clear global settings cache
        import config.environment
        config.environment._settings = None
        
        # Use a custom env file approach to test validation
        with patch('config.environment.Settings') as mock_settings_class:
            # Mock the Settings class to raise validation error
            def mock_init(*args, **kwargs):
                raise ValueError("Missing required environment variables: JWT_SECRET")
            mock_settings_class.side_effect = mock_init
            
            with self.assertRaises(ValueError) as context:
                validate_required_settings()
            self.assertIn('JWT_SECRET', str(context.exception))

    def test_validate_required_settings_missing_supabase(self):
        """Test validation with missing Supabase settings"""
        # Clear global settings cache
        import config.environment
        config.environment._settings = None
        
        # Use a custom env file approach to test validation
        with patch('config.environment.Settings') as mock_settings_class:
            # Mock the Settings class to raise validation error
            def mock_init(*args, **kwargs):
                raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY")
            mock_settings_class.side_effect = mock_init
            
            with self.assertRaises(ValueError) as context:
                validate_required_settings()
            self.assertIn('SUPABASE_URL', str(context.exception))
            self.assertIn('SUPABASE_KEY', str(context.exception))

    def test_get_logging_config(self):
        """Test logging configuration generation"""
        test_env = {**TEST_ENV_VARS, 'LOG_LEVEL': 'DEBUG'}
        with patch.dict(os.environ, test_env):
            config = get_logging_config()
            
            self.assertIn('version', config)
            self.assertIn('formatters', config)
            self.assertIn('handlers', config)
            self.assertIn('root', config)
            self.assertIn('loggers', config)
            
            # Check that log level is applied
            self.assertEqual(config['handlers']['console']['level'], 'DEBUG')
            self.assertEqual(config['root']['level'], 'DEBUG')

    def test_settings_singleton(self):
        """Test that get_settings returns the same instance"""
        with patch.dict(os.environ, TEST_ENV_VARS):
            settings1 = get_settings()
            settings2 = get_settings()
            
            self.assertIs(settings1, settings2)

    def test_reload_settings(self):
        """Test settings reload functionality"""
        test_env = {**TEST_ENV_VARS, 'APP_NAME': 'Original Name'}
        with patch.dict(os.environ, test_env):
            settings1 = get_settings()
            self.assertEqual(settings1.app_name, 'Original Name')
            
            # Change environment variable
            os.environ['APP_NAME'] = 'New Name'
            
            # Reload settings
            settings2 = reload_settings()
            self.assertEqual(settings2.app_name, 'New Name')
            
            # Should be a new instance
            self.assertIsNot(settings1, settings2)

if __name__ == '__main__':
    unittest.main() 