// Authentication Types
// Supabase-aligned authentication types for the AI Agent Platform

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  metadata?: Record<string, unknown>;
  user_metadata?: Record<string, unknown>;
  app_metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

// LoginResponse is now defined in api.ts 