import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, screen, waitFor } from '@testing-library/react';
import { useJobPolling, useSingleJobPolling, type PollingOptions } from '../../lib/polling';
import type { Job, JobMinimal } from '../../lib/types';
import { createMockJob } from '../utils';

// Mock the API module with hoisted functions
const { mockGetAllMinimal, mockGetById } = vi.hoisted(() => ({
  mockGetAllMinimal: vi.fn(),
  mockGetById: vi.fn()
}));

vi.mock('../../lib/api', () => ({
  api: {
    jobs: {
      getAllMinimal: mockGetAllMinimal,
      getById: mockGetById
    }
  }
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock timers
vi.useFakeTimers();

describe('Polling Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    mockGetAllMinimal.mockClear();
    mockGetById.mockClear();
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    vi.useFakeTimers();
  });

  describe('useJobPolling', () => {
    const createMockJobMinimal = (overrides: Partial<JobMinimal> = {}): JobMinimal => ({
      id: 'job-1',
      status: 'pending',
      agent_identifier: 'test_agent',
      title: 'Test Job',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      ...overrides
    });

    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.isPaused).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.error).toBeNull();
      expect(result.current.pollingState.retryCount).toBe(0);
    });

    it('should provide pause and resume functions', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      expect(typeof result.current.pausePolling).toBe('function');
      expect(typeof result.current.resumePolling).toBe('function');
      expect(typeof result.current.forceUpdate).toBe('function');
    });

    it('should handle manual refresh functionality', async () => {
      const mockJobs = [createMockJobMinimal()];
      mockGetAllMinimal.mockResolvedValue(mockJobs);
      
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      // Manual refresh
      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(mockGetAllMinimal).toHaveBeenCalledWith({ limit: 50 });
      expect(onUpdate).toHaveBeenCalledWith(expect.any(Array));
    });

    it('should pause and resume polling', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

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

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });
      
      const onUpdate = vi.fn();
      
      // Should not throw
      expect(() => {
        renderHook(() => useJobPolling(onUpdate, { persistKey: 'test' }));
      }).not.toThrow();
    });
  });

  describe('useSingleJobPolling', () => {
    it('should initialize with correct default state', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useSingleJobPolling('job-1', onUpdate, { autoStart: false }));

      expect(result.current.pollingState.isPolling).toBe(false);
      expect(result.current.pollingState.isPaused).toBe(false);
      expect(result.current.pollingState.lastUpdate).toBeNull();
      expect(result.current.pollingState.error).toBeNull();
      expect(result.current.pollingState.retryCount).toBe(0);
    });

    it('should provide pause and resume functions', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useSingleJobPolling('job-1', onUpdate, { autoStart: false }));

      expect(typeof result.current.pausePolling).toBe('function');
      expect(typeof result.current.resumePolling).toBe('function');
      expect(typeof result.current.forceUpdate).toBe('function');
    });

    it('should handle manual refresh for single job', async () => {
      const mockJob = createMockJob({ id: 'job-1' });
      mockGetById.mockResolvedValue(mockJob);
      
      const onUpdate = vi.fn();
      const { result } = renderHook(() => 
        useSingleJobPolling('job-1', onUpdate, { autoStart: false })
      );

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(mockGetById).toHaveBeenCalledWith('job-1');
      expect(onUpdate).toHaveBeenCalledWith(mockJob);
    });

    it('should pause and resume single job polling', () => {
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useSingleJobPolling('job-1', onUpdate, { autoStart: false }));

      // Pause
      act(() => {
        result.current.pausePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(true);

      // Resume
      act(() => {
        result.current.resumePolling();
      });

      expect(result.current.pollingState.isPaused).toBe(false);
    });
  });

  describe('Helper Functions', () => {
    it('should convert minimal job to full job object', async () => {
      const minimal: JobMinimal = {
        id: 'job-1',
        status: 'completed',
        agent_identifier: 'test_agent',
        title: 'Test Job',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z'
      };

      mockGetAllMinimal.mockResolvedValue([minimal]);
      
      const onUpdate = vi.fn();
      const { result } = renderHook(() => useJobPolling(onUpdate, { autoStart: false }));

      await act(async () => {
        await result.current.forceUpdate();
      });

      expect(onUpdate).toHaveBeenCalledWith([
        expect.objectContaining({
          id: 'job-1',
          status: 'completed',
          agent_identifier: 'test_agent',
          title: 'Test Job',
          user_id: '',
          priority: 5,
          data: {
            agent_identifier: 'test_agent',
            title: 'Test Job'
          },
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:01:00Z'
        })
      ]);
    });
  });
}); 