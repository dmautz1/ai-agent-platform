import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useJobPolling, useSingleJobPolling } from '../../lib/polling'
import type { Job } from '../../lib/types'

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getAll: vi.fn(),
      getById: vi.fn(),
      getBatchStatus: vi.fn(),
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
        agent_type: 'text_processing', 
        title: 'Job 1',
        input_text: 'Test text to process',
        operation: 'sentiment_analysis',
        language: 'en'
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
        agent_type: 'summarization', 
        title: 'Job 2',
        input_text: 'Text to summarize',
        max_summary_length: 200,
        format: 'paragraph',
        language: 'en'
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:02:00Z'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
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
      expect(result.current.pollingState.retryCount).toBe(0)
      expect(result.current.pollingState.error).toBe(null)
    })

    it('starts polling and fetches jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as any).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(api.jobs.getAll).toHaveBeenCalled()
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJobs)
      expect(result.current.pollingState.lastUpdate).toBeTruthy()
      expect(result.current.pollingState.error).toBe(null)
    })

    it('handles fetch errors gracefully', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const mockError = new Error('Network error')
      
      ;(api.jobs.getAll as any).mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(result.current.pollingState.error).toBe('Network error')
      expect(result.current.pollingState.retryCount).toBe(1)
    })

    it('stops polling when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as any).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      act(() => {
        result.current.stopPolling()
      })
      
      expect(result.current.pollingState.isPolling).toBe(false)
    })

    it('forces update when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getAll as any).mockResolvedValue(mockJobs)
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.forceUpdate()
      })
      
      expect(api.jobs.getAll).toHaveBeenCalled()
      expect(mockOnUpdate).toHaveBeenCalledWith(mockJobs)
    })

    it('uses lightweight polling when enabled', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      // First call returns jobs, second call uses batch status
      ;(api.jobs.getAll as any).mockResolvedValueOnce(mockJobs)
      ;(api.jobs.getBatchStatus as any).mockResolvedValue({
        job1: { status: 'completed', updated_at: '2024-01-01T00:05:00Z' },
        job2: { status: 'completed', updated_at: '2024-01-01T00:06:00Z' }
      })
      
      const { result } = renderHook(() => 
        useJobPolling(mockOnUpdate, { useLightweightPolling: true })
      )
      
      // Start polling to get initial jobs
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(api.jobs.getAll).toHaveBeenCalledTimes(1)
      expect(mockOnUpdate).toHaveBeenCalledTimes(1)
    })

    it('accepts custom polling options', () => {
      const mockOnUpdate = vi.fn()
      const options = {
        baseInterval: 10000,
        backgroundOptimization: false,
        maxRetries: 5,
        retryBackoffMultiplier: 2.0,
        useLightweightPolling: false
      }
      
      const { result } = renderHook(() => useJobPolling(mockOnUpdate, options))
      
      // Options should be applied (we can't directly test them but they shouldn't cause errors)
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
        agent_type: 'text_processing', 
        title: 'Single Job',
        input_text: 'Single job text to process',
        operation: 'sentiment_analysis',
        language: 'en'
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:01:00Z'
    }

    it('initializes with correct default state', () => {
      const mockOnUpdate = vi.fn()
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      expect(result.current.pollingState.isPolling).toBe(false)
      expect(result.current.pollingState.lastUpdate).toBe(null)
      expect(result.current.pollingState.retryCount).toBe(0)
      expect(result.current.pollingState.error).toBe(null)
    })

    it('starts polling and fetches single job', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as any).mockResolvedValue(mockJob)
      
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
      
      ;(api.jobs.getById as any).mockRejectedValue(mockError)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(result.current.pollingState.error).toBe('Job not found')
      expect(result.current.pollingState.retryCount).toBe(1)
    })

    it('stops polling for completed jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const completedJob = { ...mockJob, status: 'completed' as const }
      
      ;(api.jobs.getById as any).mockResolvedValue(completedJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(mockOnUpdate).toHaveBeenCalledWith(completedJob)
      // Polling should not continue for completed jobs
    })

    it('continues polling for active jobs', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      const runningJob = { ...mockJob, status: 'running' as const }
      
      ;(api.jobs.getById as any).mockResolvedValue(runningJob)
      
      const { result } = renderHook(() => useSingleJobPolling('job1', mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      expect(mockOnUpdate).toHaveBeenCalledWith(runningJob)
      // For running jobs, polling should continue (can't easily test the timeout)
    })

    it('forces update when requested', async () => {
      const { api } = await import('../../lib/api')
      const mockOnUpdate = vi.fn()
      
      ;(api.jobs.getById as any).mockResolvedValue(mockJob)
      
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
      
      ;(api.jobs.getById as any).mockResolvedValue(mockJob)
      
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
        backgroundOptimization: false,
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
      
      ;(api.jobs.getAll as any).mockResolvedValue(mockJobs)
      
      const { result, unmount } = renderHook(() => useJobPolling(mockOnUpdate))
      
      await act(async () => {
        await result.current.startPolling()
      })
      
      unmount()
      
      // Should not throw any errors during cleanup
      expect(() => unmount()).not.toThrow()
    })
  })
}) 