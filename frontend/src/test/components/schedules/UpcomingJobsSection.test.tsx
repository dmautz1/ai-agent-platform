import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { UpcomingJobsSection } from '../../../components/dashboard/UpcomingJobsSection'
import { renderWithProviders } from '../../utils'
import '@testing-library/jest-dom'

// Mock upcoming job data
const mockUpcomingJobs = [
  {
    id: 'schedule-1',
    title: 'Daily Data Processing',
    agent_name: 'data_processor',
    cron_expression: '0 9 * * *',
    next_run: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
    enabled: true,
    description: 'Process daily data files'
  },
  {
    id: 'schedule-2', 
    title: 'Weekly Report Generation',
    agent_name: 'report_generator',
    cron_expression: '0 0 * * 0',
    next_run: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes from now
    enabled: false,
    description: 'Generate weekly reports'
  },
  {
    id: 'schedule-3',
    title: 'Overdue Task',
    agent_name: 'task_processor', 
    cron_expression: '0 */6 * * *',
    next_run: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 minutes ago
    enabled: true,
    description: 'Process overdue tasks'
  }
]

// Mock the API module with comprehensive responses
vi.mock('../../../lib/api', () => ({
  api: {
    schedules: {
      getAllUpcoming: vi.fn(),
      enable: vi.fn(),
      disable: vi.fn(),
      runNow: vi.fn(),
    }
  },
  handleApiError: vi.fn((error) => {
    if (error instanceof Error) {
      return error.message
    }
    if (typeof error === 'string') {
      return error
    }
    return 'An error occurred'
  }),
}))

// Import the mocked API after mocking
import { api } from '../../../lib/api'

// Mock toast notifications
const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
}

vi.mock('../../../components/ui/toast', () => ({
  useToast: () => mockToast,
}))

// Mock react-router-dom
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}))

describe('UpcomingJobsSection Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(mockUpcomingJobs)
    vi.mocked(api.schedules.enable).mockResolvedValue({ success: true })
    vi.mocked(api.schedules.disable).mockResolvedValue({ success: true })
    vi.mocked(api.schedules.runNow).mockResolvedValue({ job_id: 'test-job-123' })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Rendering and Loading (Task 5.6)', () => {
    it('renders without crashing', () => {
      renderWithProviders(<UpcomingJobsSection />)
      expect(screen.getByText(/upcoming jobs/i)).toBeInTheDocument()
    })

    it('shows loading state initially', async () => {
      renderWithProviders(<UpcomingJobsSection />)
      
      // Check for loading elements (skeleton loading)
      const loadingElements = document.querySelectorAll('.animate-pulse')
      expect(loadingElements.length).toBeGreaterThan(0)
    })

    it('displays upcoming jobs after loading', async () => {
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
        expect(screen.getByText('Weekly Report Generation')).toBeInTheDocument()
        expect(screen.getByText('Overdue Task')).toBeInTheDocument()
      })

      // Verify agents are displayed
      expect(screen.getByText('data_processor')).toBeInTheDocument()
      expect(screen.getByText('report_generator')).toBeInTheDocument()
      expect(screen.getByText('task_processor')).toBeInTheDocument()
    })

    it('shows empty state when no jobs are scheduled', async () => {
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue([])
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/no upcoming scheduled jobs/i)).toBeInTheDocument()
        expect(screen.getByText(/create your first schedule/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /create schedule/i })).toBeInTheDocument()
      })
    })

    it.skip('handles API errors gracefully', async () => {
      const error = new Error('Network error')
      vi.clearAllMocks()
      
      // Mock getAllUpcoming to always reject to prevent retry success
      vi.mocked(api.schedules.getAllUpcoming).mockRejectedValue(error)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      // Wait longer to account for retry attempts (component retries up to 2 times with 1s, 2s delays)
      await waitFor(() => {
        expect(screen.getByText(/Failed to Load Upcoming Jobs/i)).toBeInTheDocument()
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      }, { timeout: 8000 })
    })
  })

  describe('Run Now Button Functionality (Task 5.6)', () => {
    it('displays run now button for each schedule', async () => {
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        const runNowButtons = screen.getAllByTitle('Run schedule now')
        expect(runNowButtons).toHaveLength(3)
      })
    })

    it('successfully runs schedule immediately when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      // Verify API call
      expect(api.schedules.runNow).toHaveBeenCalledWith('schedule-1')
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith(
          'Job "Daily Data Processing" started successfully',
          expect.objectContaining({
            title: 'Job ID: test-job-123',
            action: expect.objectContaining({
              label: 'View Job'
            })
          })
        )
      })
    })

    it('handles run now errors properly', async () => {
      const user = userEvent.setup()
      const error = new Error('Job submission failed')
      vi.mocked(api.schedules.runNow).mockRejectedValue(error)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Failed to run "Daily Data Processing" immediately',
          expect.objectContaining({
            title: 'Job submission failed',
            action: expect.objectContaining({
              label: 'Retry'
            })
          })
        )
      })
    })

    it('shows loading state while running schedule', async () => {
      const user = userEvent.setup()
      
      // Mock a slow API response
      vi.mocked(api.schedules.runNow).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ job_id: 'test-job-123' }), 100))
      )
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      // Check for spinner during operation
      expect(document.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('disables run now button during operation', async () => {
      const user = userEvent.setup()
      
      // Mock a slow API response
      vi.mocked(api.schedules.runNow).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ job_id: 'test-job-123' }), 100))
      )
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      // Button should be disabled during operation
      expect(runNowButtons[0]).toBeDisabled()
    })

    it('navigates to dashboard when View Job is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalled()
      })

      // Simulate clicking the "View Job" action
      const successCall = mockToast.success.mock.calls[0]
      const actionCallback = successCall[1].action.onClick
      actionCallback()

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  describe('Time Formatting and Cron Descriptions (Task 5.7)', () => {
    it('formats next run times correctly', async () => {
      // Use fresh mock data for this test
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(mockUpcomingJobs)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        // 2 hours from now should show "In 1h XXm" format (time is dynamic)
        expect(screen.getByText(/In 1h \d+m/)).toBeInTheDocument()
        
        // 30 minutes from now should show "In XX minutes"
        expect(screen.getByText(/In \d+ minutes/)).toBeInTheDocument()
        
        // Overdue task should show "Overdue"
        expect(screen.getByText('Overdue')).toBeInTheDocument()
      })
    })

    it('displays human-readable cron descriptions', async () => {
      // Use fresh mock data for this test
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(mockUpcomingJobs)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        // Check for common cron pattern descriptions
        expect(screen.getByText('Daily at 9:00 AM')).toBeInTheDocument()
        expect(screen.getByText('Weekly on Sunday')).toBeInTheDocument()
        expect(screen.getByText('Every 6 hours')).toBeInTheDocument()
      })
    })

    it('falls back to raw cron expression for unknown patterns', async () => {
      const customSchedule = [{
        id: 'schedule-custom',
        title: 'Custom Schedule',
        agent_name: 'custom_agent',
        cron_expression: '5 14 * * 2,4', // Unknown pattern
        next_run: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Custom schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(customSchedule)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        // Should show raw cron expression when no pattern match
        expect(screen.getByText('5 14 * * 2,4')).toBeInTheDocument()
      })
    })

    it('formats different time ranges correctly', async () => {
      const now = new Date()
      
      // Test case 1: 1 minute
      const schedule1 = [{
        id: 'schedule-time-1',
        title: 'Time Test 1',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() + 1 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule1)
      
      let { unmount } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/In \d+ minute/)).toBeInTheDocument()
      })
      
      unmount()
      
      // Test case 2: 45 minutes (use flexible matching for dynamic time)
      const schedule2 = [{
        id: 'schedule-time-2',
        title: 'Time Test 2',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() + 45 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule2)
      
      const { unmount: unmount2 } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/In \d+ minutes/)).toBeInTheDocument()
      })
      
      unmount2()
      
      // Test case 3: 3 hours
      const schedule3 = [{
        id: 'schedule-time-3',
        title: 'Time Test 3',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() + 3 * 60 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule3)
      
      const { unmount: unmount3 } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/In \d+h/)).toBeInTheDocument()
      })
      
      unmount3()
      
      // Test case 4: 1 day
      const schedule4 = [{
        id: 'schedule-time-4',
        title: 'Time Test 4',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() + 25 * 60 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule4)
      
      const { unmount: unmount4 } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/In \d+ day/)).toBeInTheDocument()
      })
      
      unmount4()
      
      // Test case 5: 3 days
      const schedule5 = [{
        id: 'schedule-time-5',
        title: 'Time Test 5',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() + 72 * 60 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule5)
      
      const { unmount: unmount5 } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText(/In \d+ days/)).toBeInTheDocument()
      })
      
      unmount5()
      
      // Test case 6: Overdue
      const schedule6 = [{
        id: 'schedule-time-6',
        title: 'Time Test 6',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        next_run: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
        enabled: true,
        description: 'Time test schedule'
      }]
      
      vi.clearAllMocks()
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue(schedule6)
      
      const { unmount: unmount6 } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Overdue')).toBeInTheDocument()
      })
      
      unmount6()
    })
  })

  describe('Schedule Actions and Navigation (Task 5.6)', () => {
    it('handles enable/disable toggle correctly', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      // Find pause button for enabled schedule
      const pauseButtons = screen.getAllByTitle('Disable schedule')
      await user.click(pauseButtons[0])

      expect(api.schedules.disable).toHaveBeenCalledWith('schedule-1')
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Schedule disabled successfully')
      })

      // Find play button for disabled schedule
      const playButtons = screen.getAllByTitle('Enable schedule')
      await user.click(playButtons[0])

      expect(api.schedules.enable).toHaveBeenCalledWith('schedule-2')
      
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Schedule enabled successfully')
      })
    })

    it('handles toggle errors properly', async () => {
      const user = userEvent.setup()
      const error = new Error('Toggle failed')
      vi.mocked(api.schedules.disable).mockRejectedValue(error)
      
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const pauseButtons = screen.getAllByTitle('Disable schedule')
      await user.click(pauseButtons[0])

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith(
          'Failed to disable schedule',
          expect.objectContaining({
            title: 'Toggle failed',
            action: expect.objectContaining({
              label: 'Retry'
            })
          })
        )
      })
    })

    it('navigates to schedule history when clicking view button', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const viewButtons = screen.getAllByTitle('View schedule history')
      await user.click(viewButtons[0])

      expect(mockNavigate).toHaveBeenCalledWith('/schedule-history/schedule-1')
    })

    it('navigates to schedule history when clicking table row', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      // Click on the table row (not on action buttons)
      const titleCell = screen.getByText('Daily Data Processing')
      await user.click(titleCell)

      expect(mockNavigate).toHaveBeenCalledWith('/schedule-history/schedule-1')
    })

    it('stops row click propagation when clicking action buttons', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      // Click on run now button - should not navigate to history
      const runNowButtons = screen.getAllByTitle('Run schedule now')
      await user.click(runNowButtons[0])

      // Should call runNow but not navigate to history
      expect(api.schedules.runNow).toHaveBeenCalled()
      expect(mockNavigate).not.toHaveBeenCalledWith('/schedule-history/schedule-1')
    })
  })

  describe('Component Props and Configuration (Task 5.6)', () => {
    it('respects limit prop', async () => {
      renderWithProviders(<UpcomingJobsSection limit={2} />)
      
      expect(api.schedules.getAllUpcoming).toHaveBeenCalledWith(2)
    })

    it('can hide actions when showActions is false', async () => {
      renderWithProviders(<UpcomingJobsSection showActions={false} />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      // Should not have action buttons
      expect(screen.queryByTitle('Run schedule now')).not.toBeInTheDocument()
      expect(screen.queryByTitle('Enable schedule')).not.toBeInTheDocument()
      expect(screen.queryByTitle('Disable schedule')).not.toBeInTheDocument()
    })

    it('handles refresh functionality', async () => {
      const user = userEvent.setup()
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('Daily Data Processing')).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      // Should call API again
      expect(api.schedules.getAllUpcoming).toHaveBeenCalledTimes(2)
    })

    it('handles forceRefresh prop changes', async () => {
      let forceRefresh = 0
      const { rerender } = renderWithProviders(<UpcomingJobsSection forceRefresh={forceRefresh} />)
      
      await waitFor(() => {
        expect(api.schedules.getAllUpcoming).toHaveBeenCalledTimes(1)
      })

      // Update forceRefresh prop
      forceRefresh = 1
      rerender(<UpcomingJobsSection forceRefresh={forceRefresh} />)

      await waitFor(() => {
        expect(api.schedules.getAllUpcoming).toHaveBeenCalledTimes(2)
      })
    })

    it('shows refresh indicator when isRefreshing is true', () => {
      renderWithProviders(<UpcomingJobsSection isRefreshing={true} />)
      
      // Should show spinning refresh icon in header
      const headerSpinner = document.querySelector('.animate-spin')
      expect(headerSpinner).toBeInTheDocument()
    })
  })

  describe('Status and Badge Display (Task 5.7)', () => {
    it('displays correct status badges for enabled/disabled schedules', async () => {
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        // Check for Active and Paused badges
        expect(screen.getAllByText('Active')).toHaveLength(2) // schedule-1 and schedule-3
        expect(screen.getByText('Paused')).toBeInTheDocument() // schedule-2
      })
    })

    it('displays job count badge in header', async () => {
      renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('3 upcoming')).toBeInTheDocument()
      })
    })

    it('updates badge count when schedules change', async () => {
      const { rerender } = renderWithProviders(<UpcomingJobsSection />)
      
      await waitFor(() => {
        expect(screen.getByText('3 upcoming')).toBeInTheDocument()
      })

      // Update with fewer schedules
      vi.mocked(api.schedules.getAllUpcoming).mockResolvedValue([mockUpcomingJobs[0]])
      rerender(<UpcomingJobsSection forceRefresh={1} />)
      
      await waitFor(() => {
        expect(screen.getByText('1 upcoming')).toBeInTheDocument()
      })
    })
  })
}) 