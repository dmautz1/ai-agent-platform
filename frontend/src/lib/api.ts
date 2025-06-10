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
  JobListResponse,
  JobDetailResponse,
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
  AgentSchemaResponse,
  
  // System types
  HealthCheck,
  SystemStats,
  
  // Utility types
} from './models';

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
      
      const response = await apiClient.get<JobListResponse>('/jobs', { params });
      return response.data.jobs || [];
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
      
      const response = await apiClient.get<JobListResponse>('/jobs', { params });
      
      // Convert backend JobListResponse to frontend JobsListResponse format
      return {
        jobs: response.data.jobs || [],
        pagination: {
          total: response.data.total_count || 0,
          page: 1, // Default values since backend doesn't return pagination info yet
          per_page: response.data.total_count || 50,
          total_pages: 1,
          has_next: false,
          has_prev: false
        },
        filters_applied: query || {}
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

    // Rerun any job (creates new job with same config)
    rerun: async (id: string): Promise<{ original_job_id: string; new_job_id: string; original_job_status: string; data: Job }> => {
      const response = await apiClient.post<{
        success: boolean;
        message?: string;
        original_job_id: string;
        new_job_id: string;
        original_job_status: string;
        data: Job;
      }>(`/jobs/${id}/rerun`);
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to rerun job');
      }
      return {
        original_job_id: response.data.original_job_id,
        new_job_id: response.data.new_job_id,
        original_job_status: response.data.original_job_status,
        data: response.data.data
      };
    },

    // Get job logs
    getLogs: async (id: string): Promise<string[]> => {
      const response = await apiClient.get<ApiResponse<string[]>>(`/jobs/${id}/logs`);
      return response.data.data || [];
    },
  },

  // Agent management
  agents: {
    // NEW: Get all agents from discovery system
    getAll: async (): Promise<AgentInfo[]> => {
      const response = await apiClient.get<{ agents?: Record<string, AgentInfo> }>('/agents');
      const agents = response.data?.agents || {};
      
      // Convert the agents object to an array of AgentInfo
      return Object.values(agents).map((agent: AgentInfo) => ({
        identifier: agent.identifier,
        name: agent.name,
        description: agent.description,
        class_name: agent.class_name,
        lifecycle_state: agent.lifecycle_state,
        supported_environments: agent.supported_environments || [],
        version: agent.version || '1.0.0',
        enabled: agent.enabled,
        has_error: agent.has_error,
        error_message: agent.error_message,
        created_at: agent.created_at,
        last_updated: agent.last_updated
      }));
    },

    // NEW: Get detailed agent information by identifier
    getById: async (agentId: string): Promise<AgentInfo> => {
      const response = await apiClient.get<{ agent?: AgentInfo }>(`/agents/${agentId}`);
      const agent = response.data?.agent;
      
      if (!agent) {
        throw new Error(`Agent ${agentId} not found`);
      }
      
      return {
        identifier: agent.identifier,
        name: agent.name,
        description: agent.description,
        class_name: agent.class_name,
        lifecycle_state: agent.lifecycle_state,
        supported_environments: agent.supported_environments || [],
        version: agent.version || '1.0.0',
        enabled: agent.enabled,
        has_error: agent.has_error,
        error_message: agent.error_message,
        created_at: agent.created_at,
        last_updated: agent.last_updated,
        runtime_info: agent.runtime_info,
        instance_available: agent.instance_available
      };
    },

    // NEW: Get agent schema for dynamic form generation
    getSchema: async (agentId: string): Promise<AgentSchemaResponse> => {
      const response = await apiClient.get<AgentSchemaResponse>(`/agents/${agentId}/schema`);
      return response.data;
    },

    // Get agent configuration
    getConfig: async (agentId: string): Promise<Record<string, unknown>> => {
      const response = await apiClient.get<ApiResponse<Record<string, unknown>>>(`/agents/${agentId}/config`);
      return response.data.data || {};
    },

    // Test agent connectivity
    test: async (agentId: string): Promise<boolean> => {
      try {
        const response = await apiClient.post<ApiResponse<{ success: boolean }>>(`/agents/${agentId}/test`);
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
  JobPriority,
  CreateJobRequest,
  CreateJobResponse,
  User,
  ApiError,
  HealthCheck,
  SystemStats,
} from './models';

export default apiClient; 