# Testing ApiResponse Implementation - Best Practices

## Overview

This document provides comprehensive best practices for testing the ApiResponse implementation across the AI Agent Platform, covering backend unit tests, integration tests, and frontend component tests.

## Backend Testing

### Unit Testing ApiResponse Models

```python
# tests/unit/test_models.py
import pytest
from pydantic import ValidationError
from backend.models import ApiResponse
from backend.utils.responses import create_success_response, create_error_response

class TestApiResponse:
    """Test ApiResponse model and utilities."""
    
    def test_success_response_creation(self):
        """Test creating a successful ApiResponse."""
        data = {"id": 1, "name": "test"}
        response = create_success_response(data, "Operation successful")
        
        assert response.success is True
        assert response.result == data
        assert response.message == "Operation successful"
        assert response.error is None
    
    def test_error_response_creation(self):
        """Test creating an error ApiResponse."""
        response = create_error_response("Something went wrong")
        
        assert response.success is False
        assert response.result is None
        assert response.error == "Something went wrong"
        assert response.message is None
    
    def test_response_serialization(self):
        """Test ApiResponse JSON serialization."""
        data = {"users": [{"id": 1, "name": "Alice"}]}
        response = create_success_response(data)
        
        # Test serialization
        json_data = response.model_dump()
        assert "success" in json_data
        assert "result" in json_data
        assert json_data["success"] is True
        assert json_data["result"] == data
```

### Integration Testing API Endpoints

```python
# tests/integration/test_routes_jobs.py
import pytest
from httpx import AsyncClient
from backend.models import ApiResponse, JobListResponse

class TestJobRoutes:
    """Test job-related API endpoints return correct ApiResponse format."""
    
    @pytest.mark.asyncio
    async def test_get_jobs_returns_api_response(self, client: AsyncClient, auth_headers):
        """Test /jobs/list returns proper ApiResponse[JobListResponse]."""
        response = await client.get("/jobs/list", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Parse response as ApiResponse
        data = response.json()
        assert "success" in data
        assert "result" in data
        assert data["success"] is True
        
        # Validate result structure matches JobListResponse
        result = data["result"]
        assert "jobs" in result
        assert "total_count" in result
        assert isinstance(result["jobs"], list)
        assert isinstance(result["total_count"], int)
    
    @pytest.mark.asyncio
    async def test_create_job_validation_error(self, client: AsyncClient, auth_headers):
        """Test job creation with invalid data returns ApiResponse error."""
        invalid_data = {"agent_name": ""}  # Missing required fields
        
        response = await client.post("/jobs/create", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        
        # Should be ApiResponse with error
        assert data["success"] is False
        assert data["error"] is not None
        assert data["result"] is None
```

## Frontend Testing

### Testing API Client Methods

```typescript
// src/test/lib/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { api } from '@/lib/api';
import { ApiResponse, JobListResponse } from '@/lib/types/api';

vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchJobs', () => {
    it('should return extracted result from ApiResponse', async () => {
      const mockApiResponse: ApiResponse<JobListResponse> = {
        success: true,
        result: {
          jobs: [{ id: '1', name: 'Test Job', status: 'completed' }],
          total_count: 1
        },
        message: null,
        error: null,
        metadata: null
      };

      mockedAxios.get.mockResolvedValueOnce({ data: mockApiResponse });

      const result = await api.fetchJobs();
      
      // API client should extract result automatically
      expect(result).toEqual(mockApiResponse.result);
      expect(result.jobs).toHaveLength(1);
      expect(result.total_count).toBe(1);
    });

    it('should handle API error responses', async () => {
      const mockErrorResponse: ApiResponse<JobListResponse> = {
        success: false,
        result: null,
        message: null,
        error: 'Failed to fetch jobs',
        metadata: null
      };

      mockedAxios.get.mockResolvedValueOnce({ data: mockErrorResponse });

      await expect(api.fetchJobs()).rejects.toThrow('Failed to fetch jobs');
    });
  });
});
```

### Testing React Components with ApiResponse

```typescript
// src/test/components/JobList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { JobList } from '@/components/JobList';
import { api } from '@/lib/api';
import { JobListResponse } from '@/lib/types/api';

vi.mock('@/lib/api');
const mockedApi = vi.mocked(api);

describe('JobList Component', () => {
  it('should display jobs when API returns successful response', async () => {
    const mockJobsData: JobListResponse = {
      jobs: [
        { id: '1', name: 'Test Job 1', status: 'completed' },
        { id: '2', name: 'Test Job 2', status: 'running' }
      ],
      total_count: 2
    };

    // Mock API client to return extracted result (not ApiResponse wrapper)
    mockedApi.fetchJobs.mockResolvedValueOnce(mockJobsData);

    render(<JobList />);

    await waitFor(() => {
      expect(screen.getByText('Test Job 1')).toBeInTheDocument();
      expect(screen.getByText('Test Job 2')).toBeInTheDocument();
    });

    expect(screen.getByText('Total: 2')).toBeInTheDocument();
  });

  it('should display error message when API fails', async () => {
    const errorMessage = 'Failed to load jobs';
    mockedApi.fetchJobs.mockRejectedValueOnce(new Error(errorMessage));

    render(<JobList />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });
});
```

## Testing Utilities and Best Practices

### Mock Data Generators

```typescript
// src/test/utils/apiMocks.ts
import { ApiResponse, JobListResponse, AgentInfo } from '@/lib/types/api';

/**
 * Create mock ApiResponse for testing
 */
export function createMockApiResponse<T>(
  result: T,
  options: {
    success?: boolean;
    message?: string;
    error?: string;
  } = {}
): ApiResponse<T> {
  return {
    success: options.success ?? true,
    result: options.success !== false ? result : null,
    message: options.message || null,
    error: options.error || null,
    metadata: null
  };
}

/**
 * Mock job list response
 */
export function createMockJobListResponse(): JobListResponse {
  return {
    jobs: [
      { id: '1', name: 'Job 1', status: 'completed' },
      { id: '2', name: 'Job 2', status: 'running' }
    ],
    total_count: 2
  };
}

/**
 * Mock error ApiResponse
 */
export function createMockErrorResponse(error: string): ApiResponse<null> {
  return createMockApiResponse(null, { success: false, error });
}
```

### Test Setup and Configuration

```typescript
// src/test/setupTests.ts
import { beforeEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
beforeEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock API responses consistently
export const setupApiMocks = () => {
  // Setup default successful responses
  vi.mocked(api.fetchJobs).mockResolvedValue(createMockJobListResponse());
  // Add more default mocks as needed
};
```

## Error Handling Testing

### Backend Error Response Testing

```python
# tests/integration/test_error_handling.py
import pytest
from httpx import AsyncClient

class TestErrorHandling:
    """Test error scenarios return proper ApiResponse format."""
    
    @pytest.mark.asyncio
    async def test_404_returns_api_response(self, client: AsyncClient):
        """Test 404 errors return ApiResponse format."""
        response = await client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] is not None
        assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_validation_error_returns_api_response(self, client: AsyncClient, auth_headers):
        """Test validation errors return ApiResponse format."""
        invalid_job_data = {"invalid": "data"}
        
        response = await client.post("/jobs/create", json=invalid_job_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error"] is not None
        assert "validation" in data["error"].lower()
```

### Frontend Error Handling Testing

```typescript
// src/test/hooks/useApiError.test.ts
import { renderHook } from '@testing-library/react';
import { useApiError } from '@/hooks/useApiError';

describe('useApiError Hook', () => {
  it('should extract error message from ApiResponse', () => {
    const { result } = renderHook(() => useApiError());
    
    const mockError = {
      response: {
        data: {
          success: false,
          error: 'Authentication failed',
          result: null
        }
      }
    };
    
    const errorMessage = result.current.getErrorMessage(mockError);
    expect(errorMessage).toBe('Authentication failed');
  });
  
  it('should handle non-ApiResponse errors', () => {
    const { result } = renderHook(() => useApiError());
    
    const networkError = new Error('Network Error');
    const errorMessage = result.current.getErrorMessage(networkError);
    
    expect(errorMessage).toBe('Network Error');
  });
});
```

## Performance Testing

### Response Size and Serialization

```python
# tests/performance/test_api_response_performance.py
import pytest
import time
import json
from backend.models import ApiResponse
from backend.utils.responses import create_success_response

class TestApiResponsePerformance:
    """Test ApiResponse performance characteristics."""
    
    def test_large_response_serialization(self):
        """Test serialization performance with large datasets."""
        # Create large dataset
        large_data = {"items": [{"id": i, "name": f"Item {i}"} for i in range(10000)]}
        
        start_time = time.time()
        response = create_success_response(large_data)
        json_data = response.model_dump_json()
        end_time = time.time()
        
        # Should serialize large responses in reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert len(json_data) > 0
    
    def test_response_memory_usage(self):
        """Test memory usage of ApiResponse objects."""
        import sys
        
        data = {"test": "data"}
        response = create_success_response(data)
        
        # ApiResponse should not significantly increase memory footprint
        response_size = sys.getsizeof(response)
        data_size = sys.getsizeof(data)
        
        # Response should not be more than 3x the data size
        assert response_size < (data_size * 3)
```

## Coverage and Quality Metrics

### Test Coverage Guidelines

```bash
# Backend coverage targets
pytest --cov=backend --cov-report=html --cov-fail-under=95

# Frontend coverage targets  
npm run test:frontend -- --coverage --coverageThreshold='{"global":{"branches":90,"functions":90,"lines":90,"statements":90}}'
```

### Quality Assurance Checklist

- [ ] **All endpoints return ApiResponse format**
- [ ] **Frontend components handle both success and error responses**
- [ ] **API client methods extract result field automatically**
- [ ] **Error handling preserves ApiResponse structure**
- [ ] **Performance tests validate response serialization**
- [ ] **Mock data generators create realistic ApiResponse objects**
- [ ] **Integration tests validate complete request/response cycle**

## Common Testing Patterns

### Pattern 1: Testing API Response Structure

```typescript
// Helper function for response validation
export function validateApiResponse<T>(
  response: any,
  expectedResultShape?: Partial<T>
): asserts response is ApiResponse<T> {
  expect(response).toHaveProperty('success');
  expect(response).toHaveProperty('result');
  expect(response).toHaveProperty('error');
  expect(response).toHaveProperty('message');
  
  if (response.success) {
    expect(response.result).not.toBeNull();
    if (expectedResultShape) {
      expect(response.result).toMatchObject(expectedResultShape);
    }
  } else {
    expect(response.error).not.toBeNull();
  }
}
```

### Pattern 2: Testing Component Error States

```typescript
// Test component error handling with ApiResponse
const renderWithApiError = (errorMessage: string) => {
  vi.mocked(api.fetchJobs).mockRejectedValueOnce(new Error(errorMessage));
  return render(<JobList />);
};

it('should display API error messages', async () => {
  renderWithApiError('Server unavailable');
  
  await waitFor(() => {
    expect(screen.getByText('Server unavailable')).toBeInTheDocument();
  });
});
```

This testing approach ensures comprehensive coverage of the ApiResponse implementation while maintaining clear separation between backend and frontend testing concerns. 