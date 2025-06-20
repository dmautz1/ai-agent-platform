// API Types
// Standardized API response patterns for the AI Agent Platform

import type { Job, JobStatus, JobMinimal, JobStatusUpdate } from './job';
import type { AgentInfo, AgentSchema } from './agent';
import type { User, AuthTokens } from './auth';
import type { SystemStats } from './system';

// Unified API Response interface matching backend implementation
export interface ApiResponse<T = unknown> {
  success: boolean;           // Operation success status
  result: T | null;          // Response data (null on error)
  message: string | null;    // Human-readable message
  error: string | null;      // Error description (null on success)
  metadata: Record<string, unknown> | null;  // Additional context and debugging info
}

export interface ApiError {
  status: number;
  message: string;
  data?: unknown;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Job-specific result types (these go inside ApiResponse<T>)
export interface CreateJobResult {
  job_id: string;
  job: Job;
}

export interface JobListResult {
  jobs: Job[];
  total_count: number;
}

export interface JobDetailResult {
  job: Job;
}

export interface JobStatusResult {
  status: JobStatus;
}

export interface JobRetryResult {
  job_id: string;
  new_status: string;
}

export interface JobRerunResult {
  original_job_id: string;
  new_job_id: string;
  new_job: Job;
}

export interface JobLogsResult {
  job_id: string;
  logs: string[];
  log_count: number;
}

export interface BatchStatusResult {
  statuses: Record<string, JobStatusUpdate>;
}

export interface JobsMinimalResult {
  jobs: JobMinimal[];
  total_count: number;
}

// Agent-specific result types
export interface AgentListResult {
  agents: AgentInfo[];
  total_count: number;
  loaded_count: number;
  discovery_info: {
    last_scan: string | null;
    scan_count: number;
  };
}

export interface AgentDetailResult extends AgentInfo {
  // Agent details are merged with base info
}

export interface AgentSchemaResult {
  status: string;
  message?: string;
  agent_found: boolean;
  instance_available: boolean;
  agent_id: string;
  agent_name: string;
  description: string;
  available_models: string[];
  schemas: Record<string, AgentSchema>;
  error?: string;
}

// System result types
export interface HealthResult {
  status: string;
  version: string;
  timestamp: string;
}

export interface SystemStatsResult {
  statistics: SystemStats;
  timestamp: string;
}

export interface SystemConfigResult {
  config: {
    environment: string;
    version: string;
    debug: boolean;
    cors_enabled: boolean;
    timestamp: string;
  };
}

// Auth result types
export interface LoginResult {
  user: User;
  tokens: AuthTokens;
}

export interface AuthUserResult {
  user: User;
}

export interface AuthTokenResult {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Convenience type aliases for complete API responses
export type CreateJobResponse = ApiResponse<CreateJobResult>;
export type JobListResponse = ApiResponse<JobListResult>;
export type JobDetailResponse = ApiResponse<JobDetailResult>;
export type JobStatusResponse = ApiResponse<JobStatusResult>;
export type JobRetryResponse = ApiResponse<JobRetryResult>;
export type JobRerunResponse = ApiResponse<JobRerunResult>;
export type JobLogsResponse = ApiResponse<JobLogsResult>;
export type BatchStatusResponse = ApiResponse<BatchStatusResult>;
export type JobsMinimalResponse = ApiResponse<JobsMinimalResult>;

export type AgentListResponse = ApiResponse<AgentListResult>;
export type AgentDetailResponse = ApiResponse<AgentDetailResult>;
export type AgentSchemaResponse = ApiResponse<AgentSchemaResult>;

export type HealthResponse = ApiResponse<HealthResult>;
export type SystemStatsResponse = ApiResponse<SystemStatsResult>;
export type SystemConfigResponse = ApiResponse<SystemConfigResult>;

export type LoginResponse = ApiResponse<LoginResult>;
export type AuthUserResponse = ApiResponse<AuthUserResult>;
export type AuthTokenResponse = ApiResponse<AuthTokenResult>;

// Remove unused import
// import type { JobsQuery } from './job'; 