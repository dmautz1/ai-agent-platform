"""
Unit tests for database operations.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
from unittest.mock import Mock, patch, AsyncMock
from database import DatabaseClient, get_database_client
import os

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        yield

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    with patch('database.get_supabase_client') as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client

class TestDatabaseClient:
    """Test cases for DatabaseClient class"""

    def test_init_success(self, mock_env_vars, mock_supabase_client):
        """Test successful initialization with valid environment variables"""
        client = DatabaseClient()
        assert client.client is not None

    def test_init_missing_env_vars(self):
        """Test initialization fails with missing environment variables"""
        with patch('database.get_supabase_client') as mock_get_client:
            # Mock get_supabase_client to raise an error
            mock_get_client.side_effect = ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_KEY environment variables are required"):
                DatabaseClient()

    @pytest.mark.asyncio
    async def test_create_job_success(self, mock_env_vars, mock_supabase_client):
        """Test successful job creation"""
        # Setup proper mock chain
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        # Create mock response with real list for data attribute
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([{"id": "test-id"}])

        client = DatabaseClient()
        job_data = {"task": "test", "input": "test input"}
        
        result = await client.create_job(job_data)
        
        assert result is not None
        assert result["id"] == "test-id"
        mock_supabase_client.table.assert_called_with("jobs")

    @pytest.mark.asyncio
    async def test_create_job_failure(self, mock_env_vars, mock_supabase_client):
        """Test job creation failure"""
        # Setup mock to return no data
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        
        # Create mock response with None data
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse(None)

        client = DatabaseClient()
        job_data = {"task": "test"}
        
        with pytest.raises(Exception, match="No data returned from job creation"):
            await client.create_job(job_data)

    @pytest.mark.asyncio
    async def test_get_job_success(self, mock_env_vars, mock_supabase_client):
        """Test successful job retrieval"""
        # Setup proper mock chain
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        
        # Create mock response with real list
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([{"id": "test-id", "status": "pending"}])

        client = DatabaseClient()
        result = await client.get_job("test-id")
        
        assert result is not None
        assert result["id"] == "test-id"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, mock_env_vars, mock_supabase_client):
        """Test job retrieval when job doesn't exist"""
        # Setup mock to return empty data
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        
        # Create mock response with empty list
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([])

        client = DatabaseClient()
        result = await client.get_job("nonexistent-id")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_jobs_success(self, mock_env_vars, mock_supabase_client):
        """Test successful retrieval of all jobs"""
        # Setup proper mock chain
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.range.return_value = mock_table
        
        # Create mock response with real list
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([
            {"id": "job1", "status": "completed"},
            {"id": "job2", "status": "pending"}
        ])

        client = DatabaseClient()
        result = await client.get_user_jobs("user123")  # Provide required user_id
        
        assert len(result) == 2
        assert result[0]["id"] == "job1"
        assert result[1]["id"] == "job2"

    @pytest.mark.asyncio
    async def test_update_job_success(self, mock_env_vars, mock_supabase_client):
        """Test successful job update"""
        # Setup proper mock chain
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        
        # Create mock response with real list
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([{"id": "test-id", "status": "completed"}])

        client = DatabaseClient()
        result = await client.update_job("test-id", {"status": "completed"})
        
        assert result is not None
        assert result["id"] == "test-id"

    @pytest.mark.asyncio
    async def test_update_job_status(self, mock_env_vars, mock_supabase_client):
        """Test job status update"""
        # Setup proper mock chain
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        
        # Create mock response with real list
        class MockResponse:
            def __init__(self, data):
                self.data = data
        
        mock_table.execute.return_value = MockResponse([{"id": "test-id", "status": "completed"}])

        client = DatabaseClient()
        result = await client.update_job_status("test-id", "completed", "success result")
        
        assert result is not None
        assert result["id"] == "test-id"

def test_get_database_client():
    """Test singleton database client getter"""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        with patch('database.create_client'):
            client1 = get_database_client()
            client2 = get_database_client()
            
            # Should return the same instance (singleton pattern)
            assert client1 is client2 