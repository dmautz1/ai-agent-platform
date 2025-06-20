// Job Types
// Simplified job types for the AI Agent Platform

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Job {
  id: string;
  status: JobStatus;
  priority: number;
  title?: string;
  agent_identifier?: string;
  data: Record<string, unknown>; // Flexible data structure for any agent
  result?: string;
  result_format?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  user_id: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  progress?: JobProgress;
  execution_time_ms?: number;
}

export interface CreateJobRequest {
  agent_identifier: string;
  title: string;
  data: Record<string, unknown>;
  priority?: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface UpdateJobRequest {
  priority?: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface JobProgress {
  percentage: number;
  stage: string;
  estimated_remaining_ms?: number;
  current_step?: string;
  total_steps?: number;
}

export interface JobStatusUpdate {
  status: JobStatus;
  updated_at: string;
  progress?: JobProgress;
}

export interface BatchStatusRequest {
  job_ids: string[];
}

export interface JobsQuery {
  status?: JobStatus | JobStatus[];
  agent_identifier?: string | string[];
  user_id?: string;
  created_after?: string;
  created_before?: string;
  tags?: string[];
  page?: number;
  per_page?: number;
  sort_by?: 'created_at' | 'updated_at' | 'priority';
  sort_order?: 'asc' | 'desc';
}

export interface JobMinimal {
  id: string;
  status: JobStatus;
  agent_identifier: string;
  title: string;
  created_at: string;
  updated_at: string;
}

// Dashboard-compatible job interface that includes minimal data plus required fields
export interface JobDashboard extends JobMinimal {
  user_id: string;
  priority: number;
  data: Record<string, unknown>;
} 