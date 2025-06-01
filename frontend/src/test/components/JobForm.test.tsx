import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { JobForm } from '../../components/JobForm'
import { mockSupabaseClient } from '../utils'

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      create: vi.fn(),
    }
  },
  handleApiError: vi.fn((error) => error.message || 'An error occurred'),
}))

// Mock Supabase
vi.mock('../../lib/supabase', () => ({
  supabase: mockSupabaseClient,
}))

// Mock toast hook
const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
}
vi.mock('../../components/ui/toast', () => ({
  useToast: () => mockToast,
}))

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
)

describe('JobForm', () => {
  const mockOnJobCreated = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    expect(screen.getByRole('textbox', { name: /job title/i })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /agent type/i })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /advanced parameters/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create job/i })).toBeInTheDocument()
  })

  it('shows validation errors for required fields', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /create job/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument()
      expect(screen.getByText(/agent type is required/i)).toBeInTheDocument()
    })
  })

  it('shows appropriate input fields based on agent type selection', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Select text processing agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Text Processing'))

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /input text/i })).toBeInTheDocument()
      expect(screen.queryByRole('textbox', { name: /input url/i })).not.toBeInTheDocument()
    })
  })

  it('shows URL input for web scraping agent type', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Select web scraping agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Web Scraping'))

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /input url/i })).toBeInTheDocument()
      expect(screen.queryByRole('textbox', { name: /input text/i })).not.toBeInTheDocument()
    })
  })

  it('shows both text and URL inputs for summarization agent type', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Select summarization agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Summarization'))

    await waitFor(() => {
      expect(screen.getByRole('textbox', { name: /input text.*optional/i })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /input url.*optional/i })).toBeInTheDocument()
    })
  })

  it('successfully creates a text processing job', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    ;(api.jobs.create as any).mockResolvedValue({
      job_id: 'test-job-id',
      success: true,
    })

    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Fill in required fields
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'Test Text Processing Job')
    
    // Select agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Text Processing'))

    // Fill in text input
    await user.type(screen.getByRole('textbox', { name: /input text/i }), 'This is test text to process')

    // Submit form
    await user.click(screen.getByRole('button', { name: /create job/i }))

    await waitFor(() => {
      expect(api.jobs.create).toHaveBeenCalledWith({
        data: {
          agent_type: 'text_processing',
          title: 'Test Text Processing Job',
          input_text: 'This is test text to process',
          operation: 'sentiment_analysis',
          language: 'en',
        },
        priority: 'normal',
        tags: [],
        metadata: {
          created_from: 'web_ui',
          user_agent: navigator.userAgent,
        },
      })
      expect(mockOnJobCreated).toHaveBeenCalledWith('test-job-id')
      expect(mockToast.success).toHaveBeenCalled()
    })
  })

  it('validates URL input for web scraping', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Fill in required fields
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'Test Web Scraping Job')
    
    // Select web scraping agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Web Scraping'))

    // Enter invalid URL
    await user.type(screen.getByRole('textbox', { name: /input url/i }), 'invalid-url')

    // Submit form
    await user.click(screen.getByRole('button', { name: /create job/i }))

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid url/i)).toBeInTheDocument()
    })
  })

  it('validates JSON parameters', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Fill in required fields
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'Test Job')
    
    // Select agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Text Processing'))

    // Fill in text input
    await user.type(screen.getByRole('textbox', { name: /input text/i }), 'Test text')

    // Enter invalid JSON in parameters
    await user.type(screen.getByRole('textbox', { name: /advanced parameters/i }), 'invalid json')

    // Submit form
    await user.click(screen.getByRole('button', { name: /create job/i }))

    await waitFor(() => {
      expect(screen.getByText(/parameters must be valid json/i)).toBeInTheDocument()
    })
  })

  it('handles submission errors gracefully', async () => {
    const user = userEvent.setup()
    const { api, handleApiError } = await import('../../lib/api')
    
    const errorMessage = 'API Error occurred'
    ;(api.jobs.create as any).mockRejectedValue(new Error(errorMessage))
    ;(handleApiError as any).mockReturnValue(errorMessage)

    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Fill in required fields
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'Test Job')
    
    // Select agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Text Processing'))

    // Fill in text input
    await user.type(screen.getByRole('textbox', { name: /input text/i }), 'Test text')

    // Submit form
    await user.click(screen.getByRole('button', { name: /create job/i }))

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(mockToast.error).toHaveBeenCalledWith(`Failed to create job: ${errorMessage}`, {
        title: 'Error',
      })
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()
    const { api } = await import('../../lib/api')
    
    // Mock delayed response
    ;(api.jobs.create as any).mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ job_id: 'test-job-id' }), 100)
      )
    )

    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Fill in required fields
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'Test Job')
    
    // Select agent type
    await user.click(screen.getByRole('combobox', { name: /agent type/i }))
    await user.click(screen.getByText('Text Processing'))

    // Fill in text input
    await user.type(screen.getByRole('textbox', { name: /input text/i }), 'Test text')

    // Submit form
    await user.click(screen.getByRole('button', { name: /create job/i }))

    expect(screen.getByText(/creating job/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /creating job/i })).toBeDisabled()
  })

  it('clears validation errors when user starts typing', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <JobForm onJobCreated={mockOnJobCreated} />
      </TestWrapper>
    )

    // Submit form to trigger validation errors
    await user.click(screen.getByRole('button', { name: /create job/i }))

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument()
    })

    // Start typing in title field
    await user.type(screen.getByRole('textbox', { name: /job title/i }), 'T')

    // Error should be cleared
    expect(screen.queryByText(/title is required/i)).not.toBeInTheDocument()
  })
}) 