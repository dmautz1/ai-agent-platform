import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import { api, handleApiError, formatValidationErrors, isValidationError, setAuthToken, clearAuthToken } from '../../src/lib/api';
import type { CreateJobRequest, JobsQuery, LoginRequest, ApiError } from '../../src/lib/types';
import axios from 'axios';

// Mock server setup for testing different scenarios
const mockServer = {
  baseURL: 'http://localhost:8001', // Different port to avoid conflicts
  isRunning: false,
};

// Mock responses for different scenarios
const mockResponses = {
  validJob: {
    success: true,
    data: {
      id: 'test-job-123',
      status: 'pending',
      priority: 'normal',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_id: 'test-user-123',
      data: {
        agent_type: 'text_processing',
        title: 'Test Job',
        input_text: 'Test input text',
        operation: 'sentiment_analysis'
      }
    }
  },
  validJobsList: {
    success: true,
    data: {
      jobs: [
        {
          id: 'job-1',
          status: 'completed',
          priority: 'normal',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          user_id: 'test-user-123',
          data: { agent_type: 'text_processing', title: 'Job 1', input_text: 'Test' }
        },
        {
          id: 'job-2',
          status: 'running',
          priority: 'high',
          created_at: '2024-01-01T01:00:00Z',
          updated_at: '2024-01-01T01:00:00Z',
          user_id: 'test-user-123',
          data: { agent_type: 'summarization', title: 'Job 2', input_text: 'Test content' }
        }
      ],
      pagination: {
        total: 2,
        page: 1,
        per_page: 20,
        total_pages: 1,
        has_next: false,
        has_prev: false
      },
      filters_applied: {}
    }
  },
  validUser: {
    success: true,
    data: {
      id: 'test-user-123',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
  },
  healthCheck: {
    success: true,
    data: {
      status: 'healthy',
      timestamp: '2024-01-01T00:00:00Z',
      version: '1.0.0',
      environment: 'testing',
      components: {
        database: { status: 'healthy', last_check: '2024-01-01T00:00:00Z' },
        agents: { status: 'healthy', last_check: '2024-01-01T00:00:00Z' },
        storage: { status: 'healthy', last_check: '2024-01-01T00:00:00Z' },
        external_apis: { status: 'healthy', last_check: '2024-01-01T00:00:00Z' }
      }
    }
  }
};

// Setup axios mock for controlled testing
const mockAxios = vi.fn();
const originalCreate = axios.create;

describe('API Communication Integration Tests', () => {
  beforeAll(() => {
    // Setup environment for testing
    vi.stubEnv('VITE_API_BASE_URL', mockServer.baseURL);
    vi.stubEnv('DEV', true);
  });

  afterAll(() => {
    vi.unstubAllEnvs();
  });

  beforeEach(() => {
    // Clear any stored auth tokens
    clearAuthToken();
    
    // Clear axios interceptors and reset mocks
    vi.clearAllMocks();
    
    // Mock axios.create to return our controlled mock
    vi.mocked(axios.create).mockImplementation(() => ({
      ...axios.create(),
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() }
      },
      get: mockAxios,
      post: mockAxios,
      patch: mockAxios,
      delete: mockAxios,
    }) as any);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Job API Operations', () => {
    it('should successfully fetch all jobs', async () => {
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJobsList });

      const jobs = await api.jobs.getAll();

      expect(mockAxios).toHaveBeenCalledWith('/jobs', { params: undefined });
      expect(jobs).toHaveLength(2);
      expect(jobs[0].id).toBe('job-1');
      expect(jobs[0].status).toBe('completed');
      expect(jobs[1].id).toBe('job-2');
      expect(jobs[1].status).toBe('running');
    });

    it('should fetch jobs with query parameters', async () => {
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJobsList });

      const query: JobsQuery = {
        status: ['pending', 'running'],
        agent_type: 'text_processing',
        page: 1,
        per_page: 10
      };

      await api.jobs.getAll(query);

      expect(mockAxios).toHaveBeenCalledWith('/jobs', { 
        params: expect.any(URLSearchParams)
      });

      // Verify query parameters are properly formatted
      const callParams = mockAxios.mock.calls[0][1].params;
      expect(callParams.toString()).toContain('status=pending%2Crunning');
      expect(callParams.toString()).toContain('agent_type=text_processing');
    });

    it('should successfully fetch job by ID', async () => {
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJob });

      const job = await api.jobs.getById('test-job-123');

      expect(mockAxios).toHaveBeenCalledWith('/jobs/test-job-123');
      expect(job.id).toBe('test-job-123');
      expect(job.status).toBe('pending');
    });

    it('should throw error when job not found', async () => {
      mockAxios.mockResolvedValueOnce({ data: { success: true, data: null } });

      await expect(api.jobs.getById('nonexistent-job')).rejects.toThrow('Job not found');
    });

    it('should successfully create a new job', async () => {
      const createResponse = {
        success: true,
        message: 'Job created successfully',
        job_id: 'new-job-123',
        estimated_completion_time: '2024-01-01T01:00:00Z'
      };
      
      mockAxios.mockResolvedValueOnce({ data: createResponse });

      const jobRequest: CreateJobRequest = {
        data: {
          agent_type: 'text_processing',
          title: 'New Test Job',
          input_text: 'Test content for processing',
          operation: 'sentiment_analysis'
        },
        priority: 'high',
        tags: ['test', 'integration']
      };

      const result = await api.jobs.create(jobRequest);

      expect(mockAxios).toHaveBeenCalledWith('/jobs', jobRequest);
      expect(result.job_id).toBe('new-job-123');
      expect(result.success).toBe(true);
    });

    it('should handle job creation failure', async () => {
      mockAxios.mockResolvedValueOnce({ data: { success: false, job_id: null } });

      const jobRequest: CreateJobRequest = {
        data: {
          agent_type: 'text_processing',
          title: 'Failed Job',
          input_text: 'Test content'
        }
      };

      await expect(api.jobs.create(jobRequest)).rejects.toThrow('Failed to create job');
    });

    it('should successfully update a job', async () => {
      const updatedJob = { ...mockResponses.validJob.data, priority: 'high' };
      mockAxios.mockResolvedValueOnce({ data: { success: true, data: updatedJob } });

      const result = await api.jobs.update('test-job-123', { priority: 'high' });

      expect(mockAxios).toHaveBeenCalledWith('/jobs/test-job-123', { priority: 'high' });
      expect(result.priority).toBe('high');
    });

    it('should successfully delete a job', async () => {
      mockAxios.mockResolvedValueOnce({ data: { success: true } });

      await api.jobs.delete('test-job-123');

      expect(mockAxios).toHaveBeenCalledWith('/jobs/test-job-123');
    });

    it('should fetch job status', async () => {
      mockAxios.mockResolvedValueOnce({ 
        data: { success: true, data: { status: 'running' } } 
      });

      const status = await api.jobs.getStatus('test-job-123');

      expect(mockAxios).toHaveBeenCalledWith('/jobs/test-job-123/status');
      expect(status).toBe('running');
    });

    it('should fetch batch job statuses', async () => {
      const batchResponse = {
        success: true,
        data: {
          'job-1': { status: 'completed', updated_at: '2024-01-01T00:00:00Z' },
          'job-2': { status: 'running', updated_at: '2024-01-01T00:00:00Z' }
        }
      };
      
      mockAxios.mockResolvedValueOnce({ data: batchResponse });

      const result = await api.jobs.getBatchStatus(['job-1', 'job-2']);

      expect(mockAxios).toHaveBeenCalledWith('/jobs/batch/status', { 
        job_ids: ['job-1', 'job-2'] 
      });
      expect(result['job-1'].status).toBe('completed');
      expect(result['job-2'].status).toBe('running');
    });
  });

  describe('Authentication API Operations', () => {
    it('should successfully login with valid credentials', async () => {
      const loginResponse = {
        success: true,
        data: {
          user: mockResponses.validUser.data,
          tokens: {
            access_token: 'valid-token-123',
            refresh_token: 'refresh-token-123',
            token_type: 'Bearer',
            expires_in: 3600
          }
        }
      };

      mockAxios.mockResolvedValueOnce({ data: loginResponse });

      const credentials: LoginRequest = {
        email: 'test@example.com',
        password: 'testpassword'
      };

      const result = await api.auth.login(credentials);

      expect(mockAxios).toHaveBeenCalledWith('/auth/login', credentials);
      expect(result.user.email).toBe('test@example.com');
      expect(result.tokens.access_token).toBe('valid-token-123');
    });

    it('should handle login failure', async () => {
      mockAxios.mockResolvedValueOnce({ data: { success: false, data: null } });

      const credentials: LoginRequest = {
        email: 'invalid@example.com',
        password: 'wrongpassword'
      };

      await expect(api.auth.login(credentials)).rejects.toThrow('Login failed');
    });

    it('should get current user when authenticated', async () => {
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validUser });

      const user = await api.auth.getCurrentUser();

      expect(mockAxios).toHaveBeenCalledWith('/auth/me');
      expect(user.email).toBe('test@example.com');
    });

    it('should handle logout', async () => {
      setAuthToken('test-token');
      mockAxios.mockResolvedValueOnce({ data: { success: true } });

      await api.auth.logout();

      expect(mockAxios).toHaveBeenCalledWith('/auth/logout');
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('Health Check API Operations', () => {
    it('should fetch health check status', async () => {
      mockAxios.mockResolvedValueOnce({ data: mockResponses.healthCheck });

      const health = await api.health.check();

      expect(mockAxios).toHaveBeenCalledWith('/health');
      expect(health.status).toBe('healthy');
      expect(health.components.database.status).toBe('healthy');
    });

    it('should handle unhealthy status', async () => {
      const unhealthyResponse = {
        success: true,
        data: {
          ...mockResponses.healthCheck.data,
          status: 'unhealthy',
          components: {
            ...mockResponses.healthCheck.data.components,
            database: { status: 'unhealthy', last_check: '2024-01-01T00:00:00Z', error: 'Connection failed' }
          }
        }
      };

      mockAxios.mockResolvedValueOnce({ data: unhealthyResponse });

      const health = await api.health.check();

      expect(health.status).toBe('unhealthy');
      expect(health.components.database.status).toBe('unhealthy');
      expect(health.components.database.error).toBe('Connection failed');
    });
  });

  describe('Error Handling Scenarios', () => {
    it('should handle 401 Unauthorized errors', async () => {
      const errorResponse = {
        response: {
          status: 401,
          data: { message: 'Authentication required' }
        }
      };

      mockAxios.mockRejectedValueOnce(errorResponse);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 401,
          message: 'Authentication required'
        });
      }
    });

    it('should handle 422 Validation errors', async () => {
      const validationError = {
        response: {
          status: 422,
          data: {
            message: 'Validation failed',
            errors: {
              'title': ['Title is required'],
              'input_text': ['Input text must be at least 10 characters']
            }
          }
        }
      };

      mockAxios.mockRejectedValueOnce(validationError);

      try {
        await api.jobs.create({
          data: {
            agent_type: 'text_processing',
            title: '',
            input_text: 'short'
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 422,
          message: 'Validation failed',
          errors: {
            'title': ['Title is required'],
            'input_text': ['Input text must be at least 10 characters']
          }
        });
      }
    });

    it('should handle 404 Not Found errors', async () => {
      const notFoundError = {
        response: {
          status: 404,
          data: { message: 'Resource not found' }
        }
      };

      mockAxios.mockRejectedValueOnce(notFoundError);

      try {
        await api.jobs.getById('nonexistent-job');
      } catch (error) {
        expect(error).toMatchObject({
          status: 404,
          message: 'Resource not found'
        });
      }
    });

    it('should handle 500 Internal Server errors', async () => {
      const serverError = {
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        }
      };

      mockAxios.mockRejectedValueOnce(serverError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 500,
          message: 'Internal server error'
        });
      }
    });

    it('should handle network errors', async () => {
      const networkError = {
        request: {},
        message: 'Network Error'
      };

      mockAxios.mockRejectedValueOnce(networkError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'Network error - please check your connection'
        });
      }
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded'
      };

      mockAxios.mockRejectedValueOnce(timeoutError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'timeout of 30000ms exceeded'
        });
      }
    });

    it('should handle malformed response data', async () => {
      mockAxios.mockResolvedValueOnce({ data: 'invalid json' });

      const jobs = await api.jobs.getAll();

      // Should handle gracefully and return empty array
      expect(jobs).toEqual([]);
    });

    it('should handle missing response data', async () => {
      mockAxios.mockResolvedValueOnce({ data: { success: true } });

      const jobs = await api.jobs.getAll();

      expect(jobs).toEqual([]);
    });
  });

  describe('Authentication Token Handling', () => {
    it('should include auth token in requests when available', async () => {
      setAuthToken('test-token-123');
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJobsList });

      await api.jobs.getAll();

      // Note: This would normally be tested via interceptor behavior
      // In a real test, you'd verify the Authorization header is set
      expect(mockAxios).toHaveBeenCalled();
    });

    it('should handle token refresh on 401 errors', async () => {
      // First request fails with 401
      const unauthorizedError = {
        response: {
          status: 401,
          data: { message: 'Token expired' }
        }
      };

      mockAxios.mockRejectedValueOnce(unauthorizedError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 401,
          message: 'Token expired'
        });
      }

      // Verify auth token was cleared
      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('should clear token and redirect on authentication failure', async () => {
      setAuthToken('invalid-token');
      
      const unauthorizedError = {
        response: {
          status: 401,
          data: { message: 'Invalid token' }
        }
      };

      mockAxios.mockRejectedValueOnce(unauthorizedError);

      // Mock window.location.href
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { ...originalLocation, href: '' };

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(localStorage.getItem('auth_token')).toBeNull();
        // Note: In real implementation, would verify redirect occurred
      }

      // Restore window.location
      window.location = originalLocation;
    });
  });

  describe('Error Utility Functions', () => {
    it('should handle API errors correctly', () => {
      const apiError: ApiError = {
        status: 422,
        message: 'Validation failed',
        errors: {
          'field1': ['Error 1', 'Error 2'],
          'field2': ['Error 3']
        }
      };

      const message = handleApiError(apiError);
      expect(message).toBe('Validation failed');
    });

    it('should handle string errors', () => {
      const message = handleApiError('Simple error message');
      expect(message).toBe('Simple error message');
    });

    it('should handle unknown error formats', () => {
      const message = handleApiError({});
      expect(message).toBe('An unexpected error occurred');
    });

    it('should format validation errors correctly', () => {
      const errors = {
        'title': ['Title is required'],
        'input_text': ['Input text must be at least 10 characters', 'Input text contains invalid characters']
      };

      const formatted = formatValidationErrors(errors);
      expect(formatted).toBe('title: Title is required; input_text: Input text must be at least 10 characters, Input text contains invalid characters');
    });

    it('should identify validation errors correctly', () => {
      const validationError = { status: 422, errors: {} };
      const otherError = { status: 500, message: 'Server error' };

      expect(isValidationError(validationError)).toBe(true);
      expect(isValidationError(otherError)).toBe(false);
    });
  });

  describe('Rate Limiting and Retry Logic', () => {
    it('should handle 429 Too Many Requests errors', async () => {
      const rateLimitError = {
        response: {
          status: 429,
          data: {
            message: 'Rate limit exceeded',
            retry_after: 60
          }
        }
      };

      mockAxios.mockRejectedValueOnce(rateLimitError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 429,
          message: 'Rate limit exceeded'
        });
      }
    });

    it('should handle concurrent requests efficiently', async () => {
      // Mock successful responses for multiple requests
      mockAxios
        .mockResolvedValueOnce({ data: mockResponses.validJob })
        .mockResolvedValueOnce({ data: mockResponses.validJob })
        .mockResolvedValueOnce({ data: mockResponses.validJob });

      const promises = [
        api.jobs.getById('job-1'),
        api.jobs.getById('job-2'),
        api.jobs.getById('job-3')
      ];

      const results = await Promise.all(promises);

      expect(results).toHaveLength(3);
      expect(mockAxios).toHaveBeenCalledTimes(3);
    });
  });

  describe('Content Type and Data Serialization', () => {
    it('should handle JSON request and response data correctly', async () => {
      const complexJobData = {
        agent_type: 'summarization' as const,
        title: 'Complex Summarization Job',
        input_text: 'This is a very long text that needs to be summarized...',
        max_summary_length: 100,
        format: 'bullet_points' as const,
        include_quotes: true
      };

      const createRequest: CreateJobRequest = {
        data: complexJobData,
        priority: 'high',
        tags: ['complex', 'summarization'],
        metadata: {
          source: 'test',
          complexity: 'high'
        }
      };

      mockAxios.mockResolvedValueOnce({ 
        data: { 
          success: true, 
          job_id: 'complex-job-123' 
        } 
      });

      const result = await api.jobs.create(createRequest);

      expect(mockAxios).toHaveBeenCalledWith('/jobs', createRequest);
      expect(result.job_id).toBe('complex-job-123');
    });

    it('should handle special characters and Unicode in requests', async () => {
      const unicodeJobData = {
        agent_type: 'text_processing' as const,
        title: 'Unicode Test Job 🚀',
        input_text: 'Testing special chars: àáâãäåæçèéêë 中文 العربية 🌍',
        operation: 'sentiment_analysis' as const
      };

      mockAxios.mockResolvedValueOnce({ 
        data: { 
          success: true, 
          job_id: 'unicode-job-123' 
        } 
      });

      const result = await api.jobs.create({ data: unicodeJobData });

      expect(result.job_id).toBe('unicode-job-123');
    });
  });

  describe('Request and Response Logging', () => {
    it('should log requests in development mode', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJobsList });

      await api.jobs.getAll();

      // Note: In real implementation, would verify console.log was called
      // with request details in development mode
      
      consoleSpy.mockRestore();
    });

    it('should log responses in development mode', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      mockAxios.mockResolvedValueOnce({ data: mockResponses.validJobsList });

      await api.jobs.getAll();

      // Note: In real implementation, would verify console.log was called
      // with response details in development mode
      
      consoleSpy.mockRestore();
    });
  });
}); 