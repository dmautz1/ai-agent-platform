import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import IndexPage from '../../pages/index'
import { AuthProvider } from '../../contexts/AuthContext'
import { mockSupabaseClient, mockJobs } from '../utils'

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getList: vi.fn(),
      getById: vi.fn(),
      delete: vi.fn(),
    },
    agents: {
      getTypes: vi.fn(),
    }
  },
  handleApiError: vi.fn((error) => error.message || 'An error occurred'),
}))

// Mock Supabase
vi.mock('../../lib/supabase', () => ({
  supabase: mockSupabaseClient,
}))

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('IndexPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSupabaseClient.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user123', email: 'test@example.com' } },
      error: null
    })
    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: { access_token: 'token123' } },
      error: null
    })
    mockSupabaseClient.auth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } }
    })
  })

  it('renders page title and navigation', async () => {
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: [],
      pagination: { page: 1, per_page: 10, total: 0 }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/job dashboard/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create new job/i })).toBeInTheDocument()
    })
  })

  it('displays jobs when loaded', async () => {
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
      expect(screen.getByText('Summarization Job')).toBeInTheDocument()
      expect(screen.getByText('Web Scraping Job')).toBeInTheDocument()
    })
  })

  it('shows empty state when no jobs exist', async () => {
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: [],
      pagination: { page: 1, per_page: 10, total: 0 }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/no jobs found/i)).toBeInTheDocument()
      expect(screen.getByText(/get started by creating your first job/i)).toBeInTheDocument()
    })
  })

  it('filters jobs by status', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Filter by completed status
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i })
    await user.click(statusFilter)
    await user.click(screen.getByText('Completed'))

    await waitFor(() => {
      expect(api.jobs.getList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'completed'
        })
      )
    })
  })

  it('filters jobs by agent type', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Filter by text processing agent type
    const agentFilter = screen.getByRole('combobox', { name: /filter by agent type/i })
    await user.click(agentFilter)
    await user.click(screen.getByText('Text Processing'))

    await waitFor(() => {
      expect(api.jobs.getList).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_type: 'text_processing'
        })
      )
    })
  })

  it('searches jobs by title', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Search for jobs
    const searchInput = screen.getByRole('textbox', { name: /search jobs/i })
    await user.type(searchInput, 'Test Job')

    await waitFor(() => {
      expect(api.jobs.getList).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'Test Job'
        })
      )
    })
  })

  it('navigates to create job page', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: [],
      pagination: { page: 1, per_page: 10, total: 0 }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    const createButton = await screen.findByRole('button', { name: /create new job/i })
    await user.click(createButton)

    expect(mockNavigate).toHaveBeenCalledWith('/jobs/new')
  })

  it('navigates to job details when clicking on job', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs.slice(0, 1),
      pagination: { page: 1, per_page: 10, total: 1 }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    const jobCard = screen.getByText('Test Job').closest('div')
    await user.click(jobCard!)

    expect(mockNavigate).toHaveBeenCalledWith(`/jobs/${mockJobs[0].id}`)
  })

  it('handles pagination', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: 25 }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Click next page
    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(api.jobs.getList).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      )
    })
  })

  it('handles API errors gracefully', async () => {
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockRejectedValue(new Error('API Error'))
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/error loading jobs/i)).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching jobs', async () => {
    const { api } = await import('../../lib/api')
    
    // Mock delayed response
    ;(api.jobs.getList as any).mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          jobs: mockJobs,
          pagination: { page: 1, per_page: 10, total: mockJobs.length }
        }), 100)
      )
    )
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })
  })

  it('refreshes job list when refresh button is clicked', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Clear the mock call count
    ;(api.jobs.getList as any).mockClear()

    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i })
    await user.click(refreshButton)

    expect(api.jobs.getList).toHaveBeenCalledTimes(1)
  })

  it('clears filters when clear button is clicked', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.getList as any).mockResolvedValue({
      jobs: mockJobs,
      pagination: { page: 1, per_page: 10, total: mockJobs.length }
    })
    ;(api.agents.getTypes as any).mockResolvedValue([])

    render(
      <TestWrapper>
        <IndexPage />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Job')).toBeInTheDocument()
    })

    // Apply filters first
    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i })
    await user.click(statusFilter)
    await user.click(screen.getByText('Completed'))

    // Clear filters
    const clearButton = screen.getByRole('button', { name: /clear filters/i })
    await user.click(clearButton)

    await waitFor(() => {
      expect(api.jobs.getList).toHaveBeenCalledWith(
        expect.objectContaining({
          status: undefined,
          agent_type: undefined,
          search: undefined
        })
      )
    })
  })
}) 