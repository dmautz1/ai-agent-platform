// API Types
// Standardized API response patterns for the AI Agent Platform

import type { Job, JobStatus, JobMinimal, JobStatusUpdate } from './job';
import type { AgentInfo } from './agent';
import type { User, AuthTokens } from './auth';
import type { SystemStats } from './system';

// Base response interface
export interface BaseApiResponse {
  success: boolean;
  message?: string;
  error?: string;
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

// Job-specific response types
export interface CreateJobResponse extends BaseApiResponse {
  job_id: string;
  job: Job;
}

export interface JobListResponse extends BaseApiResponse {
  jobs: Job[];
  total_count: number;
}

export interface JobDetailResponse extends BaseApiResponse {
  job: Job;
}

export interface JobStatusResponse extends BaseApiResponse {
  status: JobStatus;
}

export interface JobRetryResponse extends BaseApiResponse {
  job_id: string;
  new_status: string;
}

export interface JobRerunResponse extends BaseApiResponse {
  original_job_id: string;
  new_job_id: string;
  new_job: Job;
}

export interface JobLogsResponse extends BaseApiResponse {
  job_id: string;
  logs: string[];
  log_count: number;
}

export interface BatchStatusResponse extends BaseApiResponse {
  statuses: Record<string, JobStatusUpdate>;
}

export interface JobsMinimalResponse extends BaseApiResponse {
  jobs: JobMinimal[];
  total_count: number;
}

// Agent-specific response types
export interface AgentListResponse extends BaseApiResponse {
  agents: AgentInfo[];
  total_count: number;
  loaded_count: number;
  discovery_info: {
    last_scan: string | null;
    scan_count: number;
  };
}

export interface AgentDetailResponse extends BaseApiResponse, AgentInfo {
  // Agent details are merged with base response
}

// System response types
export interface HealthResponse extends BaseApiResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface SystemStatsResponse extends BaseApiResponse {
  statistics: SystemStats;
  timestamp: string;
}

export interface SystemConfigResponse extends BaseApiResponse {
  config: {
    environment: string;
    version: string;
    debug: boolean;
    cors_enabled: boolean;
    timestamp: string;
  };
}

// Auth response types
export interface LoginResponse extends BaseApiResponse {
  user: User;
  tokens: AuthTokens;
}

export interface AuthUserResponse extends BaseApiResponse {
  user: User;
}

export interface AuthTokenResponse extends BaseApiResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Remove unused import
// import type { JobsQuery } from './job'; 