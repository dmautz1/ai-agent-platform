// ============================================================================
// BASE API TYPES
// ============================================================================

export interface ApiResponse<T = any> {
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
  data?: any;
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

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
  terms_accepted: boolean;
}

export interface RegisterResponse {
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

export type JobPriority = 'low' | 'normal' | 'high' | 'urgent';

export type AgentType = 'text_processing' | 'summarization' | 'web_scraping';

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
  metadata?: Record<string, any>;
}

export interface Job extends BaseJob {
  data: JobData;
  result?: JobResult;
  error_message?: string;
  progress?: JobProgress;
  execution_time_ms?: number;
}

// Job Data Types (input for different agent types)
export interface BaseJobData {
  agent_type: AgentType;
  title: string;
}

export interface TextProcessingJobData extends BaseJobData {
  agent_type: 'text_processing';
  input_text: string;
  operation?: 'sentiment_analysis' | 'entity_extraction' | 'summarization' | 'translation';
  language?: string;
  max_length?: number;
  temperature?: number;
}

export interface SummarizationJobData extends BaseJobData {
  agent_type: 'summarization';
  input_text?: string;
  input_url?: string;
  max_summary_length?: number;
  format?: 'paragraph' | 'bullet_points' | 'key_highlights';
  language?: string;
  include_quotes?: boolean;
}

export interface WebScrapingJobData extends BaseJobData {
  agent_type: 'web_scraping';
  input_url: string;
  selectors?: string[];
  max_pages?: number;
  wait_time?: number;
  follow_links?: boolean;
  extract_images?: boolean;
  extract_metadata?: boolean;
}

export type JobData = TextProcessingJobData | SummarizationJobData | WebScrapingJobData;

// Job Result Types (output from different agent types)
export interface BaseJobResult {
  type: AgentType;
  processing_time_ms: number;
  token_count?: number;
}

export interface TextProcessingResult extends BaseJobResult {
  type: 'text_processing';
  processed_text: string;
  analysis?: {
    sentiment?: {
      score: number;
      label: 'positive' | 'negative' | 'neutral';
      confidence: number;
    };
    entities?: Array<{
      text: string;
      label: string;
      confidence: number;
      start: number;
      end: number;
    }>;
    keywords?: Array<{
      text: string;
      score: number;
    }>;
  };
}

export interface SummarizationResult extends BaseJobResult {
  type: 'summarization';
  summary: string;
  key_points?: string[];
  original_length: number;
  summary_length: number;
  compression_ratio: number;
  quotes?: string[];
}

export interface WebScrapingResult extends BaseJobResult {
  type: 'web_scraping';
  scraped_data: {
    url: string;
    title?: string;
    content: string;
    images?: Array<{
      url: string;
      alt?: string;
      caption?: string;
    }>;
    links?: Array<{
      url: string;
      text: string;
      type: 'internal' | 'external';
    }>;
    metadata?: Record<string, any>;
  };
  pages_processed: number;
  success_rate: number;
}

export type JobResult = TextProcessingResult | SummarizationResult | WebScrapingResult;

export interface JobProgress {
  percentage: number;
  stage: string;
  estimated_remaining_ms?: number;
  current_step?: string;
  total_steps?: number;
}

// Job Request/Response Types
export interface CreateJobRequest {
  data: JobData;
  priority?: JobPriority;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface CreateJobResponse {
  success: boolean;
  message: string;
  job_id: string;
  estimated_completion_time?: string;
}

export interface UpdateJobRequest {
  priority?: JobPriority;
  tags?: string[];
  metadata?: Record<string, any>;
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
  agent_type?: AgentType | AgentType[];
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

export interface AgentInfo {
  type: AgentType;
  name: string;
  description: string;
  version: string;
  capabilities: string[];
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  configuration: AgentConfiguration;
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

export interface AgentTypesResponse {
  agents: AgentInfo[];
  total: number;
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
  jobs_by_agent_type: Record<AgentType, number>;
  average_processing_time_by_agent: Record<AgentType, number>;
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
  data?: Record<string, any>;
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
  filters?: Record<string, any>;
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

// Type guards for job data
export const isTextProcessingJobData = (data: JobData): data is TextProcessingJobData => {
  return data.agent_type === 'text_processing';
};

export const isSummarizationJobData = (data: JobData): data is SummarizationJobData => {
  return data.agent_type === 'summarization';
};

export const isWebScrapingJobData = (data: JobData): data is WebScrapingJobData => {
  return data.agent_type === 'web_scraping';
};

// Type guards for job results
export const isTextProcessingResult = (result: JobResult): result is TextProcessingResult => {
  return result.type === 'text_processing';
};

export const isSummarizationResult = (result: JobResult): result is SummarizationResult => {
  return result.type === 'summarization';
};

export const isWebScrapingResult = (result: JobResult): result is WebScrapingResult => {
  return result.type === 'web_scraping';
}; 