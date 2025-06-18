// System Types
// System health and monitoring types for the AI Agent Platform

export interface HealthCheck {
  status: string;
  timestamp: string;
  version: string;
}

export interface SystemStats {
  total_jobs: number;
  jobs_by_status: Record<string, number>;
  jobs_by_agent_identifier: Record<string, number>;
  average_processing_time_by_agent: Record<string, number>;
  success_rate_percentage: number;
  peak_concurrent_jobs: number;
  uptime_hours: number;
} 