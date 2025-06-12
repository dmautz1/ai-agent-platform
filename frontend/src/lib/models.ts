// ============================================================================
// BASE API TYPES
// ============================================================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
  timestamp?: string;
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

// ============================================================================
// USER & AUTHENTICATION TYPES
// ============================================================================

export interface User {
  id: string;
  email: string;
  name?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  profile?: UserProfile;
}

export interface UserProfile {
  avatar_url?: string;
  bio?: string;
  timezone?: string;
  language?: string;
  notifications_enabled: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

// ============================================================================
// JOB TYPES
// ============================================================================

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type JobPriority = 'low' | 'normal' | 'high' | 'urgent' | number;

export interface BaseJob {
  id: string;
  status: JobStatus;
  priority: JobPriority;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  user_id: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface Job extends BaseJob {
  data: JobData;
  result?: string;
  result_format?: string;
  error_message?: string;
  progress?: JobProgress;
  execution_time_ms?: number;
}

// Modern generic job data types
export interface BaseJobData {
  agent_identifier: string; // Generic agent identifier
  title: string;
  [key: string]: unknown; // Allow arbitrary data fields for different agents
}

// Generic job data interface - agents can define their own data structure
export interface GenericJobData extends BaseJobData {
  agent_identifier: string;
  title: string;
  // All other fields are dynamic based on the agent's requirements
}

// Modern generic job data type - supports any agent
export type JobData = GenericJobData;

// Modern generic job result types
export interface BaseJobResult {
  agent_identifier: string; // Generic agent identifier
  processing_time_ms: number;
  token_count?: number;
  [key: string]: unknown; // Allow arbitrary result fields for different agents
}

// Generic job result interface - agents can define their own result structure
export interface GenericJobResult extends BaseJobResult {
  agent_identifier: string;
  processing_time_ms: number;
  // All other fields are dynamic based on the agent's output
}

// Modern generic job result type - supports any agent
export type JobResult = GenericJobResult;

export interface JobProgress {
  percentage: number;
  stage: string;
  estimated_remaining_ms?: number;
  current_step?: string;
  total_steps?: number;
}

// Job Request/Response Types
export interface CreateJobRequest {
  agent_identifier: string;
  data: Omit<JobData, 'agent_identifier'>; // Job data without agent_identifier since it's at top level
  priority?: number | JobPriority;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface CreateJobResponse {
  success: boolean;
  message: string;
  job_id: string;
  estimated_completion_time?: string;
}

export interface JobListResponse {
  success: boolean;
  message: string;
  jobs: Job[];
  total_count: number;
}

export interface JobDetailResponse {
  success: boolean;
  message: string;
  job: Job;
}

export interface UpdateJobRequest {
  priority?: JobPriority;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface JobStatusUpdate {
  status: JobStatus;
  updated_at: string;
  progress?: JobProgress;
}

export interface BatchStatusRequest {
  job_ids: string[];
}

export interface BatchStatusResponse {
  statuses: Record<string, JobStatusUpdate>;
}

export interface JobsQuery {
  status?: JobStatus | JobStatus[];
  agent_identifier?: string | string[]; // Modern generic agent identifiers
  user_id?: string;
  created_after?: string;
  created_before?: string;
  tags?: string[];
  page?: number;
  per_page?: number;
  sort_by?: 'created_at' | 'updated_at' | 'priority';
  sort_order?: 'asc' | 'desc';
}

export interface JobsListResponse {
  jobs: Job[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  filters_applied: Partial<JobsQuery>;
}

export interface JobMinimal {
  id: string;
  status: JobStatus;
  updated_at: string;
  priority: JobPriority;
}

// ============================================================================
// AGENT TYPES
// ============================================================================

// Modern agent info from discovery system
export interface AgentInfo {
  identifier: string;
  name: string;
  description: string;
  class_name: string;
  lifecycle_state: string;
  supported_environments: string[];
  version: string;
  enabled: boolean;
  has_error: boolean;
  error_message?: string | null;
  created_at: string;
  last_updated: string;
  runtime_info?: Record<string, unknown>;
  instance_available?: boolean;
}

export interface AgentConfiguration {
  max_input_length?: number;
  supported_languages?: string[];
  default_temperature?: number;
  rate_limit?: {
    requests_per_minute: number;
    requests_per_hour: number;
  };
  timeout_ms?: number;
  retry_attempts?: number;
}

// ============================================================================
// SYSTEM TYPES
// ============================================================================

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  components: {
    database: ComponentHealth;
    agents: ComponentHealth;
    storage: ComponentHealth;
    external_apis: ComponentHealth;
  };
  metrics?: SystemMetrics;
}

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms?: number;
  last_check: string;
  error?: string;
}

export interface SystemMetrics {
  active_jobs: number;
  completed_jobs_24h: number;
  failed_jobs_24h: number;
  average_processing_time_ms: number;
  system_load: number;
  memory_usage_mb: number;
  disk_usage_percentage: number;
}

export interface SystemStats {
  total_jobs: number;
  jobs_by_status: Record<JobStatus, number>;
  jobs_by_agent_identifier: Record<string, number>; // Generic agent identifiers
  average_processing_time_by_agent: Record<string, number>; // Generic agent identifiers
  success_rate_percentage: number;
  peak_concurrent_jobs: number;
  uptime_hours: number;
}

// ============================================================================
// NOTIFICATION TYPES
// ============================================================================

export interface Notification {
  id: string;
  type: 'job_completed' | 'job_failed' | 'system_alert' | 'account_update';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
  action_url?: string;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  push_notifications: boolean;
  job_completion_notifications: boolean;
  job_failure_notifications: boolean;
  system_alerts: boolean;
  marketing_emails: boolean;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface FileUpload {
  id: string;
  filename: string;
  size: number;
  mime_type: string;
  url: string;
  created_at: string;
}

export interface SearchQuery {
  q: string;
  filters?: Record<string, unknown>;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  query: SearchQuery;
  suggestions?: string[];
  facets?: Record<string, Array<{ value: string; count: number }>>;
}

// ============================================================================
// TYPE GUARDS AND UTILITY FUNCTIONS
// ============================================================================

// Modern type guards for generic job data
export const isGenericJobData = (data: JobData): data is GenericJobData => {
  return 'agent_identifier' in data;
};

// Modern type guards for generic job results
export const isGenericJobResult = (result: JobResult): result is GenericJobResult => {
  return 'agent_identifier' in result;
};

// Schema and Dynamic Form types
export interface FormFieldSchema {
  type: string;
  title?: string;
  description?: string;
  default?: unknown;
  enum?: string[];
  format?: string;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  pattern?: string;
  form_field_type: string;
}

export interface AgentSchema {
  model_name: string;
  model_class: string;
  title: string;
  description: string;
  type: string;
  properties: Record<string, FormFieldSchema>;
  required: string[];
  definitions?: Record<string, unknown>;
}

export interface AgentSchemaResponse {
  status: string;
  message?: string;
  agent_id: string;
  agent_name: string;
  description: string;
  agent_found?: boolean;
  instance_available?: boolean;
  available_models: string[];
  schemas: Record<string, AgentSchema>;
  error?: string;
}

// Dynamic Job Data interface for schema-based jobs
export interface DynamicJobData {
  agent_identifier: string;
  title: string;
  [key: string]: unknown; // Dynamic fields based on agent schema
} 