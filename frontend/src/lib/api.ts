import axios, { type AxiosInstance, type AxiosResponse, AxiosError } from 'axios';
import type {
  // Base API types
  BaseApiResponse,
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
  AgentSchemaResponse,
  
  // System types
  HealthCheck,
  SystemStats,
  
  // Utility types
} from './types';

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
    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { message?: string; detail?: string; errors?: Record<string, string[]> };

      console.error(`API Error ${status}:`, data);

      // Handle specific status codes
      switch (status) {
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
          console.error('Unexpected error:', data);
      }

      // Return standardized error response
      const apiError: ApiError = {
        status,
        message: data?.message || data?.detail || 'An error occurred',
        data: data,
        errors: data?.errors,
      };
      
      return Promise.reject(apiError);
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
      
      const response = await apiClient.get<JobListResponse>('/jobs/list', { params });
      return response.data.jobs || [];
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
      return { 
        jobs: response.data.jobs || [], 
        total_count: response.data.total_count || 0 
      };
    },

    // Get job by ID
    getById: async (id: string): Promise<Job> => {
      const response = await apiClient.get<JobDetailResponse>(`/jobs/${id}`);
      if (!response.data.job) {
        throw new Error('Job not found');
      }
      return response.data.job;
    },

    // Create new job
    create: async (jobData: CreateJobRequest): Promise<{ job_id: string }> => {
      const response = await apiClient.post<CreateJobResponse>('/jobs/create', jobData);
      if (!response.data.job_id) {
        throw new Error('Failed to create job');
      }
      return { job_id: response.data.job_id };
    },

    // Update job
    update: async (id: string, updates: Partial<Job>): Promise<Job> => {
      const response = await apiClient.patch<JobDetailResponse>(`/jobs/${id}`, updates);
      if (!response.data.job) {
        throw new Error('Failed to update job');
      }
      return response.data.job;
    },

    // Delete job
    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`/jobs/${id}`);
    },

    // Cancel job
    cancel: async (id: string): Promise<Job> => {
      const response = await apiClient.post<JobDetailResponse>(`/jobs/${id}/cancel`);
      if (!response.data.job) {
        throw new Error('Failed to cancel job');
      }
      return response.data.job;
    },

    // Get job status
    getStatus: async (id: string): Promise<JobStatus> => {
      const response = await apiClient.get<JobStatusResponse>(`/jobs/${id}/status`);
      return response.data.status || 'pending';
    },

    // Get multiple job statuses (batch operation)
    getBatchStatus: async (ids: string[]): Promise<Record<string, JobStatusUpdate>> => {
      const request: BatchStatusRequest = { job_ids: ids };
      const response = await apiClient.post<BatchStatusResponse>('/jobs/batch/status', request);
      return response.data.statuses || {};
    },

    // Get jobs with minimal data for polling (lighter weight)
    getAllMinimal: async (): Promise<JobMinimal[]> => {
      const response = await apiClient.get<JobsMinimalResponse>('/jobs/minimal');
      return response.data.jobs || [];
    },

    // Retry failed job
    retry: async (id: string): Promise<{ job_id: string; status: string }> => {
      const response = await apiClient.post<JobRetryResponse>(`/jobs/${id}/retry`);
      if (!response.data.job_id) {
        throw new Error('Failed to retry job');
      }
      return {
        job_id: response.data.job_id,
        status: response.data.new_status
      };
    },

    // Rerun any job (creates new job with same config)
    rerun: async (id: string): Promise<{ original_job_id: string; new_job_id: string; new_job: Job }> => {
      const response = await apiClient.post<JobRerunResponse>(`/jobs/${id}/rerun`);
      
      if (!response.data.new_job_id) {
        throw new Error('Failed to rerun job');
      }
      
      return {
        original_job_id: response.data.original_job_id,
        new_job_id: response.data.new_job_id,
        new_job: response.data.new_job
      };
    },

    // Get job logs
    getLogs: async (id: string): Promise<string[]> => {
      const response = await apiClient.get<JobLogsResponse>(`/jobs/${id}/logs`);
      return response.data.logs || [];
    },
  },

  // Agent management
  agents: {
    // Get all agents from discovery system
    getAll: async (): Promise<AgentInfo[]> => {
      const response = await apiClient.get<AgentListResponse>('/agents');
      return response.data.agents || [];
    },

    // Get detailed agent information by identifier
    getById: async (agentId: string): Promise<AgentInfo> => {
      const response = await apiClient.get<AgentDetailResponse>(`/agents/${agentId}`);
      if (!response.data) {
        throw new Error(`Agent ${agentId} not found`);
      }
      return response.data;
    },

    // Get agent schema for dynamic form generation
    getSchema: async (agentId: string): Promise<AgentSchemaResponse> => {
      const response = await apiClient.get<AgentSchemaResponse>(`/agents/${agentId}/schema`);
      if (!response.data) {
        throw new Error(`Schema not found for agent ${agentId}`);
      }
      return response.data;
    },

    // Get agent configuration
    getConfig: async (agentId: string): Promise<Record<string, unknown>> => {
      const response = await apiClient.get<BaseApiResponse & { config: Record<string, unknown> }>(`/agents/${agentId}/config`);
      return response.data.config || {};
    },

    // Test agent connectivity
    test: async (agentId: string): Promise<boolean> => {
      try {
        const response = await apiClient.post<BaseApiResponse & { test_result: boolean }>(`/agents/${agentId}/test`);
        return response.data.test_result || false;
      } catch {
        return false;
      }
    },
  },

  // Authentication
  auth: {
    // Login
    login: async (credentials: LoginRequest): Promise<LoginResponse> => {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
      if (!response.data.user) {
        throw new Error('Login failed');
      }
      return response.data;
    },

    // Logout
    logout: async (): Promise<void> => {
      await apiClient.post('/auth/logout');
      localStorage.removeItem('auth_token');
    },

    // Get current user
    getCurrentUser: async (): Promise<User> => {
      const response = await apiClient.get<AuthUserResponse>('/auth/me');
      if (!response.data.user) {
        throw new Error('Failed to get user data');
      }
      return response.data.user;
    },

    // Refresh auth token
    refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
      const response = await apiClient.post<AuthTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
      if (!response.data.access_token) {
        throw new Error('Failed to refresh token');
      }
      return {
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
        expires_in: response.data.expires_in
      };
    },
  },

  // Health check and system stats
  health: {
    check: async (): Promise<HealthCheck> => {
      const response = await apiClient.get<HealthResponse>('/health');
      return response.data || { 
        status: 'unhealthy', 
        timestamp: new Date().toISOString(),
        version: 'unknown'
      };
    },

    getStats: async (): Promise<SystemStats> => {
      const response = await apiClient.get<SystemStatsResponse>('/stats');
      return response.data.statistics || {
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
  // Handle ApiError instances
  if (error && typeof error === 'object' && 'status' in error) {
    const apiError = error as ApiError;
    if (apiError.status === 422 && apiError.errors) {
      return formatValidationErrors(apiError.errors);
    }
    return apiError.message || 'An unexpected error occurred';
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