import { useEffect, useRef, useCallback, useState } from 'react';
import { api, type Job } from './api';

export interface PollingOptions {
  /** Base polling interval in milliseconds (default: 5000) */
  baseInterval?: number;
  /** Maximum retry attempts for failed requests (default: 3) */
  maxRetries?: number;
  /** Key for localStorage persistence (optional) */
  persistKey?: string;
}

export interface PollingState {
  isPolling: boolean;
  lastUpdate: Date | null;
  error: string | null;
  isPaused: boolean;
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
  localStorage.setItem(key, JSON.stringify(paused));
};

/**
 * Simple polling intervals based on job status
 */
const getPollingInterval = (jobs: Pick<Job, 'status'>[], baseInterval: number): number => {
  const hasActiveJobs = jobs.some(job => job.status === 'running' || job.status === 'pending');
  return hasActiveJobs ? baseInterval : baseInterval * 2;
};

/**
 * Hook for polling job status updates
 */
export const useJobPolling = (
  onUpdate: (jobs: Job[]) => void,
  options: PollingOptions = {}
) => {
  const { baseInterval = 5000, maxRetries = 3, persistKey } = options;

  const [pollingState, setPollingState] = useState<PollingState>({
    isPolling: false,
    lastUpdate: null,
    error: null,
    isPaused: persistKey ? getStoredPauseState(persistKey) : false,
    retryCount: 0,
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobsRef = useRef<Job[]>([]);
  const isPausedRef = useRef(pollingState.isPaused);
  const retryCountRef = useRef(0);

  // Keep paused ref in sync and persist to localStorage
  useEffect(() => {
    isPausedRef.current = pollingState.isPaused;
    if (persistKey) {
      setStoredPauseState(persistKey, pollingState.isPaused);
    }
  }, [pollingState.isPaused, persistKey]);

  const fetchJobs = useCallback(async (): Promise<Job[]> => {
    setPollingState(prev => ({ ...prev, isPolling: true, error: null }));

    try {
      const jobs = await api.jobs.getAll();
      currentJobsRef.current = jobs;
      retryCountRef.current = 0;
      onUpdate(jobs);

      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        error: null,
        retryCount: 0,
      }));

      return jobs;
    } catch (error: unknown) {
      retryCountRef.current++;
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch jobs';
      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        error: errorMessage,
        retryCount: retryCountRef.current,
      }));
      throw error;
    }
  }, [onUpdate]);

  const scheduleNextPoll = useCallback((jobs: Job[] = []) => {
    if (isPausedRef.current) return;

    const interval = getPollingInterval(jobs, baseInterval);
    
    timeoutRef.current = setTimeout(async () => {
      if (isPausedRef.current) return;
      
      try {
        const updatedJobs = await fetchJobs();
        scheduleNextPoll(updatedJobs);
      } catch {
        // Retry count already handled in fetchJobs
        if (retryCountRef.current <= maxRetries) {
          // Retry with exponential backoff
          const retryDelay = baseInterval * Math.pow(2, retryCountRef.current - 1);
          timeoutRef.current = setTimeout(() => {
            if (!isPausedRef.current) {
              scheduleNextPoll(currentJobsRef.current);
            }
          }, retryDelay);
        } else {
          // Max retries reached, continue with regular interval
          retryCountRef.current = 0;
          setPollingState(prev => ({ ...prev, retryCount: 0 }));
          scheduleNextPoll(currentJobsRef.current);
        }
      }
    }, interval);
  }, [baseInterval, fetchJobs, maxRetries]);

  const startPolling = useCallback(async () => {
    if (timeoutRef.current) return;

    // Only set isPaused to false if not persisted as paused
    setPollingState(prev => ({ 
      ...prev, 
      isPaused: persistKey ? getStoredPauseState(persistKey) : false,
      retryCount: 0,
    }));
    retryCountRef.current = 0;

    // Don't start polling if paused
    if (persistKey && getStoredPauseState(persistKey)) {
      return;
    }

    try {
      const jobs = await fetchJobs();
      scheduleNextPoll(jobs);
    } catch {
      scheduleNextPoll([]);
    }
  }, [fetchJobs, scheduleNextPoll, persistKey]);

  const stopPolling = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setPollingState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const pausePolling = useCallback(() => {
    setPollingState(prev => ({ ...prev, isPaused: true }));
    stopPolling();
  }, [stopPolling]);

  const resumePolling = useCallback(async () => {
    setPollingState(prev => ({ ...prev, isPaused: false }));
    await startPolling();
  }, [startPolling]);

  const forceUpdate = useCallback(async () => {
    try {
      const jobs = await fetchJobs();
      if (!isPausedRef.current && !timeoutRef.current) {
        scheduleNextPoll(jobs);
      }
    } catch {
      // Error handled in fetchJobs
    }
  }, [fetchJobs, scheduleNextPoll]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  return {
    pollingState,
    startPolling,
    stopPolling,
    pausePolling,
    resumePolling,
    forceUpdate,
  };
};

/**
 * Hook for polling a single job's status
 */
export const useSingleJobPolling = (
  jobId: string,
  onUpdate: (job: Job) => void,
  options: PollingOptions = {}
) => {
  const { baseInterval = 3000, maxRetries = 3 } = options;

  const [pollingState, setPollingState] = useState<PollingState>({
    isPolling: false,
    lastUpdate: null,
    error: null,
    isPaused: false,
    retryCount: 0,
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobRef = useRef<Job | null>(null);
  const isPausedRef = useRef(false);
  const retryCountRef = useRef(0);

  // Keep paused ref in sync
  useEffect(() => {
    isPausedRef.current = pollingState.isPaused;
  }, [pollingState.isPaused]);

  const fetchJob = useCallback(async (): Promise<Job> => {
    setPollingState(prev => ({ ...prev, isPolling: true, error: null }));

    try {
      const job = await api.jobs.getById(jobId);
      currentJobRef.current = job;
      retryCountRef.current = 0;
      onUpdate(job);

      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        error: null,
        retryCount: 0,
      }));

      return job;
    } catch (error: unknown) {
      retryCountRef.current++;
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch job';
      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        error: errorMessage,
        retryCount: retryCountRef.current,
      }));
      throw error;
    }
  }, [jobId, onUpdate]);

  const scheduleNextPoll = useCallback((job: Job | null) => {
    // Only poll active jobs and when not paused
    if (!job || (job.status !== 'pending' && job.status !== 'running') || isPausedRef.current) {
      return;
    }

    timeoutRef.current = setTimeout(async () => {
      if (isPausedRef.current) return;
      
      try {
        const updatedJob = await fetchJob();
        scheduleNextPoll(updatedJob);
      } catch {
        setPollingState(prev => ({ ...prev, retryCount: retryCountRef.current }));
        
        if (retryCountRef.current <= maxRetries) {
          const retryDelay = baseInterval * Math.pow(2, retryCountRef.current - 1);
          timeoutRef.current = setTimeout(() => {
            if (!isPausedRef.current) {
              scheduleNextPoll(currentJobRef.current);
            }
          }, retryDelay);
        } else {
          retryCountRef.current = 0;
          setPollingState(prev => ({ ...prev, retryCount: 0 }));
          scheduleNextPoll(currentJobRef.current);
        }
      }
    }, baseInterval);
  }, [baseInterval, fetchJob, maxRetries]);

  const startPolling = useCallback(async () => {
    if (timeoutRef.current) return;

    setPollingState(prev => ({ ...prev, isPaused: false, retryCount: 0 }));
    retryCountRef.current = 0;

    try {
      const job = await fetchJob();
      scheduleNextPoll(job);
    } catch {
      scheduleNextPoll(null);
    }
  }, [fetchJob, scheduleNextPoll]);

  const stopPolling = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setPollingState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const pausePolling = useCallback(() => {
    setPollingState(prev => ({ ...prev, isPaused: true }));
    stopPolling();
  }, [stopPolling]);

  const resumePolling = useCallback(async () => {
    setPollingState(prev => ({ ...prev, isPaused: false }));
    await startPolling();
  }, [startPolling]);

  const forceUpdate = useCallback(async () => {
    try {
      const job = await fetchJob();
      if (!isPausedRef.current) {
        stopPolling();
        scheduleNextPoll(job);
      }
    } catch {
      // Error handled in fetchJob
    }
  }, [fetchJob, scheduleNextPoll, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  return {
    pollingState,
    startPolling,
    stopPolling,
    pausePolling,
    resumePolling,
    forceUpdate,
  };
}; 