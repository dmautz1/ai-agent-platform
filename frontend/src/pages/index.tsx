import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { type Job } from '@/lib/api';
import { useJobPolling } from '@/lib/polling';
import { useToast } from '@/components/ui/toast';
import { useBreakpoint, responsivePadding, responsiveSpacing, touchButtonSizes } from '@/lib/responsive';
import JobList from '@/components/JobList';
import { JobForm } from '@/components/JobForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Plus, Activity, Clock, CheckCircle, XCircle, User, Wifi, WifiOff } from 'lucide-react';
import { StatsGridLoading } from '@/components/ui/loading';
import { ErrorMessage, AccessDeniedError } from '@/components/ui/error';
import { cn } from '@/lib/utils';

export const DashboardPage: React.FC = () => {
  const { user, signOut } = useAuth();
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

  // Initialize polling
  const { pollingState, startPolling, stopPolling, forceUpdate } = useJobPolling(
    handleJobUpdate,
    {
      baseInterval: 5000,
      backgroundOptimization: true,
      useLightweightPolling: true,
    }
  );

  // Start polling on mount
  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  // Handle polling errors
  useEffect(() => {
    if (pollingState.error) {
      setError(pollingState.error);
    }
  }, [pollingState.error]);

  const handleJobCreated = (jobId: string) => {
    setIsJobModalOpen(false);
    toast.success('Job created successfully!', {
      action: {
        label: 'View Details',
        onClick: () => window.location.href = `/job/${jobId}`
      }
    });
    forceUpdate(); // Force immediate update after job creation
  };

  const handleRefresh = async () => {
    await forceUpdate();
    toast.info('Dashboard refreshed');
  };

  const handleCreateJob = () => {
    setIsJobModalOpen(true);
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
              <h1 className="text-xl font-bold sm:text-2xl">AI Agent Template</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                Job Management Dashboard
              </p>
            </div>
          </div>
          
          {/* Mobile actions */}
          <div className="flex items-center gap-2 sm:gap-4">
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
        
        {/* Connection status - Mobile friendly */}
        <div className="mt-3 flex items-center justify-between sm:mt-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {pollingState.error ? (
              <WifiOff className="h-3 w-3 text-red-500" />
            ) : (
              <Wifi className="h-3 w-3 text-green-500" />
            )}
            <span className="truncate">
              {pollingState.error ? 'Connection Issues' : 
               pollingState.lastUpdate ? `Updated: ${pollingState.lastUpdate.toLocaleTimeString()}` :
               'Connecting...'}
            </span>
            {pollingState.isPolling && (
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            )}
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
      <Dialog open={isJobModalOpen} onOpenChange={setIsJobModalOpen}>
        <DialogContent className={cn(
          "w-full max-w-[calc(100vw-1rem)] max-h-[calc(100vh-2rem)]",
          "sm:max-w-[600px] sm:max-h-[80vh]",
          "overflow-y-auto"
        )}>
          <DialogHeader className={responsivePadding.card}>
            <DialogTitle className="text-lg sm:text-xl">Create New Job</DialogTitle>
            <DialogDescription className="text-sm sm:text-base">
              Configure and submit a new AI agent job.
            </DialogDescription>
          </DialogHeader>
          <div className={responsivePadding.card}>
            <JobForm onJobCreated={handleJobCreated} />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DashboardPage; 