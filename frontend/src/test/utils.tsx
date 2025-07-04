import React from 'react'
import { render } from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'
import { vi, expect } from 'vitest'
import type { Job } from '../lib/types'
import type { ApiResponse } from '../lib/types/api'

// Define mock components locally to ensure they work
const BrowserRouter = ({ children }: { children: React.ReactNode }) => (
  <div data-testid="mock-browser-router">{children}</div>
)

const ToastProvider = ({ children }: { children: React.ReactNode }) => (
  <div data-testid="mock-toast-provider">{children}</div>
)

// ApiResponse helper functions for testing
export function createMockApiResponse<T>(
  result: T,
  success: boolean = true,
  message?: string,
  error?: string,
  metadata?: Record<string, any>
): ApiResponse<T> {
  return {
    success,
    result: success ? result : null,
    message: message || (success ? 'Operation successful' : 'Operation failed'),
    error: error || (!success ? 'Unknown error' : null),
    metadata: metadata || null,
  }
}

export function createMockApiSuccessResponse<T>(
  result: T,
  message?: string,
  metadata?: Record<string, any>
): ApiResponse<T> {
  return createMockApiResponse(result, true, message, undefined, metadata)
}

export function createMockApiErrorResponse(
  error: string,
  message?: string,
  metadata?: Record<string, any>
): ApiResponse<null> {
  return createMockApiResponse(null, false, message, error, metadata)
}

export function createMockApiValidationErrorResponse(
  validationErrors: any[],
  message?: string
): ApiResponse<null> {
  return createMockApiResponse(null, false, message || 'Validation failed', 'Validation failed', {
    validation_errors: validationErrors,
    error_type: 'VALIDATION_ERROR'
  })
}

// ApiResponse Validation Utilities for Frontend Testing
export function validateApiResponseStructure<T>(response: ApiResponse<T>): boolean {
  if (!response || typeof response !== 'object') {
    throw new Error('Response must be an object')
  }
  
  // Check required fields
  if (!('success' in response)) {
    throw new Error("Response missing 'success' field")
  }
  if (typeof response.success !== 'boolean') {
    throw new Error("'success' field must be boolean")
  }
  
  // Check optional fields exist (can be null)
  if (!('result' in response)) {
    throw new Error("Response missing 'result' field")
  }
  if (!('message' in response)) {
    throw new Error("Response missing 'message' field")
  }
  if (!('error' in response)) {
    throw new Error("Response missing 'error' field")
  }
  if (!('metadata' in response)) {
    throw new Error("Response missing 'metadata' field")
  }
  
  // Validate success/error consistency
  if (response.success) {
    if (response.error !== null) {
      throw new Error('Successful response should not have error field set')
    }
  } else {
    if (response.error === null) {
      throw new Error('Failed response must have error field set')
    }
    if (typeof response.error !== 'string') {
      throw new Error('Error field must be a string')
    }
  }
  
  return true
}

export function assertApiSuccessResponse<T>(
  response: ApiResponse<T>, 
  expectedResult?: T
): void {
  validateApiResponseStructure(response)
  
  if (response.success !== true) {
    throw new Error(`Expected success=true, got ${response.success}`)
  }
  if (response.error !== null) {
    throw new Error(`Expected error=null, got ${response.error}`)
  }
  
  if (expectedResult !== undefined) {
    expect(response.result).toEqual(expectedResult)
  }
}

export function assertApiErrorResponse<T>(
  response: ApiResponse<T>, 
  expectedError?: string
): void {
  validateApiResponseStructure(response)
  
  if (response.success !== false) {
    throw new Error(`Expected success=false, got ${response.success}`)
  }
  if (response.error === null) {
    throw new Error('Expected error field to be set')
  }
  if (response.result !== null) {
    throw new Error(`Expected result=null, got ${response.result}`)
  }
  
  if (expectedError !== undefined) {
    if (!response.error.includes(expectedError)) {
      throw new Error(`Expected error to contain '${expectedError}', got '${response.error}'`)
    }
  }
}

export function assertApiValidationErrorResponse<T>(response: ApiResponse<T>): void {
  assertApiErrorResponse(response, 'Validation failed')
  
  if (!response.metadata) {
    throw new Error('Validation error should have metadata')
  }
  if (!response.metadata.validation_errors) {
    throw new Error('Validation error should have validation_errors in metadata')
  }
}

export function extractApiResult<T>(response: ApiResponse<T>): T | null {
  return response.result
}

export function isApiResponseFormat(data: any): data is ApiResponse<any> {
  try {
    validateApiResponseStructure(data)
    return true
  } catch {
    return false
  }
}

// Enhanced Mock Data Generators for Frontend Testing
export function createMockJobListApiResponse(jobs: Job[] = [], totalCount?: number): ApiResponse<{jobs: Job[], total_count: number}> {
  return createMockApiSuccessResponse({
    jobs,
    total_count: totalCount ?? jobs.length
  }, 'Jobs retrieved successfully')
}

export function createMockAgentListApiResponse(agents: Record<string, any> = {}, totalCount?: number): ApiResponse<{agents: Record<string, any>, total_count: number}> {
  return createMockApiSuccessResponse({
    agents,
    total_count: totalCount ?? Object.keys(agents).length
  }, 'Agents retrieved successfully')
}

export function createMockHealthCheckApiResponse(status: string = 'healthy', additionalData: Record<string, any> = {}): ApiResponse<{status: string, timestamp: string, version: string}> {
  return createMockApiSuccessResponse({
    status,
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    ...additionalData
  }, 'Health check completed')
}

export function createMockSchemaApiResponse(schema?: Record<string, any>): ApiResponse<{schema: Record<string, any>}> {
  const defaultSchema = {
    type: 'object',
    properties: {
      prompt: { type: 'string', description: 'The prompt text' },
      max_tokens: { type: 'integer', description: 'Maximum tokens', default: 100 }
    },
    required: ['prompt']
  }
  
  return createMockApiSuccessResponse({
    schema: schema || defaultSchema
  }, 'Schema retrieved successfully')
}

// Performance Testing Utilities for Frontend
export function benchmarkApiResponseSerialization<T>(response: ApiResponse<T>, iterations: number = 1000): number {
  const start = performance.now()
  for (let i = 0; i < iterations; i++) {
    JSON.stringify(response)
  }
  const end = performance.now()
  return (end - start) / iterations
}

export function benchmarkApiResponseDeserialization(responseString: string, iterations: number = 1000): number {
  const start = performance.now()
  for (let i = 0; i < iterations; i++) {
    JSON.parse(responseString)
  }
  const end = performance.now()
  return (end - start) / iterations
}

// Test Data Validation Helpers
export function validateJobDataStructure(jobData: Job): boolean {
  const requiredFields = ['id', 'status', 'data', 'created_at', 'updated_at']
  for (const field of requiredFields) {
    if (!(field in jobData)) {
      throw new Error(`Job data missing required field: ${field}`)
    }
  }
  return true
}

export function validateAgentDataStructure(agentData: any): boolean {
  const requiredFields = ['identifier', 'name', 'description']
  for (const field of requiredFields) {
    if (!(field in agentData)) {
      throw new Error(`Agent data missing required field: ${field}`)
    }
  }
  return true
}

// Mock API Response Generators with Realistic Data
export function createMockJobApiResponse(jobOverrides: Partial<Job> = {}): ApiResponse<Job> {
  const job = createMockJob(jobOverrides)
  return createMockApiSuccessResponse(job, 'Job retrieved successfully')
}

export function createMockAgentApiResponse(agentOverrides: any = {}): ApiResponse<any> {
  const agent = createMockAgent(
    agentOverrides.identifier || 'test_agent',
    agentOverrides.name || 'Test Agent',
    agentOverrides.description || 'Test agent for unit testing'
  )
  return createMockApiSuccessResponse({ ...agent, ...agentOverrides }, 'Agent information retrieved successfully')
}

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

// Mock axios with ApiResponse format
export const mockAxios = {
  get: vi.fn(() => Promise.resolve({ 
    data: createMockApiSuccessResponse({}) 
  })),
  post: vi.fn(() => Promise.resolve({ 
    data: createMockApiSuccessResponse({}) 
  })),
  put: vi.fn(() => Promise.resolve({ 
    data: createMockApiSuccessResponse({}) 
  })),
  delete: vi.fn(() => Promise.resolve({ 
    data: createMockApiSuccessResponse({}) 
  })),
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
    user_metadata: { name: 'Test User' },
    app_metadata: {},
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
  priority: 3,
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
    priority: 5,
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
    priority: 1,
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

// Mock API responses in ApiResponse format
export const mockApiResponses = {
  // Job-related responses
  jobList: createMockApiSuccessResponse({
    jobs: mockJobs,
    total: mockJobs.length,
    page: 1,
    per_page: 10,
    total_pages: 1
  }),
  
  jobDetail: createMockApiSuccessResponse(mockJob),
  
  jobCreate: createMockApiSuccessResponse({
    job_id: 'new-job-123',
    status: 'pending',
    message: 'Job created successfully'
  }),
  
  jobStatus: createMockApiSuccessResponse({
    job_id: mockJob.id,
    status: mockJob.status,
    progress: 100,
    last_updated: mockJob.updated_at
  }),
  
  // Agent-related responses
  agentList: createMockApiSuccessResponse({
    agents: mockAgents,
    total: mockAgents.length
  }),
  
  agentSchema: createMockApiSuccessResponse({
    schema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', title: 'Prompt' },
        max_tokens: { type: 'integer', title: 'Max Tokens', default: 1000 }
      },
      required: ['prompt']
    },
    ui_schema: {
      prompt: { 'ui:widget': 'textarea' }
    }
  }),
  
  // System responses
  systemHealth: createMockApiSuccessResponse({
    status: 'healthy',
    version: '1.0.0',
    environment: 'test',
    timestamp: new Date().toISOString()
  }),
  
  systemStats: createMockApiSuccessResponse({
    total_jobs: 100,
    pending_jobs: 5,
    running_jobs: 2,
    completed_jobs: 85,
    failed_jobs: 8,
    success_rate: 91.4
  }),
  
  // Error responses
  notFound: createMockApiErrorResponse(
    'Resource not found',
    'The requested resource could not be found',
    { error_code: 'NOT_FOUND', status_code: 404 }
  ),
  
  validationError: createMockApiErrorResponse(
    'Validation failed: prompt is required',
    'Input validation failed',
    { 
      error_type: 'validation_error',
      error_count: 1,
      validation_errors: [
        { loc: ['prompt'], msg: 'field required', type: 'value_error.missing' }
      ]
    }
  ),
  
  serverError: createMockApiErrorResponse(
    'Internal server error',
    'An unexpected error occurred',
    { error_code: 'INTERNAL_ERROR', status_code: 500 }
  )
}

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
      <BrowserRouter>
        <ToastProvider>
          {children}
        </ToastProvider>
      </BrowserRouter>
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
      <BrowserRouter>
        <ToastProvider>
          {children}
        </ToastProvider>
      </BrowserRouter>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
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

// Utility function to wait for loading states to finish
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
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