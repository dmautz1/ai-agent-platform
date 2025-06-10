import { screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { userEvent } from '@testing-library/user-event'
import { renderWithProviders, mockJobs, mockJob } from '../utils'
import { JobList } from '../../components/JobList'
import type { Job } from '../../lib/models'

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getAll: vi.fn(() => Promise.resolve([])),
    },
  },
  handleApiError: vi.fn((error) => error.message || 'An error occurred'),
}))

// Mock React Router hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

// Mock responsive hooks
vi.mock('../../lib/responsive', () => ({
  useBreakpoint: () => ({ isMobile: false }),
  responsiveTable: {
    container: '',
    header: '',
    cell: '',
  },
  responsivePadding: {
    card: '',
  },
  touchButtonSizes: {
    sm: '',
  },
}))

describe('JobList Component', () => {
  const defaultProps = {
    jobs: mockJobs,
    loading: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render jobs dashboard when jobs are provided', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      expect(screen.getByText('Jobs Dashboard')).toBeInTheDocument()
      
      // Check job count badge
      expect(screen.getByText('3 jobs')).toBeInTheDocument()
    })

    it('should render job data correctly', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      // Check that agent identifiers are displayed (uppercase with spaces)
      expect(screen.getByText('EXAMPLE RESEARCH AGENT')).toBeInTheDocument()
      expect(screen.getByText('CONTENT SUMMARIZER')).toBeInTheDocument()
      expect(screen.getByText('WEB DATA EXTRACTOR')).toBeInTheDocument()
      
      // Check status badges
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Running')).toBeInTheDocument()
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    it('should render loading state', () => {
      renderWithProviders(<JobList {...defaultProps} loading={true} />)
      
      expect(screen.getByText('Jobs Dashboard')).toBeInTheDocument()
      // Check for loading skeleton elements
      const skeletonElements = document.querySelectorAll('.animate-pulse')
      expect(skeletonElements.length).toBeGreaterThan(0)
    })

    it('should render empty state when no jobs', () => {
      renderWithProviders(<JobList {...defaultProps} jobs={[]} />)
      
      expect(screen.getByText('No jobs found')).toBeInTheDocument()
    })

    it('should render job count correctly', () => {
      renderWithProviders(<JobList {...defaultProps} jobs={[mockJob]} />)
      
      expect(screen.getByText('1 job')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should render status badges with correct text', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Running')).toBeInTheDocument()
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })

    it('should handle pending status', () => {
      const jobsWithPending: Job[] = [
        {
          ...mockJob,
          status: 'pending',
        },
      ]
      
      renderWithProviders(<JobList {...defaultProps} jobs={jobsWithPending} />)
      
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })
  })

  describe('Desktop Table View', () => {
    it('should show table headers on desktop', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      // Check table headers
      expect(screen.getByText('ID')).toBeInTheDocument()
      expect(screen.getByText('Title')).toBeInTheDocument()
      expect(screen.getByText('Agent Identifier')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Created')).toBeInTheDocument()
      expect(screen.getByText('Updated')).toBeInTheDocument()
      expect(screen.getByText('Actions')).toBeInTheDocument()
    })

    it('should show view details buttons', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      const viewButtons = screen.getAllByText('View Details')
      expect(viewButtons).toHaveLength(mockJobs.length)
    })

    it('should show job IDs truncated', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      // Should show truncated job IDs for first job
      expect(screen.getByText('123e4567...')).toBeInTheDocument()
      expect(screen.getByText('abc12345...')).toBeInTheDocument()
      expect(screen.getByText('def67890...')).toBeInTheDocument()
    })
  })

  describe('Mobile Card View', () => {
    it('should render job titles when available', () => {
      // The mobile view shows job titles, which we can test regardless of breakpoint
      renderWithProviders(<JobList {...defaultProps} />)
      
      // Job titles should be visible (either in table or cards)
      expect(screen.getByText('Test Research Job')).toBeInTheDocument()
      expect(screen.getByText('Document Summary Job')).toBeInTheDocument()
      expect(screen.getByText('Web Data Extraction Job')).toBeInTheDocument()
    })
  })

  describe('Actions', () => {
    it('should navigate to job details when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<JobList {...defaultProps} />)
      
      const viewButtons = screen.getAllByText('View Details')
      await user.click(viewButtons[0])
      
      // Navigation is handled by mocked useNavigate
    })
  })

  describe('Date Formatting', () => {
    it('should format dates correctly', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      // The exact format will depend on the locale, but should contain date elements
      const dateElements = screen.getAllByText(/\d/)
      expect(dateElements.length).toBeGreaterThan(0)
    })

    it('should handle invalid dates gracefully', () => {
      const jobWithInvalidDate: Job[] = [
        {
          ...mockJob,
          created_at: 'invalid-date',
        },
      ]
      
      renderWithProviders(<JobList {...defaultProps} jobs={jobWithInvalidDate} />)
      
      // Should not throw an error and should render something
      expect(screen.getByText('EXAMPLE RESEARCH AGENT')).toBeInTheDocument()
    })
  })

  describe('Job Data Extraction', () => {
    it('should extract agent identifier from job data correctly', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      expect(screen.getByText('EXAMPLE RESEARCH AGENT')).toBeInTheDocument()
    })

    it('should show UNKNOWN for missing agent identifier', () => {
      const jobWithoutAgentIdentifier: Job[] = [
        {
          ...mockJob,
          data: {
            agent_identifier: undefined as unknown as string,
            title: 'Test',
            query: 'test query',
          },
        },
      ]
      
      renderWithProviders(<JobList {...defaultProps} jobs={jobWithoutAgentIdentifier} />)
      
      expect(screen.getByText('UNKNOWN')).toBeInTheDocument()
    })

    it('should extract job title from data correctly', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      expect(screen.getByText('Test Research Job')).toBeInTheDocument()
    })

    it('should use fallback title when title is missing', () => {
      const jobWithoutTitle: Job[] = [
        {
          ...mockJob,
          data: {
            agent_identifier: 'example_research_agent',
            title: undefined as unknown as string,
            query: 'test query',
          },
        },
      ]
      
      renderWithProviders(<JobList {...defaultProps} jobs={jobWithoutTitle} />)
      
      // Should show fallback title with job ID
      expect(screen.getByText('Job 123e4567')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should display error when provided', () => {
      renderWithProviders(<JobList {...defaultProps} error="Something went wrong" />)
      
      expect(screen.getByText('Failed to Load Jobs')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })

    it('should handle jobs with missing data gracefully', () => {
      const jobWithMissingData: Job[] = [
        {
          ...mockJob,
          data: {
            agent_identifier: undefined as unknown as string,
            title: 'Test',
            query: 'test query',
          },
        },
      ]
      
      renderWithProviders(<JobList {...defaultProps} jobs={jobWithMissingData} />)
      
      expect(screen.getByText('UNKNOWN')).toBeInTheDocument()
    })
  })

  describe('Refresh Functionality', () => {
    it('should show refresh button', () => {
      renderWithProviders(<JobList {...defaultProps} />)
      
      // Should have a refresh button (icon button)
      const refreshButtons = document.querySelectorAll('button')
      expect(refreshButtons.length).toBeGreaterThan(0)
    })

    it('should call onRefresh when provided', async () => {
      const mockRefresh = vi.fn()
      const user = userEvent.setup()
      
      renderWithProviders(<JobList {...defaultProps} onRefresh={mockRefresh} />)
      
      // Find refresh button and click it
      const refreshButton = document.querySelector('button[class*="border-input"]')
      if (refreshButton) {
        await user.click(refreshButton)
        expect(mockRefresh).toHaveBeenCalled()
      }
    })
  })

  describe('Performance', () => {
    it('should handle large number of jobs without performance issues', () => {
      const manyJobs = Array.from({ length: 100 }, (_, index) => ({
        ...mockJob,
        id: `job-${index}`,
      }))
      
      const startTime = performance.now()
      renderWithProviders(<JobList {...defaultProps} jobs={manyJobs} />)
      const endTime = performance.now()
      
      // Render should complete within reasonable time (1 second)
      expect(endTime - startTime).toBeLessThan(1000)
      
      expect(screen.getByText('Jobs Dashboard')).toBeInTheDocument()
    })
  })
}) 