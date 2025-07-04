import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { type Job } from '@/lib/api';
import type { AgentInfo } from '@/lib/types';
import { useJobPolling } from '@/lib/polling';
import { useToast } from '@/components/ui/toast';
import { responsivePadding, responsiveSpacing } from '@/lib/responsive';
import JobList from '@/components/JobList';
import { JobCreationModal } from '@/components/JobCreationModal';
import { Card, CardContent } from '@/components/ui/card';
import { AccessDeniedError } from '@/components/ui/error';
import { cn } from '@/lib/utils';
import UpcomingJobsSection from '@/components/dashboard/UpcomingJobsSection';
import StatsOverviewSection from '@/components/dashboard/StatsOverviewSection';
import AppHeader from '@/components/common/AppHeader';

// Simple localStorage helper for recent agents
const RECENT_AGENTS_KEY = 'recent_agents';
const MAX_RECENT_AGENTS = 5;

const getRecentAgents = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem(RECENT_AGENTS_KEY) || '[]');
  } catch {
    return [];
  }
};

const addRecentAgent = (agentId: string) => {
  const recent = getRecentAgents().filter(id => id !== agentId);
  recent.unshift(agentId);
  localStorage.setItem(RECENT_AGENTS_KEY, JSON.stringify(recent.slice(0, MAX_RECENT_AGENTS)));
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
  });
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [showAgentDirectory, setShowAgentDirectory] = useState(false);
  const [recentAgents, setRecentAgents] = useState<string[]>([]);
  
  // Force refresh counter for upcoming jobs
  const [upcomingJobsRefreshCounter, setUpcomingJobsRefreshCounter] = useState(0);

  // Calculate stats from jobs array
  const updateStats = useCallback((jobsData: Job[]) => {
    const newStats = {
      total: jobsData.length,
      pending: jobsData.filter(job => job.status === 'pending').length,
      running: jobsData.filter(job => job.status === 'running').length,
      completed: jobsData.filter(job => job.status === 'completed').length,
      failed: jobsData.filter(job => job.status === 'failed').length,
    };
    setStats(newStats);
  }, []);

  // Handle job updates from polling
  const handleJobUpdate = useCallback((updatedJobs: Job[]) => {
    setJobs(updatedJobs);
    updateStats(updatedJobs);
    setLoading(false);
  }, [updateStats]);

  // Initialize job polling
  const { pollingState, pausePolling, resumePolling, forceUpdate } = useJobPolling(
    handleJobUpdate,
    {
      baseInterval: 5000,
      persistKey: 'dashboard_polling_paused',
      autoStart: true
    }
  );

  // Initialize polling and load initial data
  useEffect(() => {
    // Load recent agents from localStorage
    setRecentAgents(getRecentAgents());
    
    // Force an initial update to load data immediately
    forceUpdate();
  }, [forceUpdate]);

  // Handle URL parameters and polling errors
  useEffect(() => {
    // Handle URL parameters for agent selection
    const agentParam = searchParams.get('agent');
    if (agentParam) {
      setSelectedAgentId(agentParam);
      setShowAgentDirectory(false);
      setIsJobModalOpen(true);
      // Clear the URL parameter after handling it
      setSearchParams(params => {
        params.delete('agent');
        return params;
      });
    }

    // Handle polling errors
    if (pollingState.error) {
      console.error('Polling error:', pollingState.error);
    }
  }, [searchParams, setSearchParams, pollingState.error]);

  const handleJobCreated = (jobId: string) => {
    // Add to recent agents
    if (selectedAgentId) {
      addRecentAgent(selectedAgentId);
      setRecentAgents(getRecentAgents());
    }
    
    setIsJobModalOpen(false);
    setSelectedAgentId('');
    setShowAgentDirectory(false);
    toast.success(`Job ${jobId} created successfully!`);
    forceUpdate(); // Refresh the job list
  };

  const handleRefresh = async () => {
    setLoading(true);
    await forceUpdate();
    // Also refresh upcoming jobs
    setUpcomingJobsRefreshCounter(prev => prev + 1);
    setLoading(false);
  };

  const handleTogglePolling = () => {
    if (pollingState.isPaused) {
      // Resume polling
      resumePolling();
      toast.info('Auto-refresh resumed');
    } else {
      // Pause polling
      pausePolling();
      toast.info('Auto-refresh paused');
    }
  };

  const handleCreateJob = () => {
    setSelectedAgentId('');
    setShowAgentDirectory(false);
    setIsJobModalOpen(true);
  };

  const handleQuickAgentSelected = (agentId: string) => {
    setSelectedAgentId(agentId);
    setShowAgentDirectory(false);
  };

  const handleBrowseAllAgents = () => {
    navigate('/agent-directory');
  };

  const handleAgentDirectorySelected = (agent: AgentInfo) => {
    setSelectedAgentId(agent.identifier);
    setShowAgentDirectory(false);
  };

  const handleBackToAgentSelection = () => {
    setSelectedAgentId('');
    setShowAgentDirectory(false);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
        <Card className="w-full max-w-md">
          <CardContent className={responsivePadding.card}>
            <AccessDeniedError
              message="Please sign in to access the dashboard."
              onSignIn={() => window.location.reload()}
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppHeader onCreateJob={handleCreateJob} />

      {/* Main Content */}
      <main className={cn(responsivePadding.section, responsiveSpacing.component)}>
        <div className="space-y-6 sm:space-y-8">
          {/* Stats Overview Section */}
          <StatsOverviewSection
            stats={stats}
            loading={loading}
            pollingState={pollingState}
            onRefresh={handleRefresh}
            onTogglePolling={handleTogglePolling}
          />

          {/* Upcoming Scheduled Jobs Section */}
          <UpcomingJobsSection
            limit={5}
            showActions={true}
            className="transition-all duration-200"
            onRefresh={handleRefresh}
            isRefreshing={pollingState.isPolling}
            forceRefresh={upcomingJobsRefreshCounter}
          />

          {/* Job List with real-time updates */}
          <JobList 
            jobs={jobs}
            loading={loading}
            error={pollingState.error}
            onRefresh={handleRefresh}
            isRefreshing={pollingState.isPolling}
            onCreateJob={handleCreateJob}
          />
        </div>
      </main>

      {/* Job Modal - Mobile optimized */}
      <JobCreationModal
        isOpen={isJobModalOpen}
        onOpenChange={setIsJobModalOpen}
        selectedAgentId={selectedAgentId}
        showAgentDirectory={showAgentDirectory}
        recentAgents={recentAgents}
        onJobCreated={handleJobCreated}
        onQuickAgentSelected={handleQuickAgentSelected}
        onBrowseAllAgents={handleBrowseAllAgents}
        onAgentDirectorySelected={handleAgentDirectorySelected}
        onBackToAgentSelection={handleBackToAgentSelection}
      />
    </div>
  );
};

export default DashboardPage; 