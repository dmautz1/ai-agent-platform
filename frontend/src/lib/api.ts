import axios, { type AxiosInstance, type AxiosResponse, AxiosError } from 'axios';
import { useState, useCallback } from 'react';
import type {
  // Base API types
  ApiResponse,
  ApiError,
  
  // Job response types
  JobListResponse,
  JobDetailResponse,
  CreateJobResponse,
  JobStatusResponse,
  JobRetryResponse,
  JobRerunResponse,
  JobLogsResponse,
  BatchStatusResponse,
  JobsMinimalResponse,
  
  // Agent response types
  AgentListResponse,
  AgentDetailResponse,
  AgentSchemaResponse,
  
  // Agent result types
  AgentSchemaResult,
  
  // System response types
  HealthResponse,
  SystemStatsResponse,
  
  // Auth response types
  LoginResponse,
  AuthUserResponse,
  AuthTokenResponse,
  
  // Core types
  Job,
  JobMinimal,
  JobStatus,
  CreateJobRequest,
  JobsQuery,
  BatchStatusRequest,
  JobStatusUpdate,
  
  // User & Auth types
  User,
  LoginRequest,
  AuthTokens,
  
  // Agent types
  AgentInfo,
  
  // System types
  HealthCheck,
  SystemStats,
  
  // Utility types
} from './types';

// Utility function to extract result from ApiResponse
export function extractApiResult<T>(response: ApiResponse<T>): T {
  if (!response.success) {
    throw new Error(response.error || 'API request failed');
  }
  if (response.result === null || response.result === undefined) {
    throw new Error('API response missing result data');
  }
  return response.result;
}

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and logging
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Check if response contains ApiResponse with success=false
    const data = response.data;
    if (data && typeof data === 'object' && 'success' in data && !data.success) {
      // This is an ApiResponse with an error
      const apiResponseData = data as ApiResponse<unknown>;
      const apiError: ApiError = {
        status: response.status,
        message: apiResponseData.error || apiResponseData.message || 'API request failed',
        data: apiResponseData,
        errors: apiResponseData.metadata?.validation_errors as Record<string, string[]> || undefined,
      };
      
      console.error(`API Error ${response.status}:`, apiResponseData);
      
      // Handle specific status codes
      switch (response.status) {
        case 401:
          // Unauthorized - clear auth token and redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/auth';
          break;
        case 403:
          console.error('Access forbidden');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 422:
          console.error('Validation error');
          break;
        case 500:
          console.error('Internal server error');
          break;
        default:
          console.error('Unexpected error:', apiResponseData);
      }
      
      return Promise.reject(apiError);
    }
    
    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;

      console.error(`API Error ${status}:`, data);

      // Check if the error response is in ApiResponse format
      if (data && typeof data === 'object' && 'success' in data && !data.success) {
        // ApiResponse error format
        const apiResponseData = data as ApiResponse<unknown>;
        const apiError: ApiError = {
          status,
          message: apiResponseData.error || apiResponseData.message || 'API request failed',
          data: apiResponseData,
          errors: apiResponseData.metadata?.validation_errors as Record<string, string[]> || undefined,
        };
        
        // Handle specific status codes
        switch (status) {
          case 401:
            localStorage.removeItem('auth_token');
            window.location.href = '/auth';
            break;
          case 403:
            console.error('Access forbidden');
            break;
          case 404:
            console.error('Resource not found');
            break;
          case 422:
            console.error('Validation error');
            break;
          case 500:
            console.error('Internal server error');
            break;
          default:
            console.error('Unexpected error:', apiResponseData);
        }
        
        return Promise.reject(apiError);
      } else {
        // Legacy error format (for backward compatibility)
        const legacyData = data as { message?: string; detail?: string; errors?: Record<string, string[]> };
        
        // Handle specific status codes
        switch (status) {
          case 401:
            localStorage.removeItem('auth_token');
            window.location.href = '/auth';
            break;
          case 403:
            console.error('Access forbidden');
            break;
          case 404:
            console.error('Resource not found');
            break;
          case 422:
            console.error('Validation error');
            break;
          case 500:
            console.error('Internal server error');
            break;
          default:
            console.error('Unexpected error:', legacyData);
        }

        // Return standardized error response
        const apiError: ApiError = {
          status,
          message: legacyData?.message || legacyData?.detail || 'An error occurred',
          data: legacyData,
          errors: legacyData?.errors,
        };
        
        return Promise.reject(apiError);
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.request);
      const networkError: ApiError = {
        status: 0,
        message: 'Network error - please check your connection',
        data: null,
      };
      return Promise.reject(networkError);
    } else {
      // Other error
      console.error('Request setup error:', error.message);
      const requestError: ApiError = {
        status: 0,
        message: error.message || 'Request failed',
        data: null,
      };
      return Promise.reject(requestError);
    }
  }
);

// API functions
export const api = {
  // Job management
  jobs: {
    // Get all jobs with optional filtering
    getAll: async (query?: JobsQuery): Promise<Job[]> => {
      const params = query ? new URLSearchParams(
        Object.entries(query).reduce((acc, [key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              acc[key] = value.join(',');
            } else {
              acc[key] = String(value);
            }
          }
          return acc;
        }, {} as Record<string, string>)
      ) : undefined;
      
      // Use limit=10 by default to prevent large response issues
      if (!params?.has('limit')) {
        if (!params) {
          const newParams = new URLSearchParams();
          newParams.set('limit', '10');
          const response = await apiClient.get<JobListResponse>('/jobs/list', { params: newParams });
          const result = extractApiResult(response.data);
          return result.jobs || [];
        } else {
          params.set('limit', '10');
        }
      }
      
      const response = await apiClient.get<JobListResponse>('/jobs/list', { params });
      const result = extractApiResult(response.data);
      return result.jobs || [];
    },

    // Get paginated jobs list
    getList: async (query?: JobsQuery): Promise<{ jobs: Job[]; total_count: number }> => {
      const params = query ? new URLSearchParams(
        Object.entries(query).reduce((acc, [key, value]) => {
          if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
              acc[key] = value.join(',');
            } else {
              acc[key] = String(value);
            }
          }
          return acc;
        }, {} as Record<string, string>)
      ) : undefined;
      
      const response = await apiClient.get<JobListResponse>('/jobs/list', { params });
      const result = extractApiResult(response.data);
      return { 
        jobs: result.jobs || [], 
        total_count: result.total_count || 0 
      };
    },

    // Get job by ID
    getById: async (id: string): Promise<Job> => {
      const response = await apiClient.get<JobDetailResponse>(`/jobs/${id}`);
      const result = extractApiResult(response.data);
      if (!result.job) {
        throw new Error('Job not found');
      }
      return result.job;
    },

    // Create new job
    create: async (jobData: CreateJobRequest): Promise<{ job_id: string }> => {
      const response = await apiClient.post<CreateJobResponse>('/jobs/create', jobData);
      const result = extractApiResult(response.data);
      if (!result.job_id) {
        throw new Error('Failed to create job');
      }
      return { job_id: result.job_id };
    },

    // Update job
    update: async (id: string, updates: Partial<Job>): Promise<Job> => {
      const response = await apiClient.patch<JobDetailResponse>(`/jobs/${id}`, updates);
      const result = extractApiResult(response.data);
      if (!result.job) {
        throw new Error('Failed to update job');
      }
      return result.job;
    },

    // Delete job
    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`/jobs/${id}`);
    },

    // Cancel job
    cancel: async (id: string): Promise<Job> => {
      const response = await apiClient.post<JobDetailResponse>(`/jobs/${id}/cancel`);
      const result = extractApiResult(response.data);
      if (!result.job) {
        throw new Error('Failed to cancel job');
      }
      return result.job;
    },

    // Get job status
    getStatus: async (id: string): Promise<JobStatus> => {
      const response = await apiClient.get<JobStatusResponse>(`/jobs/${id}/status`);
      const result = extractApiResult(response.data);
      return result.status || 'pending';
    },

    // Get multiple job statuses (batch operation)
    getBatchStatus: async (ids: string[]): Promise<Record<string, JobStatusUpdate>> => {
      const request: BatchStatusRequest = { job_ids: ids };
      const response = await apiClient.post<BatchStatusResponse>('/jobs/batch/status', request);
      const result = extractApiResult(response.data);
      return result.statuses || {};
    },

    // Get jobs with minimal data for polling (lighter weight)
    getAllMinimal: async (query?: { limit?: number; offset?: number }): Promise<JobMinimal[]> => {
      const params = query ? new URLSearchParams(
        Object.entries(query).reduce((acc, [key, value]) => {
          if (value !== undefined && value !== null) {
            acc[key] = String(value);
          }
          return acc;
        }, {} as Record<string, string>)
      ) : undefined;
      
      const response = await apiClient.get<JobsMinimalResponse>('/jobs/minimal', { params });
      const result = extractApiResult(response.data);
      return result.jobs || [];
    },

    // Retry failed job
    retry: async (id: string): Promise<{ job_id: string; status: string }> => {
      const response = await apiClient.post<JobRetryResponse>(`/jobs/${id}/retry`);
      const result = extractApiResult(response.data);
      if (!result.job_id) {
        throw new Error('Failed to retry job');
      }
      return {
        job_id: result.job_id,
        status: result.new_status
      };
    },

    // Rerun any job (creates new job with same config)
    rerun: async (id: string): Promise<{ original_job_id: string; new_job_id: string; new_job: Job }> => {
      const response = await apiClient.post<JobRerunResponse>(`/jobs/${id}/rerun`);
      const result = extractApiResult(response.data);
      
      if (!result.new_job_id) {
        throw new Error('Failed to rerun job');
      }
      
      return {
        original_job_id: result.original_job_id,
        new_job_id: result.new_job_id,
        new_job: result.new_job
      };
    },

    // Get job logs
    getLogs: async (id: string): Promise<string[]> => {
      const response = await apiClient.get<JobLogsResponse>(`/jobs/${id}/logs`);
      const result = extractApiResult(response.data);
      return result.logs || [];
    },
  },

  // Agent management
  agents: {
    // Get all agents from discovery system
    getAll: async (): Promise<AgentInfo[]> => {
      const response = await apiClient.get<AgentListResponse>('/agents');
      const result = extractApiResult(response.data);
      return result.agents || [];
    },

    // Get detailed agent information by identifier
    getById: async (agentId: string): Promise<AgentInfo> => {
      const response = await apiClient.get<AgentDetailResponse>(`/agents/${agentId}`);
      const result = extractApiResult(response.data);
      return result;
    },

    // Get agent schema for dynamic form generation
    getSchema: async (agentId: string): Promise<AgentSchemaResult> => {
      const response = await apiClient.get<AgentSchemaResponse>(`/agents/${agentId}/schema`);
      const result = extractApiResult(response.data);
      return result;
    },

    // Get agent configuration
    getConfig: async (agentId: string): Promise<Record<string, unknown>> => {
      const response = await apiClient.get<ApiResponse<{ config: Record<string, unknown> }>>(`/agents/${agentId}/config`);
      const result = extractApiResult(response.data);
      return result.config || {};
    },

    // Test agent connectivity
    test: async (agentId: string): Promise<boolean> => {
      try {
        const response = await apiClient.post<ApiResponse<{ test_result: boolean }>>(`/agents/${agentId}/test`);
        const result = extractApiResult(response.data);
        return result.test_result || false;
      } catch {
        return false;
      }
    },
  },

  // Schedule management
  schedules: {
    // Get all schedules
    getAll: async (): Promise<any[]> => {
      const response = await apiClient.get<ApiResponse<any[]>>('/schedules/');
      const result = extractApiResult(response.data);
      return result || [];
    },

    // Get schedule by ID
    getById: async (id: string): Promise<any> => {
      const response = await apiClient.get<ApiResponse<any>>(`/schedules/${id}`);
      return extractApiResult(response.data);
    },

    // Create new schedule
    create: async (scheduleData: any): Promise<any> => {
      const response = await apiClient.post<ApiResponse<any>>('/schedules/', scheduleData);
      return response.data;
    },

    // Update schedule
    update: async (id: string, scheduleData: any): Promise<any> => {
      const response = await apiClient.put<ApiResponse<any>>(`/schedules/${id}`, scheduleData);
      return extractApiResult(response.data);
    },

    // Delete schedule
    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`/schedules/${id}`);
    },

    // Enable schedule
    enable: async (id: string): Promise<any> => {
      const response = await apiClient.post<ApiResponse<any>>(`/schedules/${id}/enable`);
      return extractApiResult(response.data);
    },

    // Disable schedule
    disable: async (id: string): Promise<any> => {
      const response = await apiClient.post<ApiResponse<any>>(`/schedules/${id}/disable`);
      return extractApiResult(response.data);
    },

    // Run schedule immediately
    runNow: async (id: string): Promise<any> => {
      const response = await apiClient.post<ApiResponse<any>>(`/schedules/${id}/run-now`);
      return extractApiResult(response.data);
    },

    // Get upcoming jobs for a schedule
    getUpcomingJobs: async (scheduleId: string, limit: number = 10): Promise<any[]> => {
      const response = await apiClient.get<ApiResponse<{ jobs: any[] }>>(`/schedules/${scheduleId}/upcoming`, {
        params: { limit }
      });
      const result = extractApiResult(response.data);
      return result.jobs || [];
    },

    // Get schedule history
    getHistory: async (scheduleId: string, limit: number = 50, offset: number = 0): Promise<{ jobs: any[]; total_count: number }> => {
      const response = await apiClient.get<ApiResponse<any[]>>(`/schedules/${scheduleId}/history`, {
        params: { limit, offset }
      });
      const result = extractApiResult(response.data);
      
      // Backend follows unified ApiResponse pattern:
      // - result: Array of ScheduleExecutionHistory objects directly
      // - metadata.count: Number of records returned
      const jobs = Array.isArray(result) ? result : [];
      const totalCount = (response.data.metadata?.count as number) || jobs.length;
      
      return { 
        jobs, 
        total_count: totalCount 
      };
    },

    // Get upcoming jobs for all schedules
    getAllUpcoming: async (limit: number = 10): Promise<any[]> => {
      const response = await apiClient.get<ApiResponse<any[]>>('/schedules/upcoming', {
        params: { limit }
      });
      const result = extractApiResult(response.data);
      return result || [];
    },
  },

  // Authentication
  auth: {
    // Login
    login: async (credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> => {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
      const result = extractApiResult(response.data);
      if (!result.user) {
        throw new Error('Login failed');
      }
      return result;
    },

    // Logout
    logout: async (): Promise<void> => {
      await apiClient.post('/auth/logout');
      localStorage.removeItem('auth_token');
    },

    // Get current user
    getCurrentUser: async (): Promise<User> => {
      const response = await apiClient.get<AuthUserResponse>('/auth/me');
      const result = extractApiResult(response.data);
      if (!result.user) {
        throw new Error('Failed to get user data');
      }
      return result.user;
    },

    // Refresh auth token
    refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
      const response = await apiClient.post<AuthTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
      const result = extractApiResult(response.data);
      if (!result.access_token) {
        throw new Error('Failed to refresh token');
      }
      return {
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        token_type: result.token_type,
        expires_in: result.expires_in
      };
    },
  },

  // Health check and system stats
  health: {
    check: async (): Promise<HealthCheck> => {
      const response = await apiClient.get<HealthResponse>('/health');
      const result = extractApiResult(response.data);
      return result || { 
        status: 'unhealthy', 
        timestamp: new Date().toISOString(),
        version: 'unknown'
      };
    },

    getStats: async (): Promise<SystemStats> => {
      const response = await apiClient.get<SystemStatsResponse>('/stats');
      const result = extractApiResult(response.data);
      return result.statistics || {
        total_jobs: 0,
        jobs_by_status: { pending: 0, running: 0, completed: 0, failed: 0, cancelled: 0 },
        jobs_by_agent_identifier: {},
        average_processing_time_by_agent: {},
        success_rate_percentage: 0,
        peak_concurrent_jobs: 0,
        uptime_hours: 0,
      };
    },
  },
};

// Helper functions for error handling
export const handleApiError = (error: unknown): string => {
  // Handle ApiError instances (from axios interceptor)
  if (error && typeof error === 'object' && 'status' in error) {
    const apiError = error as ApiError;
    
    // Check if the error data contains ApiResponse format
    if (apiError.data && typeof apiError.data === 'object' && 'success' in apiError.data) {
      const apiResponseData = apiError.data as ApiResponse<unknown>;
      
      // Extract error from ApiResponse
      if (apiResponseData.error) {
        return apiResponseData.error;
      }
      
      // Fall back to message if no error field
      if (apiResponseData.message) {
        return apiResponseData.message;
      }
      
      // Check for validation errors in metadata
      if (apiResponseData.metadata?.validation_errors) {
        const validationErrors = apiResponseData.metadata.validation_errors as Record<string, string[]>;
        return formatValidationErrors(validationErrors);
      }
    }
    
    // Handle validation errors from ApiError
    if (apiError.status === 422 && apiError.errors) {
      return formatValidationErrors(apiError.errors);
    }
    
    // Fall back to ApiError message
    return apiError.message || 'An unexpected error occurred';
  }
  
  // Handle direct ApiResponse error objects (in case they're passed directly)
  if (error && typeof error === 'object' && 'success' in error && !(error as ApiResponse<unknown>).success) {
    const apiResponse = error as ApiResponse<unknown>;
    
    if (apiResponse.error) {
      return apiResponse.error;
    }
    
    if (apiResponse.message) {
      return apiResponse.message;
    }
    
    // Check for validation errors in metadata
    if (apiResponse.metadata?.validation_errors) {
      const validationErrors = apiResponse.metadata.validation_errors as Record<string, string[]>;
      return formatValidationErrors(validationErrors);
    }
    
    return 'API request failed';
  }
  
  // Handle Error instances
  if (error instanceof Error) {
    return error.message;
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Default fallback
  return 'An unexpected error occurred';
};

// Helper function to format validation errors
export const formatValidationErrors = (errors: Record<string, string[]>): string => {
  return Object.entries(errors)
    .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
    .join('; ');
};

// Helper function to check if error is a validation error
export const isValidationError = (error: ApiError): error is ApiError & { status: 422 } => {
  return error.status === 422 && Boolean(error.errors);
};

// Helper function to set auth token
export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

// Helper function to clear auth token
export const clearAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};

// Helper function to check if user is authenticated
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('auth_token');
};

// Utility functions for ApiResponse parsing and error handling

/**
 * Check if an ApiResponse indicates success
 * @param response - The ApiResponse to check
 * @returns true if the response indicates success
 */
export const isApiSuccess = <T>(response: ApiResponse<T>): boolean => {
  return response.success === true;
};

/**
 * Extract error message from an ApiResponse
 * @param response - The ApiResponse to extract error from
 * @returns The error message or a default message
 */
export const getApiError = (response: ApiResponse<unknown>): string => {
  if (response.success) {
    return '';
  }
  
  // Primary error field
  if (response.error) {
    return response.error;
  }
  
  // Fall back to message
  if (response.message) {
    return response.message;
  }
  
  // Check for validation errors in metadata
  if (response.metadata?.validation_errors) {
    const validationErrors = response.metadata.validation_errors as Record<string, string[]>;
    return formatValidationErrors(validationErrors);
  }
  
  return 'An error occurred';
};

/**
 * Handle an ApiResponse, returning the result on success or null on error
 * @param response - The ApiResponse to handle
 * @returns The result data on success, null on error
 */
export const handleApiResponse = <T>(response: ApiResponse<T>): T | null => {
  if (isApiSuccess(response) && response.result !== null && response.result !== undefined) {
    return response.result;
  }
  return null;
};

/**
 * Extract result from ApiResponse with error handling
 * @param response - The ApiResponse to extract from
 * @returns The result data
 * @throws Error if the response indicates failure or missing result
 */
export const extractApiResultSafe = <T>(response: ApiResponse<T>): T => {
  if (!isApiSuccess(response)) {
    throw new Error(getApiError(response));
  }
  
  if (response.result === null || response.result === undefined) {
    throw new Error('API response missing result data');
  }
  
  return response.result;
};

// React hook for ApiResponse handling

/**
 * Custom React hook for handling ApiResponse patterns
 * @returns Object with state and handlers for ApiResponse operations
 */
export const useApiResponse = <T>() => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Execute an API call that returns ApiResponse<T>
   * @param apiCall - Function that returns a Promise<ApiResponse<T>>
   * @returns Promise that resolves to the result data or null on error
   */
  const execute = useCallback(async (apiCall: () => Promise<ApiResponse<T>>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiCall();
      
      if (isApiSuccess(response)) {
        const result = response.result;
        setData(result);
        return result;
      } else {
        const errorMessage = getApiError(response);
        setError(errorMessage);
        setData(null);
        return null;
      }
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      setData(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Reset the hook state
   */
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    isSuccess: data !== null && error === null,
    hasError: error !== null,
  };
};

// Export types for use in components
export type {
  Job,
  JobMinimal,
  JobStatus,
  CreateJobRequest,
  User,
  ApiError,
  HealthCheck,
  SystemStats,
} from './types';

export default apiClient; 