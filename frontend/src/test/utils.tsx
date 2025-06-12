import React from 'react'
import { render } from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { ToastProvider } from '@/components/ui/toast'
import type { Job } from '@/lib/models'

// Mock the Supabase client
export const mockSupabaseClient = {
  auth: {
    signInWithPassword: vi.fn(),
    signOut: vi.fn(),
    getSession: vi.fn(),
    onAuthStateChange: vi.fn(),
    getUser: vi.fn(),
  },
  from: vi.fn(() => ({
    select: vi.fn(() => ({
      eq: vi.fn(() => ({
        order: vi.fn(() => ({
          data: [],
          error: null,
        })),
      })),
      order: vi.fn(() => ({
        data: [],
        error: null,
      })),
    })),
    insert: vi.fn(() => ({
      data: null,
      error: null,
    })),
    update: vi.fn(() => ({
      eq: vi.fn(() => ({
        data: null,
        error: null,
      })),
    })),
    delete: vi.fn(() => ({
      eq: vi.fn(() => ({
        data: null,
        error: null,
      })),
    })),
  })),
}

// Mock axios
export const mockAxios = {
  get: vi.fn(() => Promise.resolve({ data: { data: [] } })),
  post: vi.fn(() => Promise.resolve({ data: { data: {} } })),
  put: vi.fn(() => Promise.resolve({ data: { data: {} } })),
  delete: vi.fn(() => Promise.resolve({ data: { data: {} } })),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
}

// Mock auth context
export const mockAuthContext = {
  user: {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user' as const,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    last_login: '2024-01-01T00:00:00Z',
  },
  loading: false,
  session: null,
  tokens: {
    access_token: 'mock-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 3600,
  },
  signIn: vi.fn(),
  signOut: vi.fn(),
  refreshAuth: vi.fn(),
}

// Sample test data with dynamic/generic agent types
export const mockJob: Job = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  user_id: 'test-user-id',
  status: 'completed' as const,
  priority: 'normal' as const,
  data: {
    agent_identifier: 'example_research_agent',
    title: 'Test Research Job',
    query: 'Test query to research',
    max_results: 10,
  } as Job['data'], // Allow flexible data structure for different agents
  result: JSON.stringify({
    agent_identifier: 'example_research_agent',
    processing_time_ms: 1500,
    results: [
      {
        title: 'Test Result 1',
        content: 'Sample research result content',
        relevance_score: 0.95,
      }
    ],
    summary: 'Research completed successfully',
  }), // Job result is stored as string in the Job interface
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
}

// Helper function to create mock agents with dynamic identifiers
export const createMockAgent = (identifier: string, name: string, description: string) => ({
  identifier,
  name,
  description,
  class_name: `${identifier.charAt(0).toUpperCase() + identifier.slice(1)}Agent`,
  lifecycle_state: 'enabled',
  supported_environments: ['dev', 'prod'],
  version: '1.0.0',
  enabled: true,
  has_error: false,
  created_at: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-01T00:00:00Z'
});

// Helper function to create mock jobs with dynamic agent data
export const createMockJob = (overrides: Partial<Job> = {}) => ({
  ...mockJob,
  ...overrides,
  id: overrides.id || `job-${Math.random().toString(36).substr(2, 9)}`,
});

export const mockJobs = [
  mockJob,
  createMockJob({
    id: 'abc12345-e89b-12d3-a456-426614174001',
    status: 'running',
    priority: 'high',
    data: {
      agent_identifier: 'content_summarizer',
      title: 'Document Summary Job',
      content: 'Long document content to summarize...',
      max_length: 200,
      format: 'bullet_points',
    },
    result: undefined,
  }),
  createMockJob({
    id: 'def67890-e89b-12d3-a456-426614174002',
    status: 'failed',
    priority: 'low',
    data: {
      agent_identifier: 'web_data_extractor', 
      title: 'Web Data Extraction Job',
      target_url: 'https://example.com',
      selectors: ['h1', '.content', '#main'],
      max_depth: 3,
    },
    result: undefined,
    error_message: 'Target website is unreachable',
  }),
]

// Dynamic mock agents for testing
export const mockAgents = [
  createMockAgent('example_research_agent', 'Research Agent', 'Conducts research on various topics'),
  createMockAgent('content_summarizer', 'Content Summarizer', 'Summarizes long-form content'),
  createMockAgent('web_data_extractor', 'Web Data Extractor', 'Extracts structured data from websites'),
  createMockAgent('sentiment_analyzer', 'Sentiment Analyzer', 'Analyzes sentiment in text content'),
  createMockAgent('document_processor', 'Document Processor', 'Processes and analyzes documents'),
];

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[]
}

export function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) {
  const { ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ToastProvider maxToasts={3}>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </ToastProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Custom render function with authentication context
export function renderWithAuth(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) {
  const { ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <ToastProvider maxToasts={3}>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </ToastProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Mock API responses with dynamic agent data
export const mockApiResponses = {
  jobs: {
    success: {
      data: {
        data: mockJobs,
        pagination: {
          page: 1,
          limit: 10,
          total: mockJobs.length,
        },
      },
    },
    error: {
      response: {
        status: 500,
        data: {
          error: 'Internal server error',
          message: 'Something went wrong',
        },
      },
    },
  },
  job: {
    success: {
      data: {
        data: mockJob,
      },
    },
    notFound: {
      response: {
        status: 404,
        data: {
          error: 'Not found',
          message: 'Job not found',
        },
      },
    },
  },
  agents: {
    success: {
      data: {
        agents: mockAgents.reduce((acc, agent) => {
          acc[agent.identifier] = agent;
          return acc;
        }, {} as Record<string, typeof mockAgents[0]>),
      },
    },
  },
}

// Mock React Router hooks
export const mockNavigate = vi.fn()
export const mockLocation = {
  pathname: '/',
  search: '',
  hash: '',
  state: null,
  key: 'default',
}

// Helper for testing async components
export const waitForLoadingToFinish = () => {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

// Mock environment variables
export const mockEnvVars = {
  VITE_SUPABASE_URL: 'https://test-project.supabase.co',
  VITE_SUPABASE_ANON_KEY: 'test-anon-key',
  VITE_API_BASE_URL: 'http://localhost:8000',
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

// User event utilities
export { userEvent } from '@testing-library/user-event'

// Re-export testing library functions
// eslint-disable-next-line react-refresh/only-export-components
export * from '@testing-library/react'
export { vi } from 'vitest'

// Mock useAuth hook
const mockUseAuth = {
  user: null,
  loading: false,
  session: null,
  tokens: {
    access_token: 'mock-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 3600,
  },
  signIn: vi.fn(),
  signOut: vi.fn(),
  refreshAuth: vi.fn(),
} 