"""
Unit tests for environment configuration management.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from unittest.mock import patch, mock_open
from pydantic import ValidationError
from config.environment import (
    EnvironmentConfig,
    get_settings,
    validate_config,
    validate_required_settings,
    get_logging_config
)

class TestEnvironmentEnum:
    """Test Environment enumeration"""

    def test_environment_values(self):
        """Test Environment enum values"""
        assert EnvironmentConfig.development == "development"
        assert EnvironmentConfig.staging == "staging"
        assert EnvironmentConfig.production == "production"
        assert EnvironmentConfig.testing == "testing"

class TestLogLevelEnum:
    """Test LogLevel enumeration"""

    def test_log_level_values(self):
        """Test LogLevel enum values"""
        assert EnvironmentConfig.debug == "DEBUG"
        assert EnvironmentConfig.info == "INFO"
        assert EnvironmentConfig.warning == "WARNING"
        assert EnvironmentConfig.error == "ERROR"
        assert EnvironmentConfig.critical == "CRITICAL"

class TestSettings:
    """Test Settings configuration class"""

    def test_settings_defaults(self):
        """Test Settings with default values"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }, clear=True):
            settings = EnvironmentConfig()
            
            assert settings.app_name == "AI Agent Template API"
            assert settings.app_version == "1.0.0"
            assert settings.environment == EnvironmentConfig.development
            assert settings.debug is False
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.reload is True

    def test_settings_from_environment(self):
        """Test Settings loading from environment variables"""
        env_vars = {
            'APP_NAME': 'Custom API',
            'APP_VERSION': '2.0.0',
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'HOST': '127.0.0.1',
            'PORT': '9000',
            'SUPABASE_URL': 'https://prod-project.supabase.co',
            'SUPABASE_KEY': 'prod-key',
            'JWT_SECRET': 'super-secret-key',
            'GOOGLE_ADK_API_KEY': 'google-key',
            'LOG_LEVEL': 'ERROR'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = EnvironmentConfig()
            
            assert settings.app_name == 'Custom API'
            assert settings.app_version == '2.0.0'
            assert settings.environment == EnvironmentConfig.production
            assert settings.debug is False
            assert settings.host == '127.0.0.1'
            assert settings.port == 9000
            assert settings.supabase_url == 'https://prod-project.supabase.co'
            assert settings.supabase_key == 'prod-key'
            assert settings.jwt_secret == 'super-secret-key'
            assert settings.google_adk_api_key == 'google-key'
            assert settings.log_level == EnvironmentConfig.error

    def test_settings_missing_required_fields(self):
        """Test Settings validation with missing required fields"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            
            error_str = str(exc_info.value)
            assert "supabase_url" in error_str
            assert "supabase_key" in error_str

    def test_settings_invalid_supabase_url(self):
        """Test Settings validation with invalid Supabase URL"""
        # Test invalid protocol
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'http://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            assert "must start with https://" in str(exc_info.value)
        
        # Test invalid domain
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.example.com',
            'SUPABASE_KEY': 'test-key'
        }):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            assert "must end with .supabase.co" in str(exc_info.value)

    def test_settings_invalid_port(self):
        """Test Settings validation with invalid port"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'PORT': '0'  # Port must be >= 1
        }):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            assert "greater than or equal to 1" in str(exc_info.value)

    def test_settings_invalid_cors_origins(self):
        """Test Settings validation with invalid CORS origins"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'ALLOWED_ORIGINS': 'invalid-origin,another-invalid'
        }):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            assert "Invalid CORS origin" in str(exc_info.value)

    def test_environment_validation(self):
        """Test environment value validation"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'ENVIRONMENT': 'DEVELOPMENT'  # Should be converted to lowercase
        }):
            settings = EnvironmentConfig()
            assert settings.environment == EnvironmentConfig.development

class TestSettingsMethods:
    """Test Settings helper methods"""

    def setup_method(self):
        """Set up test settings"""
        self.env_vars = {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }

    def test_get_cors_origins_default_development(self):
        """Test get_cors_origins with development defaults"""
        with patch.dict(os.environ, {**self.env_vars, 'ENVIRONMENT': 'development'}):
            settings = EnvironmentConfig()
            origins = settings.get_cors_origins()
            
            assert 'http://localhost:3000' in origins
            assert 'http://localhost:5173' in origins
            assert len(origins) > 0

    def test_get_cors_origins_custom(self):
        """Test get_cors_origins with custom origins"""
        with patch.dict(os.environ, {
            **self.env_vars,
            'ALLOWED_ORIGINS': 'https://example.com,https://app.example.com'
        }):
            settings = EnvironmentConfig()
            origins = settings.get_cors_origins()
            
            assert origins == ['https://example.com', 'https://app.example.com']

    def test_get_cors_origins_production(self):
        """Test get_cors_origins for production environment"""
        with patch.dict(os.environ, {**self.env_vars, 'ENVIRONMENT': 'production'}):
            settings = EnvironmentConfig()
            origins = settings.get_cors_origins()
            
            assert 'https://yourdomain.com' in origins
            assert 'https://www.yourdomain.com' in origins

    def test_get_trusted_hosts_default(self):
        """Test get_trusted_hosts with defaults"""
        with patch.dict(os.environ, self.env_vars):
            settings = EnvironmentConfig()
            hosts = settings.get_trusted_hosts()
            
            assert hosts == ['*']

    def test_get_trusted_hosts_custom(self):
        """Test get_trusted_hosts with custom hosts"""
        with patch.dict(os.environ, {
            **self.env_vars,
            'TRUSTED_HOSTS': 'example.com,api.example.com'
        }):
            settings = EnvironmentConfig()
            hosts = settings.get_trusted_hosts()
            
            assert hosts == ['example.com', 'api.example.com']

    def test_environment_check_methods(self):
        """Test environment checking methods"""
        # Test development
        with patch.dict(os.environ, {**self.env_vars, 'ENVIRONMENT': 'development'}):
            settings = EnvironmentConfig()
            assert settings.is_development() is True
            assert settings.is_production() is False
            assert settings.is_testing() is False
        
        # Test production
        with patch.dict(os.environ, {**self.env_vars, 'ENVIRONMENT': 'production'}):
            settings = EnvironmentConfig()
            assert settings.is_development() is False
            assert settings.is_production() is True
            assert settings.is_testing() is False

    def test_get_database_url(self):
        """Test get_database_url method"""
        with patch.dict(os.environ, self.env_vars):
            settings = EnvironmentConfig()
            url = settings.get_database_url()
            
            assert url == "https://test-project.supabase.co/rest/v1/"

    def test_get_auth_url(self):
        """Test get_auth_url method"""
        with patch.dict(os.environ, self.env_vars):
            settings = EnvironmentConfig()
            url = settings.get_auth_url()
            
            assert url == "https://test-project.supabase.co/auth/v1/"

class TestSettingsGlobal:
    """Test global settings functions"""

    @patch('config.environment.get_settings', None)
    def test_get_settings_singleton(self):
        """Test get_settings returns singleton instance"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            settings1 = get_settings()
            settings2 = get_settings()
            
            assert settings1 is settings2

    @patch('config.environment.get_settings', None)
    def test_reload_settings(self):
        """Test reload_settings creates new instance"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            settings1 = get_settings()
            settings2 = validate_config()
            
            assert settings1 is not settings2

    def test_validate_required_settings_success(self):
        """Test validate_required_settings with valid settings"""
        with patch('config.environment.get_settings') as mock_get_settings:
            mock_settings = EnvironmentConfig(
                supabase_url='https://test-project.supabase.co',
                supabase_key='test-key'
            )
            mock_get_settings.return_value = mock_settings
            
            # Should not raise any exception
            validate_required_settings()

    def test_validate_required_settings_missing(self):
        """Test validate_required_settings with missing required fields"""
        with patch('config.environment.get_settings') as mock_get_settings:
            mock_settings = EnvironmentConfig(
                supabase_url='https://test-project.supabase.co',
                supabase_key='test-key'
            )
            # Simulate missing required field
            mock_settings.supabase_key = None
            mock_get_settings.return_value = mock_settings
            
            with pytest.raises(ValueError) as exc_info:
                validate_required_settings()
            assert "Missing required environment variables" in str(exc_info.value)

class TestLoggingConfig:
    """Test logging configuration"""

    def test_get_logging_config_basic(self):
        """Test get_logging_config with basic settings"""
        with patch('config.environment.get_settings') as mock_get_settings:
            mock_settings = EnvironmentConfig(
                supabase_url='https://test-project.supabase.co',
                supabase_key='test-key',
                log_level=EnvironmentConfig.info,
                log_file=None
            )
            mock_get_settings.return_value = mock_settings
            
            config = get_logging_config()
            
            assert config['version'] == 1
            assert 'console' in config['handlers']
            assert 'file' not in config['handlers']
            assert config['root']['level'] == 'INFO'

    def test_get_logging_config_with_file(self):
        """Test get_logging_config with file logging"""
        with patch('config.environment.get_settings') as mock_get_settings:
            mock_settings = EnvironmentConfig(
                supabase_url='https://test-project.supabase.co',
                supabase_key='test-key',
                log_level=EnvironmentConfig.debug,
                log_file='/var/log/app.log',
                log_rotation=True,
                log_max_size='5MB',
                log_backup_count=3
            )
            mock_get_settings.return_value = mock_settings
            
            config = get_logging_config()
            
            assert 'file' in config['handlers']
            assert config['handlers']['file']['class'] == 'logging.handlers.RotatingFileHandler'
            assert config['handlers']['file']['filename'] == '/var/log/app.log'
            assert config['handlers']['file']['maxBytes'] == 5 * 1024 * 1024
            assert config['handlers']['file']['backupCount'] == 3

    def test_get_logging_config_no_rotation(self):
        """Test get_logging_config without log rotation"""
        with patch('config.environment.get_settings') as mock_get_settings:
            mock_settings = EnvironmentConfig(
                supabase_url='https://test-project.supabase.co',
                supabase_key='test-key',
                log_file='/var/log/app.log',
                log_rotation=False
            )
            mock_get_settings.return_value = mock_settings
            
            config = get_logging_config()
            
            assert config['handlers']['file']['class'] == 'logging.FileHandler'

class TestUtilityFunctions:
    """Test utility functions"""

    def test_parse_size_bytes(self):
        """Test _parse_size with bytes"""
        assert _parse_size("1024") == 1024
        assert _parse_size("2048") == 2048

    def test_parse_size_kb(self):
        """Test _parse_size with kilobytes"""
        assert _parse_size("1KB") == 1024
        assert _parse_size("5kb") == 5 * 1024

    def test_parse_size_mb(self):
        """Test _parse_size with megabytes"""
        assert _parse_size("1MB") == 1024 * 1024
        assert _parse_size("10mb") == 10 * 1024 * 1024

    def test_parse_size_gb(self):
        """Test _parse_size with gigabytes"""
        assert _parse_size("1GB") == 1024 * 1024 * 1024
        assert _parse_size("2gb") == 2 * 1024 * 1024 * 1024

    def test_parse_size_with_spaces(self):
        """Test _parse_size with whitespace"""
        assert _parse_size(" 5MB ") == 5 * 1024 * 1024

class TestSettingsValidationEdgeCases:
    """Test edge cases and validation scenarios"""

    def test_production_debug_warning(self):
        """Test warning when debug is enabled in production"""
        with patch('config.logger') as mock_logger:
            with patch.dict(os.environ, {
                'SUPABASE_URL': 'https://prod-project.supabase.co',
                'SUPABASE_KEY': 'prod-key',
                'ENVIRONMENT': 'production',
                'DEBUG': 'true'
            }):
                settings = EnvironmentConfig()
                assert settings.debug is True
                # Should have logged a warning
                mock_logger.warning.assert_called()

    def test_production_reserved_port_warning(self):
        """Test warning when using reserved ports in production"""
        with patch('config.logger') as mock_logger:
            with patch.dict(os.environ, {
                'SUPABASE_URL': 'https://prod-project.supabase.co',
                'SUPABASE_KEY': 'prod-key',
                'ENVIRONMENT': 'production',
                'PORT': '80'
            }):
                settings = EnvironmentConfig()
                assert settings.port == 80
                # Should have logged a warning
                mock_logger.warning.assert_called()

    def test_cors_origins_with_wildcard(self):
        """Test CORS origins with wildcard"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'ALLOWED_ORIGINS': '*'
        }):
            settings = EnvironmentConfig()
            origins = settings.get_cors_origins()
            assert origins == ['*']

    def test_cors_origins_empty_string(self):
        """Test CORS origins with empty string"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'ALLOWED_ORIGINS': ''
        }):
            settings = EnvironmentConfig()
            origins = settings.get_cors_origins()
            # Should use defaults for development
            assert 'http://localhost:3000' in origins

    def test_max_values_validation(self):
        """Test maximum value validation"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-key',
            'MAX_CONCURRENT_JOBS': '150'  # Exceeds maximum of 100
        }):
            with pytest.raises(ValidationError) as exc_info:
                EnvironmentConfig()
            assert "less than or equal to 100" in str(exc_info.value) 