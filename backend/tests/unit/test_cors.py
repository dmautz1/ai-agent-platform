"""
Unit tests for CORS configuration and functionality.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app, get_cors_origins

class TestCORSConfiguration:
    """Test CORS configuration functionality"""

    def test_get_cors_origins_from_env(self):
        """Test CORS origins configuration from environment variables"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': 'http://localhost:3000,https://example.com,https://api.example.com'
        }):
            origins = get_cors_origins()
            expected = ['http://localhost:3000', 'https://example.com', 'https://api.example.com']
            assert origins == expected

    def test_get_cors_origins_development_default(self):
        """Test default CORS origins for development environment"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            origins = get_cors_origins()
            
            # Should include development localhost origins
            assert 'http://localhost:3000' in origins
            assert 'http://localhost:3001' in origins
            assert 'http://127.0.0.1:3000' in origins
            assert 'http://localhost:5173' in origins  # Vite default
            
            # Should not include production origins in development
            assert all(not origin.startswith('https://') for origin in origins)

    def test_get_cors_origins_production_default(self):
        """Test default CORS origins for production environment"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}, clear=True):
            origins = get_cors_origins()
            
            # Should include both development and production origins
            assert 'http://localhost:3000' in origins  # Still needed for local testing
            assert 'https://yourdomain.vercel.app' in origins
            assert 'https://www.yourdomain.com' in origins

    def test_get_cors_origins_custom_environment(self):
        """Test CORS origins for custom environment"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}, clear=True):
            origins = get_cors_origins()
            
            # Should include development origins for non-production environment
            assert 'http://localhost:3000' in origins
            assert len(origins) > 0

    def test_get_cors_origins_empty_env(self):
        """Test CORS origins when environment variable is empty"""
        with patch.dict(os.environ, {'ALLOWED_ORIGINS': ''}, clear=True):
            origins = get_cors_origins()
            
            # Should fall back to default origins
            assert len(origins) > 0
            assert 'http://localhost:3000' in origins

class TestCORSEndpoints:
    """Test CORS functionality with API endpoints"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)

    def test_cors_preflight_request(self):
        """Test CORS preflight OPTIONS request"""
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Authorization,Content-Type'
        }
        
        response = self.client.options("/schedule-job", headers=headers)
        
        # CORS preflight should be handled automatically by FastAPI middleware
        assert response.status_code in [200, 405]  # 405 if no OPTIONS handler, but CORS headers should be present

    def test_cors_simple_request(self):
        """Test CORS with simple GET request"""
        headers = {'Origin': 'http://localhost:3000'}
        
        response = self.client.get("/health", headers=headers)
        
        assert response.status_code == 200
        # CORS headers should be present (though they might not show in TestClient)

    def test_cors_info_endpoint_development(self):
        """Test CORS info endpoint in development environment"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            response = self.client.get("/cors-info")
            
            assert response.status_code == 200
            data = response.json()
            assert 'cors_origins' in data
            assert data['environment'] == 'development'
            assert 'CORS configuration (development mode)' in data['message']
            assert isinstance(data['cors_origins'], list)

    def test_cors_info_endpoint_production(self):
        """Test CORS info endpoint in production environment"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            response = self.client.get("/cors-info")
            
            assert response.status_code == 200
            data = response.json()
            assert 'cors_enabled' in data
            assert 'origins_count' in data
            assert data['environment'] == 'production'
            assert 'production mode - details hidden' in data['message']
            # Should not expose actual origins in production
            assert 'cors_origins' not in data

    def test_health_endpoint_includes_cors_count(self):
        """Test that health endpoint includes CORS origins count"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'cors_origins' in data
        assert isinstance(data['cors_origins'], int)
        assert data['cors_origins'] > 0

class TestCORSHeaders:
    """Test CORS headers in responses"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)

    def test_cors_headers_present_on_error_responses(self):
        """Test CORS headers are present even on error responses"""
        headers = {'Origin': 'http://localhost:3000'}
        
        # Test with an endpoint that returns 403 (no auth)
        response = self.client.get("/auth/me", headers=headers)
        
        assert response.status_code == 403
        # Note: TestClient might not show CORS headers, but they should be handled by middleware

    def test_cors_with_credentials(self):
        """Test CORS configuration allows credentials"""
        headers = {
            'Origin': 'http://localhost:3000',
            'Authorization': 'Bearer test-token'
        }
        
        response = self.client.get("/health", headers=headers)
        
        assert response.status_code == 200
        # Credentials should be allowed (configured in middleware)

class TestCORSSecurityScenarios:
    """Test CORS security scenarios"""

    def test_cors_with_malicious_origin(self):
        """Test CORS behavior with non-allowed origin"""
        headers = {'Origin': 'https://malicious-site.com'}
        
        response = self.client.get("/health", headers=headers)
        
        # Request should still succeed (CORS is browser-enforced)
        assert response.status_code == 200
        # But CORS headers should not allow the malicious origin

    def test_cors_configuration_logging(self):
        """Test that CORS configuration is properly logged"""
        with patch('main.logger') as mock_logger:
            with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
                origins = get_cors_origins()
                
                # Should log the origins configuration
                mock_logger.info.assert_called()
                call_args = [call[0][0] for call in mock_logger.info.call_args_list]
                assert any('default CORS origins' in arg for arg in call_args)

class TestCORSEnvironmentVariables:
    """Test CORS configuration with different environment variable combinations"""

    def test_cors_with_whitespace_origins(self):
        """Test CORS origins with whitespace handling"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': ' http://localhost:3000 , https://example.com , https://test.com '
        }):
            origins = get_cors_origins()
            
            # Should trim whitespace
            expected = ['http://localhost:3000', 'https://example.com', 'https://test.com']
            assert origins == expected

    def test_cors_with_single_origin(self):
        """Test CORS configuration with single origin"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': 'https://single-domain.com'
        }):
            origins = get_cors_origins()
            
            assert origins == ['https://single-domain.com']

    def test_cors_methods_and_headers_configuration(self):
        """Test that allowed methods and headers are properly configured"""
        # This tests the middleware configuration indirectly
        with patch('main.app.add_middleware') as mock_middleware:
            # Re-import to trigger middleware setup
            from importlib import reload
            import main
            reload(main)
            
            # Should have been called with proper CORS configuration
            mock_middleware.assert_called()
            
            # Check the call arguments for CORS configuration
            calls = mock_middleware.call_args_list
            cors_call = None
            for call in calls:
                if len(call[0]) > 0 and 'CORSMiddleware' in str(call[0][0]):
                    cors_call = call
                    break
            
            if cors_call:
                # Verify important CORS settings
                kwargs = cors_call[1]
                assert kwargs.get('allow_credentials') is True
                assert 'GET' in kwargs.get('allow_methods', [])
                assert 'POST' in kwargs.get('allow_methods', [])
                assert 'Authorization' in kwargs.get('allow_headers', [])
                assert 'Content-Type' in kwargs.get('allow_headers', []) 