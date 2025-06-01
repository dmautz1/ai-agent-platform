import React from 'react'
import { render } from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

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
  },
  loading: false,
  signIn: vi.fn(),
  signOut: vi.fn(),
}

// Sample test data
export const mockJob = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  user_id: 'test-user-id',
  status: 'completed' as const,
  priority: 'normal' as const,
  data: {
    agent_type: 'text_processing' as const,
    title: 'Test Job',
    input_text: 'Test text to process',
    operation: 'sentiment_analysis' as const,
  },
  result: {
    type: 'text_processing' as const,
    processing_time_ms: 1500,
    processed_text: 'Test text to process',
    analysis: {
      sentiment: {
        score: 0.95,
        label: 'positive' as const,
        confidence: 0.95,
      },
    },
  },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
}

export const mockJobs = [
  mockJob,
  {
    ...mockJob,
    id: 'abc12345-e89b-12d3-a456-426614174001',
    status: 'running' as const,
    priority: 'high' as const,
    data: {
      agent_type: 'summarization' as const,
      title: 'Summarization Job',
      input_text: 'Long text to summarize',
      max_summary_length: 200,
    },
    result: undefined,
  },
  {
    ...mockJob,
    id: 'def67890-e89b-12d3-a456-426614174002',
    status: 'failed' as const,
    priority: 'low' as const,
    data: {
      agent_type: 'web_scraping' as const,
      title: 'Web Scraping Job',
      input_url: 'https://example.com',
      max_pages: 5,
    },
    result: undefined,
    error_message: 'Connection timeout',
  },
]

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[]
}

export function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) {
  const { initialEntries = ['/'], ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        {children}
      </BrowserRouter>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Mock API responses
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
        data: {
          text_processing: {
            name: 'Text Processing Agent',
            description: 'Process and analyze text content',
            status: 'active',
          },
          summarization: {
            name: 'Summarization Agent',
            description: 'Summarize text, audio, and video content',
            status: 'active',
          },
          web_scraping: {
            name: 'Web Scraping Agent',
            description: 'Extract data from websites',
            status: 'active',
          },
        },
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
export * from '@testing-library/react'
export { vi } from 'vitest' 