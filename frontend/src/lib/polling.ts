import { useEffect, useRef, useCallback, useState } from 'react';
import { api, type Job, type JobMinimal } from './api';

export interface PollingOptions {
  /** Base polling interval in milliseconds (default: 5000) */
  baseInterval?: number;
  /** Maximum retry attempts for failed requests (default: 3) */
  maxRetries?: number;
  /** Key for localStorage persistence (optional) */
  persistKey?: string;
  /** Whether to start polling immediately (default: true) */
  autoStart?: boolean;
}

export interface PollingState {
  isPolling: boolean;
  isPaused: boolean;
  lastUpdate: Date | null;
  error: string | null;
  retryCount: number;
}

// Helper functions for localStorage persistence
const getStoredPauseState = (key: string): boolean => {
  try {
    return JSON.parse(localStorage.getItem(key) || 'false');
  } catch {
    return false;
  }
};

const setStoredPauseState = (key: string, paused: boolean) => {
  try {
    localStorage.setItem(key, JSON.stringify(paused));
  } catch {
    // Ignore localStorage errors
  }
};

/**
 * Adaptive polling interval based on job status
 */
const getPollingInterval = (jobs: Pick<Job, 'status'>[], baseInterval: number): number => {
  const hasActiveJobs = jobs.some(job => job.status === 'running' || job.status === 'pending');
  return hasActiveJobs ? baseInterval : baseInterval * 2;
};

// Helper function to convert JobMinimal to Job for dashboard compatibility
const convertMinimalToJob = (minimal: JobMinimal): Job => ({
  ...minimal,
  user_id: '', // Will be filled by the current user context
  priority: 5, // Default priority
  data: { 
    agent_identifier: minimal.agent_identifier,
    title: minimal.title 
  },
  // Optional fields that aren't in minimal response
  result: undefined,
  result_format: undefined,
  error_message: undefined,
  started_at: undefined,
  completed_at: undefined,
  tags: undefined,
  metadata: undefined,
  progress: undefined,
  execution_time_ms: undefined,
});

/**
 * Simplified job polling hook using single useEffect pattern
 */
export const useJobPolling = (
  onUpdate: (jobs: Job[]) => void,
  options: PollingOptions = {}
) => {
  const { 
    baseInterval = 15000, 
    maxRetries = 3, 
    persistKey,
    autoStart = true 
  } = options;

  // Single source of truth for all state
  const [state, setState] = useState<PollingState>(() => ({
    isPolling: false,
    isPaused: persistKey ? getStoredPauseState(persistKey) : false,
    lastUpdate: null,
    error: null,
    retryCount: 0,
  }));

  // Refs for stable references
  const mountedRef = useRef(true);
  const currentJobsRef = useRef<Job[]>([]);
  const retryCountRef = useRef(0);
  const onUpdateRef = useRef(onUpdate);

  // Update the callback ref when it changes
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  // Reset mounted ref when component mounts
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Persist pause state changes
  useEffect(() => {
    if (persistKey) {
      setStoredPauseState(persistKey, state.isPaused);
    }
  }, [state.isPaused, persistKey]);

  // Main polling effect - handles everything in one place
  useEffect(() => {
    if (!autoStart || state.isPaused) {
      return;
    }

    let timeoutId: NodeJS.Timeout | null = null;
    let isActive = true;

    const poll = async () => {
      if (!isActive || state.isPaused) {
        return;
      }

      try {
        // Call fetchJobs directly instead of relying on the callback
        if (!mountedRef.current) {
          return;
        }

        setState(prev => ({ ...prev, isPolling: true, error: null }));

        try {
          const minimalJobs = await api.jobs.getAllMinimal({ limit: 50 });
          const jobs = minimalJobs.map(convertMinimalToJob);
          
          if (!mountedRef.current || !isActive) {
            return;
          }

          // Check pause state from current state rather than stale closure
          if (state.isPaused) {
            return;
          }

          currentJobsRef.current = jobs;
          retryCountRef.current = 0;
          
          setState(prev => ({
            ...prev,
            isPolling: false,
            lastUpdate: new Date(),
            error: null,
            retryCount: 0,
          }));

          onUpdateRef.current(jobs);

          if (!isActive) {
            return;
          }

          // Schedule next poll
          const interval = getPollingInterval(jobs, baseInterval);
          timeoutId = setTimeout(poll, interval);
          
        } catch (fetchError: unknown) {
          if (!mountedRef.current || !isActive || state.isPaused) return;

          retryCountRef.current++;
          const errorMessage = fetchError instanceof Error ? fetchError.message : 'Failed to fetch jobs';
          
          setState(prev => ({
            ...prev,
            isPolling: false,
            error: errorMessage,
            retryCount: retryCountRef.current,
          }));

          // Handle retries with exponential backoff
          if (retryCountRef.current <= maxRetries) {
            const retryDelay = baseInterval * Math.pow(2, retryCountRef.current - 1);
            timeoutId = setTimeout(poll, retryDelay);
          } else {
            // Max retries reached, reset and continue with regular polling
            retryCountRef.current = 0;
            setState(prev => ({ ...prev, retryCount: 0 }));
            timeoutId = setTimeout(poll, baseInterval);
          }
        }
        
      } catch (error) {
        // This catch block handles any other errors in the poll function
        if (!isActive || state.isPaused) return;
      }
    };

    // Start polling immediately
    poll();

    // Cleanup function
    return () => {
      isActive = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [state.isPaused, autoStart, baseInterval, maxRetries]);

  // Control functions
  const pausePolling = useCallback(() => {
    setState(prev => ({ ...prev, isPaused: true }));
  }, []);

  const resumePolling = useCallback(() => {
    setState(prev => ({ ...prev, isPaused: false }));
  }, []);

  const forceUpdate = useCallback(async () => {
    try {
      if (!mountedRef.current) {
        return;
      }

      setState(prev => ({ ...prev, isPolling: true, error: null }));

      const minimalJobs = await api.jobs.getAllMinimal({ limit: 50 });
      const jobs = minimalJobs.map(convertMinimalToJob);
      
      if (!mountedRef.current) {
        return;
      }

      currentJobsRef.current = jobs;
      retryCountRef.current = 0;
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        error: null,
        retryCount: 0,
      }));

      onUpdateRef.current(jobs);
    } catch (error: unknown) {
      if (!mountedRef.current) return;

      retryCountRef.current++;
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch jobs';
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        error: errorMessage,
        retryCount: retryCountRef.current,
      }));
    }
  }, []);

  return {
    pollingState: state,
    pausePolling,
    resumePolling,
    forceUpdate,
  };
};

/**
 * Simplified single job polling hook
 */
export const useSingleJobPolling = (
  jobId: string,
  onUpdate: (job: Job) => void,
  options: PollingOptions = {}
) => {
  const { 
    baseInterval = 3000, 
    maxRetries = 3,
    persistKey,
    autoStart = true 
  } = options;

  const [state, setState] = useState<PollingState>(() => ({
    isPolling: false,
    isPaused: persistKey ? getStoredPauseState(persistKey) : false,
    lastUpdate: null,
    error: null,
    retryCount: 0,
  }));

  const mountedRef = useRef(true);
  const currentJobRef = useRef<Job | null>(null);
  const retryCountRef = useRef(0);
  const onUpdateRef = useRef(onUpdate);

  // Update the callback ref when it changes
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  // Reset mounted ref when component mounts
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Persist pause state changes
  useEffect(() => {
    if (persistKey) {
      setStoredPauseState(persistKey, state.isPaused);
    }
  }, [state.isPaused, persistKey]);

  // Main polling effect for single job
  useEffect(() => {
    if (!autoStart || state.isPaused) return;

    let timeoutId: NodeJS.Timeout | null = null;
    let isActive = true;

    const poll = async () => {
      if (!isActive || state.isPaused) return;

      try {
        // Call API directly instead of relying on the callback
        if (!mountedRef.current) return;

        setState(prev => ({ ...prev, isPolling: true, error: null }));

        try {
          const job = await api.jobs.getById(jobId);
          
          if (!mountedRef.current || !isActive) return;

          // Check pause state from current state rather than stale closure
          if (state.isPaused) return;

          currentJobRef.current = job;
          retryCountRef.current = 0;
          
          setState(prev => ({
            ...prev,
            isPolling: false,
            lastUpdate: new Date(),
            error: null,
            retryCount: 0,
          }));

          onUpdateRef.current(job);

          if (!isActive || !job) return;

          // Only continue polling for active jobs
          if (job.status === 'pending' || job.status === 'running') {
            timeoutId = setTimeout(poll, baseInterval);
          }
          
        } catch (fetchError: unknown) {
          if (!mountedRef.current || !isActive || state.isPaused) return;

          retryCountRef.current++;
          const errorMessage = fetchError instanceof Error ? fetchError.message : 'Failed to fetch job';
          
          setState(prev => ({
            ...prev,
            isPolling: false,
            error: errorMessage,
            retryCount: retryCountRef.current,
          }));

          // Handle retries with exponential backoff
          if (retryCountRef.current <= maxRetries) {
            const retryDelay = baseInterval * Math.pow(2, retryCountRef.current - 1);
            timeoutId = setTimeout(poll, retryDelay);
          } else {
            // Max retries reached, reset and continue with regular polling
            retryCountRef.current = 0;
            setState(prev => ({ ...prev, retryCount: 0 }));
            timeoutId = setTimeout(poll, baseInterval);
          }
        }
        
      } catch (error) {
        if (!isActive || state.isPaused) return;
      }
    };

    // Start polling immediately
    poll();

    // Cleanup function
    return () => {
      isActive = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [state.isPaused, autoStart, baseInterval, maxRetries, jobId]); // Removed onUpdate from dependencies

  // Control functions
  const pausePolling = useCallback(() => {
    setState(prev => ({ ...prev, isPaused: true }));
  }, []);

  const resumePolling = useCallback(() => {
    setState(prev => ({ ...prev, isPaused: false }));
  }, []);

  const forceUpdate = useCallback(async () => {
    try {
      if (!mountedRef.current) {
        return;
      }

      setState(prev => ({ ...prev, isPolling: true, error: null }));

      const job = await api.jobs.getById(jobId);
      
      if (!mountedRef.current) {
        return;
      }

      currentJobRef.current = job;
      retryCountRef.current = 0;
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        error: null,
        retryCount: 0,
      }));

      onUpdateRef.current(job);
    } catch (error: unknown) {
      if (!mountedRef.current) return;

      retryCountRef.current++;
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch job';
      
      setState(prev => ({
        ...prev,
        isPolling: false,
        error: errorMessage,
        retryCount: retryCountRef.current,
      }));
    }
  }, [jobId]);

  return {
    pollingState: state,
    pausePolling,
    resumePolling,
    forceUpdate,
  };
}; 