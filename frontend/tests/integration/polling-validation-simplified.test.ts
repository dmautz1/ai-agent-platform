import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useJobPolling, useSingleJobPolling } from '../../src/lib/polling';
import { api } from '../../src/lib/api';
import type { Job, JobStatus } from '../../src/lib/models';

// Mock the API
vi.mock('../../src/lib/api', () => ({
  api: {
    jobs: {
      getAll: vi.fn(),
      getById: vi.fn(),
      getBatchStatus: vi.fn(),
    },
  },
}));

const mockJobs: Job[] = [
  {
    id: 'job-1',
    user_id: 'user-1',
    status: 'pending' as JobStatus,
    priority: 'normal',
    data: { agent_identifier: 'test_agent', title: 'Test Job 1' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'job-2',
    user_id: 'user-1',
    status: 'running' as JobStatus,
    priority: 'high',
    data: { agent_identifier: 'test_agent_2', title: 'Test Job 2' },
    created_at: '2024-01-01T01:00:00Z',
    updated_at: '2024-01-01T01:00:00Z',
  },
  {
    id: 'job-3',
    user_id: 'user-1',
    status: 'completed' as JobStatus,
    priority: 'normal',
    data: { agent_identifier: 'test_agent_3', title: 'Test Job 3' },
    created_at: '2024-01-01T02:00:00Z',
    updated_at: '2024-01-01T02:30:00Z',
  },
];

describe('Job Polling and Real-Time Updates Validation (Simplified)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default successful API responses
    vi.mocked(api.jobs.getAll).mockResolvedValue(mockJobs);
    vi.mocked(api.jobs.getById).mockResolvedValue(mockJobs[0]);
    vi.mocked(api.jobs.getBatchStatus).mockResolvedValue({
      'job-1': { status: 'pending', updated_at: '2024-01-01T00:00:00Z' },
      'job-2': { status: 'running', updated_at: '2024-01-01T01:00:00Z' },
      'job-3': { status: 'completed', updated_at: '2024-01-01T02:30:00Z' },
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('useJobPolling Hook', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.isPaused).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.retryCount).toBe(0);
      expect(result.current.pollingState.error).toBeNull();
      expect(typeof result.current.pausePolling).toBe('function');
      expect(typeof result.current.resumePolling).toBe('function');
      expect(typeof result.current.forceUpdate).toBe('function');
    });

    it('should handle API calls correctly', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(api.jobs.getAll).toHaveBeenCalledTimes(1);
      expect(onUpdate).toHaveBeenCalledWith(mockJobs);
      expect(result.current.pollingState.lastUpdate).not.toBeNull();
    });

    it('should handle API errors gracefully', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Network error');
      vi.mocked(api.jobs.getAll).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(result.current.pollingState.error).toBe('Network error');
      expect(result.current.pollingState.retryCount).toBe(1);
    });

    it('should support pause and resume functionality', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      // Initially not paused
      expect(result.current.pollingState.isPaused).toBe(false);

      // Pause polling
      act(() => {
        result.current.pausePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(true);

      // Resume polling
      act(() => {
        result.current.resumePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(false);
    });

    it('should persist pause state with persistKey', () => {
      const onUpdate = vi.fn();
      
      const { result } = renderHook(() => 
        useJobPolling(onUpdate, { persistKey: 'test_polling', autoStart: false })
      );

      act(() => {
        result.current.pausePolling();
      });

      expect(localStorage.getItem('test_polling')).toBe('true');

      act(() => {
        result.current.resumePolling();
      });

      expect(localStorage.getItem('test_polling')).toBe('false');
    });
  });

  describe('useSingleJobPolling Hook', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate, { autoStart: false })
      );

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.isPaused).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.error).toBeNull();
    });

    it('should fetch single job data', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate, { autoStart: false })
      );

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(api.jobs.getById).toHaveBeenCalledWith('job-1');
      expect(onUpdate).toHaveBeenCalledWith(mockJobs[0]);
    });

    it('should handle single job errors', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Job not found');
      vi.mocked(api.jobs.getById).mockRejectedValueOnce(error);

      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate, { autoStart: false })
      );

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(result.current.pollingState.error).toBe('Job not found');
      expect(result.current.pollingState.retryCount).toBe(1);
    });

    it('should support pause and resume functionality', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate, { autoStart: false })
      );

      // Pause polling
      act(() => {
        result.current.pausePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(true);

      // Resume polling
      act(() => {
        result.current.resumePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(false);
    });
  });

  describe('API Response Handling', () => {
    it('should handle empty job arrays', async () => {
      const onUpdate = vi.fn();
      vi.mocked(api.jobs.getAll).mockResolvedValueOnce([]);

      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(onUpdate).toHaveBeenCalledWith([]);
      expect(result.current.pollingState.error).toBeNull();
    });

    it('should validate job status updates', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useJobPolling(onUpdate, { baseInterval: 2000, autoStart: false })
      );

      await act(async () => {
        await result.current.forceUpdate();
      });

      // Verify initial fetch was called
      expect(api.jobs.getAll).toHaveBeenCalledTimes(1);
      expect(onUpdate).toHaveBeenCalledWith(mockJobs);

      // Verify state is updated correctly
      expect(result.current.pollingState.lastUpdate).not.toBeNull();
      expect(result.current.pollingState.error).toBeNull();
    });
  });

  describe('Configuration Options', () => {
    it('should accept custom polling options', () => {
      const onUpdate = vi.fn();
      const options = {
        baseInterval: 10000,
        maxRetries: 5,
        persistKey: 'test_key',
        autoStart: false,
      };
      
      const { result } = renderHook(() => useJobPolling(onUpdate, options));
      
      expect(result.current.pollingState).toBeDefined();
      expect(result.current.pollingState.isPolling).toBe(false);
    });
  });
}); 