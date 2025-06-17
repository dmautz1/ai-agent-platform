import { renderHook, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useJobPolling, useSingleJobPolling } from '../../lib/polling'
import type { Job } from '../../lib/api'

// Mock the API
vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getAll: vi.fn(),
      getById: vi.fn(),
    },
  },
}))

const mockJobs: Job[] = [
  {
    id: 'job1',
    user_id: 'user1',
    status: 'running',
    priority: 'normal',
    data: { agent_identifier: 'test_agent', title: 'Test Job' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:01:00Z'
  }
]

describe('Polling Hooks - New Implementation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('useJobPolling', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn()
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }))

      expect(result.current.pollingState.isPolling).toBe(false)
      expect(result.current.pollingState.isPaused).toBe(false)
      expect(result.current.pollingState.lastUpdate).toBe(null)
      expect(result.current.pollingState.error).toBe(null)
      expect(result.current.pollingState.retryCount).toBe(0)
    })

    it('should pause and resume polling correctly', () => {
      const onUpdate = vi.fn()
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }))

      // Initially not paused
      expect(result.current.pollingState.isPaused).toBe(false)

      // Pause polling
      act(() => {
        result.current.pausePolling()
      })

      expect(result.current.pollingState.isPaused).toBe(true)

      // Resume polling
      act(() => {
        result.current.resumePolling()
      })

      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('should handle forceUpdate correctly', async () => {
      const { api } = await import('../../lib/api')
      const onUpdate = vi.fn()
      
      // @ts-ignore
      api.jobs.getAll.mockResolvedValue(mockJobs)

      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }))

      await act(async () => {
        await result.current.forceUpdate()
      })

      expect(api.jobs.getAll).toHaveBeenCalled()
      expect(onUpdate).toHaveBeenCalledWith(mockJobs)
    })

    it('should persist pause state with persistKey', () => {
      const onUpdate = vi.fn()
      
      const { result } = renderHook(() => 
        useJobPolling(onUpdate, { persistKey: 'test_polling', autoStart: false })
      )

      act(() => {
        result.current.pausePolling()
      })

      expect(localStorage.getItem('test_polling')).toBe('true')

      act(() => {
        result.current.resumePolling()
      })

      expect(localStorage.getItem('test_polling')).toBe('false')
    })
  })

  describe('useSingleJobPolling', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn()
      const { result } = renderHook(() => 
        useSingleJobPolling('job1', onUpdate, { autoStart: false })
      )

      expect(result.current.pollingState.isPolling).toBe(false)
      expect(result.current.pollingState.isPaused).toBe(false)
      expect(result.current.pollingState.lastUpdate).toBe(null)
      expect(result.current.pollingState.error).toBe(null)
    })

    it('should handle API calls correctly', async () => {
      const { api } = await import('../../lib/api')
      const onUpdate = vi.fn()
      
      // @ts-ignore
      api.jobs.getById.mockResolvedValue(mockJobs[0])

      const { result } = renderHook(() => 
        useSingleJobPolling('job1', onUpdate, { autoStart: false })
      )

      await act(async () => {
        await result.current.forceUpdate()
      })

      expect(api.jobs.getById).toHaveBeenCalledWith('job1')
      expect(onUpdate).toHaveBeenCalledWith(mockJobs[0])
    })

    it('should pause and resume single job polling', () => {
      const onUpdate = vi.fn()
      const { result } = renderHook(() => 
        useSingleJobPolling('job1', onUpdate, { autoStart: false })
      )

      // Pause polling
      act(() => {
        result.current.pausePolling()
      })

      expect(result.current.pollingState.isPaused).toBe(true)

      // Resume polling
      act(() => {
        result.current.resumePolling()
      })

      expect(result.current.pollingState.isPaused).toBe(false)
    })

    it('should handle API errors gracefully', async () => {
      const { api } = await import('../../lib/api')
      const onUpdate = vi.fn()
      const error = new Error('Network error')
      
      // @ts-ignore
      api.jobs.getById.mockRejectedValue(error)

      const { result } = renderHook(() => 
        useSingleJobPolling('job1', onUpdate, { autoStart: false })
      )

      await act(async () => {
        await result.current.forceUpdate()
      })

      expect(result.current.pollingState.error).toBe('Network error')
      expect(result.current.pollingState.retryCount).toBe(1)
    })
  })
}) 