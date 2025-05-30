import { useEffect, useRef, useCallback, useState } from 'react';
import { api, type Job } from './api';

export interface PollingOptions {
  /** Base polling interval in milliseconds (default: 5000) */
  baseInterval?: number;
  /** Whether to enable background tab optimization (default: true) */
  backgroundOptimization?: boolean;
  /** Maximum retry attempts for failed requests (default: 3) */
  maxRetries?: number;
  /** Multiplier for retry delays (default: 1.5) */
  retryBackoffMultiplier?: number;
  /** Whether to use lightweight polling when possible (default: true) */
  useLightweightPolling?: boolean;
}

export interface PollingState {
  isPolling: boolean;
  lastUpdate: Date | null;
  retryCount: number;
  error: string | null;
}

/**
 * Smart polling intervals based on job status
 */
const getPollingInterval = (
  jobs: Pick<Job, 'status'>[], 
  baseInterval: number, 
  isBackgroundTab: boolean
): number => {
  const hasActiveJobs = jobs.some(job => job.status === 'running' || job.status === 'pending');
  
  if (isBackgroundTab) {
    // Reduce polling frequency in background tabs
    return hasActiveJobs ? baseInterval * 4 : baseInterval * 8;
  }
  
  if (hasActiveJobs) {
    // More frequent polling for active jobs
    return baseInterval * 0.6; // 3 seconds if base is 5 seconds
  }
  
  // Less frequent polling when all jobs are completed/failed
  return baseInterval * 2;
};

/**
 * Hook for polling job status updates with smart optimizations
 */
export const useJobPolling = (
  onUpdate: (jobs: Job[]) => void,
  options: PollingOptions = {}
) => {
  const {
    baseInterval = 5000,
    backgroundOptimization = true,
    maxRetries = 3,
    retryBackoffMultiplier = 1.5,
    useLightweightPolling = true,
  } = options;

  const [pollingState, setPollingState] = useState<PollingState>({
    isPolling: false,
    lastUpdate: null,
    retryCount: 0,
    error: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobsRef = useRef<Job[]>([]);
  const isBackgroundTabRef = useRef(false);

  // Track if tab is active/background
  useEffect(() => {
    if (!backgroundOptimization) return;

    const handleVisibilityChange = () => {
      isBackgroundTabRef.current = document.hidden;
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [backgroundOptimization]);

  const fetchJobs = useCallback(async (isRetry = false): Promise<Job[]> => {
    try {
      setPollingState(prev => ({ 
        ...prev, 
        isPolling: true,
        error: isRetry ? prev.error : null 
      }));

      let jobs: Job[];

      if (useLightweightPolling && currentJobsRef.current.length > 0) {
        // Use lightweight polling for status updates
        const jobIds = currentJobsRef.current.map(job => job.id);
        const statusUpdates = await api.jobs.getBatchStatus(jobIds);
        
        // Merge status updates with existing job data
        jobs = currentJobsRef.current.map(job => {
          const statusUpdate = statusUpdates[job.id];
          return {
            ...job,
            status: (statusUpdate?.status as Job['status']) || job.status,
            updated_at: statusUpdate?.updated_at || job.updated_at,
          };
        });

        // If any jobs have status changes that require full data, fetch them
        const needsFullFetch = jobs.some(job => {
          const oldJob = currentJobsRef.current.find(j => j.id === job.id);
          return oldJob && oldJob.status !== job.status && 
                 (job.status === 'completed' || job.status === 'failed');
        });

        if (needsFullFetch) {
          jobs = await api.jobs.getAll();
        }
      } else {
        // Full fetch for initial load or when lightweight polling is disabled
        jobs = await api.jobs.getAll();
      }

      currentJobsRef.current = jobs;
      onUpdate(jobs);

      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        retryCount: 0,
        error: null,
      }));

      return jobs;
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to fetch jobs';
      
      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        retryCount: prev.retryCount + 1,
        error: errorMessage,
      }));

      throw error;
    }
  }, [onUpdate, useLightweightPolling]);

  const scheduleNextPoll = useCallback((jobs: Job[]) => {
    const interval = getPollingInterval(jobs, baseInterval, isBackgroundTabRef.current);
    
    intervalRef.current = setTimeout(async () => {
      try {
        const updatedJobs = await fetchJobs();
        scheduleNextPoll(updatedJobs);
      } catch (error) {
        // Handle retry logic
        if (pollingState.retryCount < maxRetries) {
          const retryDelay = baseInterval * Math.pow(retryBackoffMultiplier, pollingState.retryCount);
          
          retryTimeoutRef.current = setTimeout(async () => {
            try {
              const updatedJobs = await fetchJobs(true);
              scheduleNextPoll(updatedJobs);
            } catch (retryError) {
              // If retry fails, schedule next poll with exponential backoff
              scheduleNextPoll(currentJobsRef.current);
            }
          }, retryDelay);
        } else {
          // Max retries reached, continue polling with base interval
          scheduleNextPoll(currentJobsRef.current);
        }
      }
    }, interval);
  }, [baseInterval, fetchJobs, maxRetries, retryBackoffMultiplier, pollingState.retryCount]);

  const startPolling = useCallback(async () => {
    if (intervalRef.current) return; // Already polling

    try {
      const jobs = await fetchJobs();
      scheduleNextPoll(jobs);
    } catch (error) {
      // Initial fetch failed, start polling anyway with empty array
      scheduleNextPoll([]);
    }
  }, [fetchJobs, scheduleNextPoll]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    setPollingState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const forceUpdate = useCallback(async () => {
    try {
      await fetchJobs();
    } catch (error) {
      // Error handling is done in fetchJobs
    }
  }, [fetchJobs]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    pollingState,
    startPolling,
    stopPolling,
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
  const {
    baseInterval = 3000,
    backgroundOptimization = true,
    maxRetries = 3,
  } = options;

  const [pollingState, setPollingState] = useState<PollingState>({
    isPolling: false,
    lastUpdate: null,
    retryCount: 0,
    error: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobRef = useRef<Job | null>(null);
  const isBackgroundTabRef = useRef(false);

  // Track if tab is active/background
  useEffect(() => {
    if (!backgroundOptimization) return;

    const handleVisibilityChange = () => {
      isBackgroundTabRef.current = document.hidden;
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [backgroundOptimization]);

  const fetchJob = useCallback(async (): Promise<Job> => {
    setPollingState(prev => ({ ...prev, isPolling: true }));

    try {
      const job = await api.jobs.getById(jobId);
      currentJobRef.current = job;
      onUpdate(job);

      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        lastUpdate: new Date(),
        retryCount: 0,
        error: null,
      }));

      return job;
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to fetch job';
      
      setPollingState(prev => ({
        ...prev,
        isPolling: false,
        retryCount: prev.retryCount + 1,
        error: errorMessage,
      }));

      throw error;
    }
  }, [jobId, onUpdate]);

  const scheduleNextPoll = useCallback((job: Job | null) => {
    // Only poll if job is active (pending or running)
    if (!job || (job.status !== 'pending' && job.status !== 'running')) {
      return;
    }

    const interval = isBackgroundTabRef.current ? baseInterval * 3 : baseInterval;
    
    intervalRef.current = setTimeout(async () => {
      try {
        const updatedJob = await fetchJob();
        scheduleNextPoll(updatedJob);
      } catch (error) {
        // Retry logic for single job polling
        if (pollingState.retryCount < maxRetries) {
          setTimeout(async () => {
            try {
              const updatedJob = await fetchJob();
              scheduleNextPoll(updatedJob);
            } catch (retryError) {
              scheduleNextPoll(currentJobRef.current);
            }
          }, baseInterval * 2);
        } else {
          scheduleNextPoll(currentJobRef.current);
        }
      }
    }, interval);
  }, [baseInterval, fetchJob, maxRetries, pollingState.retryCount]);

  const startPolling = useCallback(async () => {
    if (intervalRef.current) return;

    try {
      const job = await fetchJob();
      scheduleNextPoll(job);
    } catch (error) {
      // Initial fetch failed, but still schedule polling
      scheduleNextPoll(null);
    }
  }, [fetchJob, scheduleNextPoll]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
    setPollingState(prev => ({ ...prev, isPolling: false }));
  }, []);

  const forceUpdate = useCallback(async () => {
    try {
      const job = await fetchJob();
      // Restart polling cycle
      stopPolling();
      scheduleNextPoll(job);
    } catch (error) {
      // Error handling is done in fetchJob
    }
  }, [fetchJob, scheduleNextPoll, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    pollingState,
    startPolling,
    stopPolling,
    forceUpdate,
  };
}; 