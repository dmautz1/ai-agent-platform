import axios, { type AxiosInstance, type AxiosResponse, AxiosError } from 'axios';
import type {
  // Base API types
  ApiResponse,
  ApiError,
  
  // Job types
  Job,
  JobMinimal,
  JobStatus,
  CreateJobRequest,
  CreateJobResponse,
  JobsQuery,
  JobsListResponse,
  BatchStatusRequest,
  JobStatusUpdate,
  
  // User & Auth types
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  AuthTokens,
  
  // Agent types
  AgentInfo,
  AgentTypesResponse,
  
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

    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        data: config.data,
        params: config.params,
      });
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
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`API Response: ${response.status}`, response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;

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
      
      const response = await apiClient.get<ApiResponse<Job[]>>('/jobs', { params });
      return response.data.data || [];
    },

    // Get paginated jobs list
    getList: async (query?: JobsQuery): Promise<JobsListResponse> => {
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
      
      const response = await apiClient.get<ApiResponse<JobsListResponse>>('/jobs/list', { params });
      return response.data.data || { jobs: [], pagination: { total: 0, page: 1, per_page: 20, total_pages: 0, has_next: false, has_prev: false }, filters_applied: {} };
    },

    // Get job by ID
    getById: async (id: string): Promise<Job> => {
      const response = await apiClient.get<ApiResponse<Job>>(`/jobs/${id}`);
      if (!response.data.data) {
        throw new Error('Job not found');
      }
      return response.data.data;
    },

    // Create new job
    create: async (jobData: CreateJobRequest): Promise<CreateJobResponse> => {
      const response = await apiClient.post<CreateJobResponse>('/jobs', jobData);
      if (!response.data.job_id) {
        throw new Error('Failed to create job');
      }
      return response.data;
    },

    // Update job
    update: async (id: string, updates: Partial<Job>): Promise<Job> => {
      const response = await apiClient.patch<ApiResponse<Job>>(`/jobs/${id}`, updates);
      if (!response.data.data) {
        throw new Error('Failed to update job');
      }
      return response.data.data;
    },

    // Delete job
    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`/jobs/${id}`);
    },

    // Cancel job
    cancel: async (id: string): Promise<Job> => {
      const response = await apiClient.post<ApiResponse<Job>>(`/jobs/${id}/cancel`);
      if (!response.data.data) {
        throw new Error('Failed to cancel job');
      }
      return response.data.data;
    },

    // Get job status
    getStatus: async (id: string): Promise<JobStatus> => {
      const response = await apiClient.get<ApiResponse<{ status: JobStatus }>>(`/jobs/${id}/status`);
      return response.data.data?.status || 'pending';
    },

    // Get multiple job statuses (batch operation)
    getBatchStatus: async (ids: string[]): Promise<Record<string, JobStatusUpdate>> => {
      const request: BatchStatusRequest = { job_ids: ids };
      const response = await apiClient.post<ApiResponse<Record<string, JobStatusUpdate>>>('/jobs/batch/status', request);
      return response.data.data || {};
    },

    // Get jobs with minimal data for polling (lighter weight)
    getAllMinimal: async (): Promise<JobMinimal[]> => {
      const response = await apiClient.get<ApiResponse<JobMinimal[]>>('/jobs/minimal');
      return response.data.data || [];
    },

    // Retry failed job
    retry: async (id: string): Promise<Job> => {
      const response = await apiClient.post<ApiResponse<Job>>(`/jobs/${id}/retry`);
      if (!response.data.data) {
        throw new Error('Failed to retry job');
      }
      return response.data.data;
    },

    // Get job logs
    getLogs: async (id: string): Promise<string[]> => {
      const response = await apiClient.get<ApiResponse<string[]>>(`/jobs/${id}/logs`);
      return response.data.data || [];
    },
  },

  // Agent management
  agents: {
    // Get available agent types
    getTypes: async (): Promise<AgentInfo[]> => {
      const response = await apiClient.get<ApiResponse<AgentTypesResponse>>('/agents/types');
      return response.data.data?.agents || [];
    },

    // Get agent configuration
    getConfig: async (agentType: string): Promise<Record<string, any>> => {
      const response = await apiClient.get<ApiResponse<Record<string, any>>>(`/agents/${agentType}/config`);
      return response.data.data || {};
    },

    // Test agent connectivity
    test: async (agentType: string): Promise<boolean> => {
      try {
        const response = await apiClient.post<ApiResponse<{ success: boolean }>>(`/agents/${agentType}/test`);
        return response.data.data?.success || false;
      } catch {
        return false;
      }
    },
  },

  // Authentication
  auth: {
    // Login
    login: async (credentials: LoginRequest): Promise<LoginResponse> => {
      const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
      if (!response.data.data) {
        throw new Error('Login failed');
      }
      return response.data.data;
    },

    // Register
    register: async (userData: RegisterRequest): Promise<RegisterResponse> => {
      const response = await apiClient.post<ApiResponse<RegisterResponse>>('/auth/register', userData);
      if (!response.data.data) {
        throw new Error('Registration failed');
      }
      return response.data.data;
    },

    // Logout
    logout: async (): Promise<void> => {
      await apiClient.post('/auth/logout');
      localStorage.removeItem('auth_token');
    },

    // Get current user
    getCurrentUser: async (): Promise<User> => {
      const response = await apiClient.get<ApiResponse<User>>('/auth/me');
      if (!response.data.data) {
        throw new Error('Failed to get user data');
      }
      return response.data.data;
    },

    // Refresh auth token
    refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
      const response = await apiClient.post<ApiResponse<AuthTokens>>('/auth/refresh', { refresh_token: refreshToken });
      if (!response.data.data) {
        throw new Error('Failed to refresh token');
      }
      return response.data.data;
    },
  },

  // Health check and system stats
  health: {
    check: async (): Promise<HealthCheck> => {
      const response = await apiClient.get<ApiResponse<HealthCheck>>('/health');
      return response.data.data || { 
        status: 'unhealthy' as const, 
        timestamp: new Date().toISOString(),
        version: 'unknown',
        environment: 'unknown',
        components: {
          database: { status: 'unhealthy' as const, last_check: new Date().toISOString() },
          agents: { status: 'unhealthy' as const, last_check: new Date().toISOString() },
          storage: { status: 'unhealthy' as const, last_check: new Date().toISOString() },
          external_apis: { status: 'unhealthy' as const, last_check: new Date().toISOString() },
        }
      };
    },

    getStats: async (): Promise<SystemStats> => {
      const response = await apiClient.get<ApiResponse<SystemStats>>('/health/stats');
      return response.data.data || {
        total_jobs: 0,
        jobs_by_status: { pending: 0, running: 0, completed: 0, failed: 0, cancelled: 0 },
        jobs_by_agent_type: { text_processing: 0, summarization: 0, web_scraping: 0 },
        average_processing_time_by_agent: { text_processing: 0, summarization: 0, web_scraping: 0 },
        success_rate_percentage: 0,
        peak_concurrent_jobs: 0,
        uptime_hours: 0,
      };
    },
  },
};

// Helper functions for error handling
export const handleApiError = (error: any): string => {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  if (error?.data?.message) {
    return error.data.message;
  }

  if (error?.data?.detail) {
    return error.data.detail;
  }
  
  return 'An unexpected error occurred';
};

// Helper function to format validation errors
export const formatValidationErrors = (errors: Record<string, string[]>): string => {
  return Object.entries(errors)
    .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
    .join('; ');
};

// Helper function to check if error is a validation error
export const isValidationError = (error: any): error is ApiError & { status: 422 } => {
  return error?.status === 422 && error?.errors;
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
  JobPriority,
  CreateJobRequest,
  CreateJobResponse,
  User,
  ApiError,
  HealthCheck,
  SystemStats,
} from './types';

export default apiClient; 