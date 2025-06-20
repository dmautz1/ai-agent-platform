// Agent Types
// Agent-related types for the AI Agent Platform

export interface AgentInfo {
  identifier: string;
  name: string;
  description: string;
  class_name: string;
  version: string;
  lifecycle_state: string;
  supported_environments: string[];
  created_at: string;
  last_updated: string;
  metadata_extras: Record<string, unknown>;
  is_loaded: boolean;
  framework_version: string;
  execution_count: number;
  last_execution_time: string | null;
  status: string;
  endpoints: unknown[];
  models: unknown[];
  // Legacy fields for backward compatibility
  enabled?: boolean;
  has_error?: boolean;
  error_message?: string | null;
  runtime_info?: Record<string, unknown>;
  instance_available?: boolean;
}

export interface AgentSchema {
  model_name: string;
  model_class?: string;
  title: string;
  description: string;
  type: string;
  properties: Record<string, FormFieldSchema>;
  required: string[];
  definitions?: Record<string, unknown>;
}

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
  form_field_type?: string;
  placeholder?: string;
  anyOf?: Array<{ type: string; maxLength?: number; [key: string]: unknown }>;
}

export interface AgentSchemaLegacy {
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