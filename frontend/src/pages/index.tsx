import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { type Job } from '@/lib/api';
import type { AgentInfo } from '@/lib/models';
import { useJobPolling } from '@/lib/polling';
import { useToast } from '@/components/ui/toast';
import { useBreakpoint, responsivePadding, responsiveSpacing, touchButtonSizes } from '@/lib/responsive';
import JobList from '@/components/JobList';
import { JobCreationModal } from '@/components/JobCreationModal';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Activity, Clock, CheckCircle, XCircle, User, Wifi, WifiOff, Search, Pause, Play } from 'lucide-react';
import { StatsGridLoading } from '@/components/ui/loading';
import { ErrorMessage, AccessDeniedError } from '@/components/ui/error';
import { cn } from '@/lib/utils';

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
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();
  const { isMobile } = useBreakpoint();
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
  });
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [showAgentDirectory, setShowAgentDirectory] = useState(false);
  const [recentAgents, setRecentAgents] = useState<string[]>([]);

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
    setError('');
  }, [updateStats]);

  // Initialize job polling
  const { pollingState, startPolling, stopPolling, pausePolling, resumePolling, forceUpdate } = useJobPolling(
    handleJobUpdate,
    {
      baseInterval: 5000,
      persistKey: 'dashboard_polling_paused',
    }
  );

  // Initialize polling and load initial data
  useEffect(() => {
    // Load recent agents from localStorage
    setRecentAgents(getRecentAgents());
    
    // Always fetch initial data
    forceUpdate();
    // Start polling (will respect persisted pause state)
    startPolling();
    
    return () => stopPolling();
  }, [startPolling, stopPolling, forceUpdate]);

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
      setError(pollingState.error);
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
    setError('');
    await forceUpdate();
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

  const StatCard: React.FC<{ 
    title: string; 
    value: number; 
    icon: React.ReactNode; 
    color: string;
  }> = ({ title, value, icon, color }) => (
    <Card className="touch-manipulation">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium leading-none">{title}</CardTitle>
        <div className={`${color}`}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tabular-nums">{value}</div>
      </CardContent>
    </Card>
  );

  // Mobile header component
  const MobileHeader: React.FC = () => (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className={cn(responsivePadding.section, "py-3 sm:py-4")}>
        <div className="flex items-center justify-between">
          {/* Mobile menu and title */}
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">AI Agent Platform</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                Job Management Dashboard
              </p>
            </div>
          </div>
          
          {/* Mobile actions */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Agent Directory button */}
            <Button 
              variant="outline"
              size="sm" 
              className={cn(
                "flex items-center gap-2 touch-manipulation",
                touchButtonSizes.sm
              )} 
              onClick={() => navigate('/agent-directory')}
            >
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline">Agents</span>
            </Button>
            
            {/* Create job button */}
            <Button 
              size="sm" 
              className={cn(
                "flex items-center gap-2 touch-manipulation",
                touchButtonSizes.sm
              )} 
              onClick={handleCreateJob}
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New Job</span>
              <span className="sm:hidden">New</span>
            </Button>
            
            {/* Theme switcher */}
            <ThemeSwitcher />
            
            {/* User menu */}
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg border sm:px-3 sm:py-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium max-w-[100px] truncate sm:max-w-none">
                {user?.name || user?.email}
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={signOut}
                className="h-6 px-2 text-xs sm:ml-2"
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
        
        {/* Connection status with pause/start control */}
        <div className="mt-3 flex items-center justify-between sm:mt-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {pollingState.error ? (
              <WifiOff className="h-3 w-3 text-red-500" />
            ) : pollingState.isPaused ? (
              <Pause className="h-3 w-3 text-orange-500" />
            ) : (
              <Wifi className="h-3 w-3 text-green-500" />
            )}
            <span className="truncate">
              {pollingState.error ? 'Connection Issues' : 
               pollingState.isPaused ? 'Auto-refresh paused' :
               pollingState.lastUpdate ? `Updated: ${pollingState.lastUpdate.toLocaleTimeString()}` :
               'Connecting...'}
            </span>
            {pollingState.isPolling && !pollingState.isPaused && (
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            )}
            
            {/* Pause/Start button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleTogglePolling}
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              title={pollingState.isPaused ? "Start auto-refresh" : "Pause auto-refresh"}
            >
              {pollingState.isPaused ? (
                <Play className="h-3 w-3" />
              ) : (
                <Pause className="h-3 w-3" />
              )}
            </Button>
          </div>
          
          {/* Stats summary on mobile */}
          {!loading && !error && isMobile && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span>{stats.total} jobs</span>
              {stats.running > 0 && (
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  {stats.running} running
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );

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
      <MobileHeader />

      {/* Main Content */}
      <main className={cn(responsivePadding.section, responsiveSpacing.component)}>
        <div className="space-y-6 sm:space-y-8">
          {/* Stats Grid - Responsive */}
          <div className="grid gap-3 grid-cols-2 sm:gap-4 md:grid-cols-3 lg:grid-cols-5">
            {loading ? (
              <StatsGridLoading count={5} />
            ) : error && !pollingState.lastUpdate ? (
              <div className="col-span-full">
                <ErrorMessage
                  title="Failed to Load Statistics"
                  message={error}
                  action={{
                    label: 'Retry',
                    onClick: handleRefresh
                  }}
                />
              </div>
            ) : (
              <>
                <StatCard
                  title="Total Jobs"
                  value={stats.total}
                  icon={<Activity className="h-4 w-4" />}
                  color="text-blue-600"
                />
                <StatCard
                  title="Pending"
                  value={stats.pending}
                  icon={<Clock className="h-4 w-4" />}
                  color="text-yellow-600"
                />
                <StatCard
                  title="Running"
                  value={stats.running}
                  icon={<Activity className="h-4 w-4" />}
                  color="text-blue-600"
                />
                <StatCard
                  title="Completed"
                  value={stats.completed}
                  icon={<CheckCircle className="h-4 w-4" />}
                  color="text-green-600"
                />
                <StatCard
                  title="Failed"
                  value={stats.failed}
                  icon={<XCircle className="h-4 w-4" />}
                  color="text-red-600"
                />
              </>
            )}
          </div>

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