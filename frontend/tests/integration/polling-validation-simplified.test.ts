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
    status: 'pending' as JobStatus,
    priority: 'normal',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    user_id: 'user-1',
    data: {
      agent_identifier: 'simple_prompt',
      title: 'Test Job 1',
      prompt: 'Test prompt content'
    },
  },
  {
    id: 'job-2',
    status: 'running' as JobStatus,
    priority: 'high',
    created_at: '2024-01-01T01:00:00Z',
    updated_at: '2024-01-01T01:00:00Z',
    user_id: 'user-1',
    data: {
      agent_identifier: 'simple_prompt',
      title: 'Test Job 2',
      prompt: 'Test content for processing'
    },
  },
  {
    id: 'job-3',
    status: 'completed' as JobStatus,
    priority: 'normal',
    created_at: '2024-01-01T02:00:00Z',
    updated_at: '2024-01-01T02:30:00Z',
    user_id: 'user-1',
    data: {
      agent_identifier: 'simple_prompt',
      title: 'Test Job 3',
      prompt: 'Test URL content'
    },
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

  describe('useJobPolling Hook Initialization', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.retryCount).toBe(0);
      expect(result.current.pollingState.error).toBeNull();
      expect(typeof result.current.startPolling).toBe('function');
      expect(typeof result.current.stopPolling).toBe('function');
      expect(typeof result.current.forceUpdate).toBe('function');
    });

    it('should accept polling options and pass them correctly', () => {
      const onUpdate = vi.fn();
      const options = {
        baseInterval: 2000,
        backgroundOptimization: false,
        maxRetries: 5,
        useLightweightPolling: false,
      };

      const { result } = renderHook(() => useJobPolling(onUpdate, options));

      // Hook should initialize without errors
      expect(result.current.pollingState.isPolling).toBe(false);
    });
  });

  describe('useJobPolling API Integration', () => {
    it('should fetch initial job data when startPolling is called', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      expect(api.jobs.getAll).toHaveBeenCalledTimes(1);
      expect(onUpdate).toHaveBeenCalledWith(mockJobs);
      expect(result.current.pollingState.lastUpdate).not.toBeNull();
    });

    it('should handle API errors gracefully', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Network error');
      vi.mocked(api.jobs.getAll).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      expect(result.current.pollingState.error).toBe('Network error');
      expect(result.current.pollingState.retryCount).toBe(1);
    });

    it('should call forceUpdate and fetch fresh data', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      vi.clearAllMocks();

      await act(async () => {
        await result.current.forceUpdate();
      });

      // forceUpdate calls fetchJobs which should call api.jobs.getAll for a fresh fetch
      // Note: If lightweight polling is enabled, it might use getBatchStatus instead
      const totalCalls = (vi.mocked(api.jobs.getAll).mock.calls.length) + 
                         (vi.mocked(api.jobs.getBatchStatus).mock.calls.length);
      expect(totalCalls).toBeGreaterThan(0);
      expect(onUpdate).toHaveBeenCalled();
    });

    it('should stop polling when stopPolling is called', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      act(() => {
        result.current.stopPolling();
      });

      expect(result.current.pollingState.isPolling).toBe(false);
    });

    it('should handle API error on initial load with null response', async () => {
      const onUpdate = vi.fn();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      vi.mocked(api.jobs.getAll).mockResolvedValueOnce(null as any);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      // Check that null responses are handled gracefully (no error should be set)
      expect(result.current.pollingState.error).toBeNull();
      expect(onUpdate).toHaveBeenCalledWith(null);
    });
  });

  describe('useSingleJobPolling Hook', () => {
    it('should initialize with correct state for single job polling', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate)
      );

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.retryCount).toBe(0);
      expect(result.current.pollingState.error).toBeNull();
    });

    it('should fetch single job data when startPolling is called', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate)
      );

      await act(async () => {
        await result.current.startPolling();
      });

      expect(api.jobs.getById).toHaveBeenCalledWith('job-1');
      expect(onUpdate).toHaveBeenCalledWith(mockJobs[0]);
    });

    it('should handle single job polling errors', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Job not found');
      vi.mocked(api.jobs.getById).mockRejectedValueOnce(error);

      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate)
      );

      await act(async () => {
        await result.current.startPolling();
      });

      expect(result.current.pollingState.error).toBe('Job not found');
      expect(result.current.pollingState.retryCount).toBe(1);
    });

    it('should force update single job data', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate)
      );

      await act(async () => {
        await result.current.startPolling();
      });

      vi.clearAllMocks();

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(api.jobs.getById).toHaveBeenCalledWith('job-1');
      expect(onUpdate).toHaveBeenCalledWith(mockJobs[0]);
    });
  });

  describe('Polling Hook State Management', () => {
    it('should update polling state correctly during lifecycle', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      // Initial state
      expect(result.current.pollingState.isPolling).toBe(false);

      // Start polling
      await act(async () => {
        await result.current.startPolling();
      });

      expect(result.current.pollingState.isPolling).toBe(false); // Should be false after completion
      expect(result.current.pollingState.lastUpdate).not.toBeNull();
      expect(result.current.pollingState.error).toBeNull();

      // Stop polling
      act(() => {
        result.current.stopPolling();
      });

      expect(result.current.pollingState.isPolling).toBe(false);
    });

    it('should handle error state correctly', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Test error');
      vi.mocked(api.jobs.getAll).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      expect(result.current.pollingState.error).toBe('Test error');
      expect(result.current.pollingState.retryCount).toBe(1);
    });
  });

  describe('API Response Handling', () => {
    it('should handle empty job arrays', async () => {
      const onUpdate = vi.fn();
      vi.mocked(api.jobs.getAll).mockResolvedValueOnce([]);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      expect(onUpdate).toHaveBeenCalledWith([]);
      expect(result.current.pollingState.error).toBeNull();
    });

    it('should handle null responses gracefully', async () => {
      const onUpdate = vi.fn();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      vi.mocked(api.jobs.getAll).mockResolvedValueOnce(null as any);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      await act(async () => {
        await result.current.startPolling();
      });

      expect(onUpdate).toHaveBeenCalledWith(null);
      expect(result.current.pollingState.error).toBeNull();
    });

    it('should validate job status updates', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useJobPolling(onUpdate, { baseInterval: 2000 })
      );

      await act(async () => {
        await result.current.startPolling();
      });

      // Verify initial fetch was called
      expect(api.jobs.getAll).toHaveBeenCalledTimes(1);
      expect(onUpdate).toHaveBeenCalledWith(mockJobs);

      // Verify state is updated correctly
      expect(result.current.pollingState.lastUpdate).not.toBeNull();
      expect(result.current.pollingState.error).toBeNull();
    });
  });

  describe('Error Recovery Mechanisms', () => {
    it('should recover from temporary network errors', async () => {
      const onUpdate = vi.fn();
      const error = new Error('Temporary network error');
      
      vi.mocked(api.jobs.getAll)
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockJobs);

      const { result } = renderHook(() => useJobPolling(onUpdate));

      // First call should fail
      await act(async () => {
        await result.current.startPolling();
      });

      expect(result.current.pollingState.error).toBe('Temporary network error');
      expect(result.current.pollingState.retryCount).toBe(1);

      // Force update should succeed
      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(result.current.pollingState.error).toBeNull();
      expect(onUpdate).toHaveBeenCalledWith(mockJobs);
    });

    it('should handle different types of API errors', async () => {
      const onUpdate = vi.fn();
      const errors = [
        new Error('Network Error'),
        { message: 'Server Error', status: 500 },
        'String error message',
      ];

      for (const error of errors) {
        vi.mocked(api.jobs.getAll).mockRejectedValueOnce(error);

        const { result } = renderHook(() => useJobPolling(onUpdate));

        await act(async () => {
          await result.current.startPolling();
        });

        expect(result.current.pollingState.error).toBeTruthy();
        expect(result.current.pollingState.retryCount).toBe(1);
      }
    });
  });

  describe('Hook Cleanup and Memory Management', () => {
    it('should cleanup properly when component unmounts', () => {
      const onUpdate = vi.fn();
      const { result, unmount } = renderHook(() => useJobPolling(onUpdate));

      // Start polling
      act(() => {
        result.current.startPolling();
      });

      // Unmount should cleanup without errors
      expect(() => unmount()).not.toThrow();
    });

    it('should prevent memory leaks with multiple start/stop cycles', async () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate));

      // Multiple start/stop cycles
      for (let i = 0; i < 3; i++) {
        await act(async () => {
          await result.current.startPolling();
        });

        act(() => {
          result.current.stopPolling();
        });
      }

      // Should not cause memory leaks or errors
      expect(result.current.pollingState.isPolling).toBe(false);
    });
  });

  describe('Configuration Validation', () => {
    it('should work with different polling options', () => {
      const onUpdate = vi.fn();
      const configs = [
        { baseInterval: 1000 },
        { maxRetries: 10 },
        { persistKey: 'test_key' },
        {
          baseInterval: 3000,
          maxRetries: 5,
          persistKey: 'test_polling',
        },
      ];

      configs.forEach(config => {
        const { result } = renderHook(() => useJobPolling(onUpdate, config));
        expect(result.current.pollingState.isPolling).toBe(false);
      });
    });

    it('should handle invalid or edge case configurations', () => {
      const onUpdate = vi.fn();
      const edgeCases = [
        { baseInterval: 0 },
        { baseInterval: -1000 },
        { maxRetries: -1 },
        {},
        undefined,
      ];

      edgeCases.forEach(config => {
        expect(() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          renderHook(() => useJobPolling(onUpdate, config as any));
        }).not.toThrow();
      });
    });

    it('should handle invalid polling configuration gracefully', () => {
      const onUpdate = vi.fn();
      const config = {
        invalidOption: 'test'
      };

      // Should not throw an error when creating hook with invalid config
      expect(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        renderHook(() => useJobPolling(onUpdate, config as any));
      }).not.toThrow();
    });
  });
}); 