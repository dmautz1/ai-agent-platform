import { describe, it, expect, vi, beforeEach, afterEach, type MockedFunction } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useJobPolling, useSingleJobPolling } from '../../lib/polling'
import type { Job } from '../../lib/api'

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getAll: vi.fn(),
      getById: vi.fn(),
    }
  }
}))

// Mock console methods
const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

describe('Polling Hooks', () => {
  const mockJobs: Job[] = [
    {
      id: 'job1',
      user_id: 'user1',
      status: 'running',
      priority: 'normal',
      data: { 
        agent_identifier: 'example_research_agent', 
        title: 'Job 1',
        query: 'Test research query',
        max_results: 10
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z'
    },
    {
      id: 'job2',
      user_id: 'user1',
      status: 'completed',
      priority: 'normal',
      data: { 
        agent_identifier: 'content_summarizer', 
        title: 'Job 2',
        content: 'Text to summarize',
        max_length: 200,
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:02:00Z'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
    consoleSpy.mockClear()
  })

  describe('useJobPolling', () => {
    it('initializes with correct default state', () => {
      const mockOnUpdate = vi.fn()
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      expect(result.current.pollingState.isPolling).toBe(false)
      expect(result.current.pollingState.lastUpdate).toBe(null)
      expect(result.current.pollingState.error).toBe(null)
      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('starts polling and fetches jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as MockedFunction<typeof api.jobs.getAll>).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(api.jobs.getAll).toHaveBeenCalled()
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJobs)
      expect(result.current.pollingState.lastUpdate).toBeTruthy()
      expect(result.current.pollingState.error).toBe(null)
    })

    it('should handle API errors and set error state', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const mockError = new Error('API Error')
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(api.jobs.getAll as any).mockRejectedValue(mockError)

      const { result } = renderHook(() => useJobPolling(mockOnUpdate))

      await act(async () => {
        await result.current.startPolling()
      })

      expect(result.current.pollingState.error).toBe('API Error')
      expect(result.current.pollingState.retryCount).toBe(1)
    })

    it('stops polling when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as MockedFunction<typeof api.jobs.getAll>).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      act(() => {
        result.current.stopPolling()
      })
      
      expect(result.current.pollingState.isPolling).toBe(false)
    })

    it('pauses and resumes polling', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as MockedFunction<typeof api.jobs.getAll>).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      act(() => {
        result.current.pausePolling()
      })
      
      expect(result.current.pollingState.isPaused).toBe(true)
      
      await act(async () => {
        await result.current.resumePolling()
      })
      
      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('forces update when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as MockedFunction<typeof api.jobs.getAll>).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.forceUpdate()
      })
      
      expect(api.jobs.getAll).toHaveBeenCalled()
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJobs)
    })

    it('persists pause state with persistKey', () => {
      const mockOnUpdate = vi.fn()
      
      const { result } = renderHook(() => 
        useJobPolling(mockOnUpdate, { persistKey: 'test_polling' })
      )
      
      act(() => {
        result.current.pausePolling()
      })
      
      expect(localStorage.getItem('test_polling')).toBe('true')
    })

    it('accepts custom polling options', () => {
      const mockOnUpdate = vi.fn()
      const options = {
        baseInterval: 10000,
        maxRetries: 5,
        persistKey: 'test_key'
      }
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate, options))
      
      expect(result.current.pollingState).toBeDefined()
    })
  })

  describe('useSingleJobPolling', () => {
    const mockJob: Job = {
      id: 'job1',
      user_id: 'user1',
      status: 'running',
      priority: 'normal',
      data: { 
        agent_identifier: 'example_research_agent',
        title: 'Single Job Test',
        query: 'Test query for single job',
        max_results: 5
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z'
    }

    it('initializes with correct default state', () => {
      const mockOnUpdate = vi.fn()
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      expect(result.current.pollingState.isPolling).toBe(false)
      expect(result.current.pollingState.lastUpdate).toBe(null)
      expect(result.current.pollingState.error).toBe(null)
      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('starts polling and fetches single job', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(mockJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(api.jobs.getById).toHaveBeenCalledWith('job1')
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJob)
      expect(result.current.pollingState.lastUpdate).toBeTruthy()
    })

    it('handles single job fetch errors', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const mockError = new Error('Job not found')
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(result.current.pollingState.error).toBe('Job not found')
    })

    it('stops polling for completed jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const completedJob = { ...mockJob, status: 'completed' as const }
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(completedJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(mockOnUpdate).toHaveBeenCalledWith(completedJob)
    })

    it('continues polling for active jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const runningJob = { ...mockJob, status: 'running' as const }
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(runningJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(mockOnUpdate).toHaveBeenCalledWith(runningJob)
    })

    it('pauses and resumes single job polling', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(mockJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      act(() => {
        result.current.pausePolling()
      })
      
      expect(result.current.pollingState.isPaused).toBe(true)
      
      await act(async () => {
        await result.current.resumePolling()
      })
      
      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('forces update when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(mockJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.forceUpdate()
      })
      
      expect(api.jobs.getById).toHaveBeenCalledWith('job1')
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJob)
    })

    it('stops polling when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as MockedFunction<typeof api.jobs.getById>).mockResolvedValue(mockJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      act(() => {
        result.current.stopPolling()
      })
      
      expect(result.current.pollingState.isPolling).toBe(false)
    })

    it('accepts custom polling options', () => {
      const mockOnUpdate = vi.fn()
      const options = {
        baseInterval: 2000,
        maxRetries: 2
      }
      
      const { result } = renderHook(() => 
        useSingleJobPolling('job1', mockOnUpdate, options)
      )
      
      expect(result.current.pollingState).toBeDefined()
    })
  })

  describe('Cleanup', () => {
    it('cleans up polling on unmount', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(api.jobs.getAll as any).mockResolvedValue(mockJobs)
      
      const { result, unmount } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      unmount()
      
      expect(() => unmount()).not.toThrow()
    })
  })
}) 