import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, handleApiError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ArrowLeft,
  Clock, 
  Search, 
  Filter, 
  X, 
  RefreshCw, 
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle,
  Settings,
  BarChart3,
  ExternalLink,
  Play,
  Pause
} from 'lucide-react';
import { RefreshLoading } from '@/components/ui/loading';
import { EmptyState } from '@/components/ui/empty-state';
import { PageLoading } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import { responsivePadding, touchButtonSizes, responsiveTextSizes, responsiveTable } from '@/lib/responsive';
import AppHeader from '@/components/common/AppHeader';

interface Schedule {
  id: string;
  title: string;
  description: string;
  agent_name: string;
  cron_expression: string;
  enabled: boolean;
  next_run: string | null;
  created_at: string;
  updated_at: string;
  success_count?: number;
  failure_count?: number;
  last_run?: string | null;
}

interface ScheduleExecutionHistory {
  schedule_id: string;
  job_id: string;
  execution_time: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  duration_seconds?: number | null;
  error_message?: string | null;
  result_preview?: string | null;
}

interface ScheduleHistoryState {
  schedule: Schedule | null;
  jobs: ScheduleExecutionHistory[];
  loading: boolean;
  error: string | null;
  refreshing: boolean;
  totalCount: number;
  currentPage: number;
  limit: number;
}

export const ScheduleHistory: React.FC = () => {
  const { scheduleId } = useParams<{ scheduleId: string }>();
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  
  const [state, setState] = useState<ScheduleHistoryState>({
    schedule: null,
    jobs: [],
    loading: true,
    error: null,
    refreshing: false,
    totalCount: 0,
    currentPage: 1,
    limit: 20
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'>('all');

  // Track component mount state to prevent memory leaks
  const isMountedRef = useRef(true);

  // Cleanup on unmount and reset on mount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Load schedule details and job history
  const loadData = useCallback(async (isRefresh = false, page = 1) => {
    if (!scheduleId || !isMountedRef.current) return;

    if (isRefresh) {
      setState(prev => ({ ...prev, refreshing: true }));
    } else {
      setState(prev => ({ ...prev, loading: true, error: null }));
    }

    try {
      // Load schedule details and job history in parallel
      const [scheduleResponse, historyResponse] = await Promise.all([
        api.schedules.getById(scheduleId),
        api.schedules.getHistory(scheduleId, state.limit, (page - 1) * state.limit)
      ]);

      if (!isMountedRef.current) return;

      setState(prev => ({
        ...prev,
        schedule: scheduleResponse,
        jobs: historyResponse.jobs,
        totalCount: historyResponse.total_count,
        currentPage: page,
        loading: false,
        refreshing: false,
        error: null
      }));
    } catch (error) {
      if (!isMountedRef.current) return;
      
      console.error('Failed to load schedule history:', error);
      const errorMessage = handleApiError(error);
      setState(prev => ({
        ...prev,
        loading: false,
        refreshing: false,
        error: errorMessage
      }));
    }
  }, [scheduleId, state.limit]);

  // Load data when user is authenticated
  useEffect(() => {
    if (!authLoading && user && scheduleId) {
      loadData();
    }
  }, [user, authLoading, scheduleId, loadData]);

  // Toggle schedule enabled/disabled
  const toggleSchedule = async (currentEnabled: boolean) => {
    if (!scheduleId || !state.schedule) return;

    try {
      if (currentEnabled) {
        await api.schedules.disable(scheduleId);
        toast.success('Schedule disabled');
      } else {
        await api.schedules.enable(scheduleId);
        toast.success('Schedule enabled');
      }
      
      // Update local state
      setState(prev => ({
        ...prev,
        schedule: prev.schedule ? { ...prev.schedule, enabled: !currentEnabled } : null
      }));
    } catch (error) {
      console.error('Failed to toggle schedule:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to ${currentEnabled ? 'disable' : 'enable'} schedule: ${errorMessage}`);
    }
  };

  // Filter jobs
  const filteredJobs = state.jobs.filter(job => {
    const matchesSearch = !searchQuery || 
      job.job_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (job.error_message && job.error_message.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (job.result_preview && job.result_preview.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
  };

  const hasActiveFilters = searchQuery || statusFilter !== 'all';

  // Format dates
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Format duration
  const formatDuration = (job: ScheduleExecutionHistory) => {
    if (!job.duration_seconds) return 'N/A';
    
    const seconds = Math.round(job.duration_seconds);
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  // Get status badge
  const getStatusBadge = (status: ScheduleExecutionHistory['status']) => {
    const configs = {
      pending: { variant: 'secondary' as const, icon: Clock, color: 'text-yellow-600' },
      running: { variant: 'default' as const, icon: Play, color: 'text-blue-600' },
      completed: { variant: 'default' as const, icon: CheckCircle, color: 'text-green-600' },
      failed: { variant: 'destructive' as const, icon: XCircle, color: 'text-red-600' },
      cancelled: { variant: 'secondary' as const, icon: XCircle, color: 'text-gray-600' }
    };
    
    const config = configs[status];
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1 text-xs">
        <Icon className="h-3 w-3" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  // Format cron expression to human readable
  const formatCronExpression = (cron: string) => {
    const patterns: Record<string, string> = {
      '0 9 * * *': 'Daily at 9:00 AM',
      '0 */6 * * *': 'Every 6 hours',
      '0 0 * * 0': 'Weekly on Sunday',
      '0 0 1 * *': 'Monthly on 1st'
    };
    return patterns[cron] || cron;
  };

  // Render job history table
  const renderJobHistoryTable = () => {
    if (filteredJobs.length === 0) {
      return (
        <EmptyState
          title={hasActiveFilters ? "No jobs match your filters" : "No Job History"}
          description={
            hasActiveFilters
              ? "Try adjusting your search criteria or clearing filters."
              : "This schedule hasn't created any jobs yet."
          }
          className="py-12"
          action={hasActiveFilters ? {
            label: "Clear Filters",
            onClick: clearFilters,
            variant: "outline" as const
          } : undefined}
        />
      );
    }

    return (
      <div className={responsiveTable.container}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className={responsiveTable.header}>Job ID</TableHead>
              <TableHead className={responsiveTable.header}>Status</TableHead>
              <TableHead className={responsiveTable.header}>Execution Time</TableHead>
              <TableHead className={responsiveTable.header}>Duration</TableHead>
              <TableHead className={responsiveTable.header}>Result</TableHead>
              <TableHead className={cn(responsiveTable.header, "text-right")}>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredJobs.map((job) => (
              <TableRow key={job.job_id} className="hover:bg-muted/50">
                <TableCell className={cn(responsiveTable.cell, "font-medium")}>
                  <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
                    {job.job_id.slice(0, 8)}
                  </code>
                </TableCell>
                <TableCell className={responsiveTable.cell}>
                  {getStatusBadge(job.status)}
                </TableCell>
                <TableCell className={responsiveTable.cell}>
                  <div className="flex items-center gap-1 text-sm">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    {formatDate(job.execution_time)}
                  </div>
                </TableCell>
                <TableCell className={responsiveTable.cell}>
                  <div className="flex items-center gap-1 text-sm">
                    <BarChart3 className="h-3 w-3 text-muted-foreground" />
                    {formatDuration(job)}
                  </div>
                </TableCell>
                <TableCell className={responsiveTable.cell}>
                  <div className="max-w-xs">
                    {job.error_message && (
                      <div className="flex items-center gap-1 text-xs text-destructive">
                        <XCircle className="h-3 w-3" />
                        <span className="truncate">{job.error_message}</span>
                      </div>
                    )}
                    {job.result_preview && !job.error_message && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <CheckCircle className="h-3 w-3 text-green-600" />
                        <span className="truncate">{job.result_preview}</span>
                      </div>
                    )}
                    {!job.error_message && !job.result_preview && (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </div>
                </TableCell>
                <TableCell className={cn(responsiveTable.cell, "text-right")}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/job/${job.job_id}`)}
                    className="h-7 px-2 text-xs"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };

  // Add authentication state check
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Schedule History"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        <main className={cn(responsivePadding.section, "pt-6")}>
          <PageLoading text="Checking authentication..." />
        </main>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Schedule History"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        <main className={cn(responsivePadding.section, "pt-6")}>
          <Card>
            <CardContent className="pt-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">Authentication Required</p>
                    <p className={responsiveTextSizes.sm}>Please log in to view schedule history.</p>
                  </div>
                </AlertDescription>
              </Alert>
              <div className="mt-4">
                <Button onClick={() => navigate('/auth')} className={touchButtonSizes.default}>
                  Go to Login
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  if (state.loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Schedule History"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        <main className={cn(responsivePadding.section, "pt-6")}>
          <div className="space-y-6">
            <div className="h-8 bg-gray-200 rounded animate-pulse" />
            <div className="h-32 bg-gray-200 rounded animate-pulse" />
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Schedule History"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        <main className={cn(responsivePadding.section, "pt-6")}>
          <div className="space-y-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/scheduled-jobs')}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Scheduled Jobs
            </Button>
            
            <Card>
              <CardContent className="pt-6">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2">
                      <p className="font-medium">Failed to Load Schedule History</p>
                      <p className={responsiveTextSizes.sm}>{state.error}</p>
                    </div>
                  </AlertDescription>
                </Alert>
                <div className="mt-4 flex flex-col sm:flex-row gap-2">
                  <Button 
                    onClick={() => loadData()} 
                    disabled={state.refreshing}
                    variant="outline"
                    className={touchButtonSizes.default}
                  >
                    <RefreshCw className={cn("mr-2 h-4 w-4", state.refreshing && "animate-spin")} />
                    {state.refreshing ? 'Retrying...' : 'Retry'}
                  </Button>
                  <Button 
                    onClick={() => navigate('/scheduled-jobs')} 
                    variant="ghost"
                    className={touchButtonSizes.default}
                  >
                    Back to Scheduled Jobs
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  if (!state.schedule) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Schedule History"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        <main className={cn(responsivePadding.section, "pt-6")}>
          <Button
            variant="ghost"
            onClick={() => navigate('/scheduled-jobs')}
            className="flex items-center gap-2 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Scheduled Jobs
          </Button>
          <EmptyState
            title="Schedule Not Found"
            description="The requested schedule could not be found."
            className="py-12"
          />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppHeader 
        subtitle="Schedule History"
        showCreateJobButton={false}
        currentPage="scheduled-jobs"
      />

      {/* Main Content */}
      <main className={cn(responsivePadding.section, "pt-6")}>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/scheduled-jobs')}
              className="flex items-center gap-2 self-start"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Scheduled Jobs
            </Button>
            
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className={cn("font-bold", responsiveTextSizes['2xl'])}>Schedule History</h2>
                <p className={cn("text-muted-foreground", responsiveTextSizes.base)}>
                  Job execution history for "{state.schedule.title}"
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={responsiveTextSizes.sm}>
                  {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''}
                </Badge>
                <RefreshLoading
                  isRefreshing={state.refreshing}
                  onRefresh={() => loadData(true, state.currentPage)}
                  size="sm"
                />
              </div>
            </div>
          </div>

          {/* Schedule Details */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="flex items-center gap-3">
                    {state.schedule.title}
                    <Badge 
                      variant={state.schedule.enabled ? "default" : "secondary"}
                      className="flex items-center gap-1"
                    >
                      {state.schedule.enabled ? (
                        <CheckCircle className="h-3 w-3" />
                      ) : (
                        <Pause className="h-3 w-3" />
                      )}
                      {state.schedule.enabled ? "Active" : "Paused"}
                    </Badge>
                  </CardTitle>
                  <p className="text-muted-foreground mt-1">{state.schedule.description}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => toggleSchedule(state.schedule!.enabled)}
                  className="flex items-center gap-1"
                >
                  {state.schedule.enabled ? (
                    <>
                      <Pause className="h-3 w-3" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="h-3 w-3" />
                      Enable
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Agent:</span>
                  <Badge variant="outline">{state.schedule.agent_name}</Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Schedule:</span>
                  <span className="text-muted-foreground">
                    {formatCronExpression(state.schedule.cron_expression)}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Next Run:</span>
                  <span className="text-muted-foreground">
                    {state.schedule.next_run ? formatDate(state.schedule.next_run) : 'Not scheduled'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">Success Rate:</span>
                  <span className="text-muted-foreground">
                    {state.schedule.success_count || 0} / {(state.schedule.success_count || 0) + (state.schedule.failure_count || 0)} jobs
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filters */}
          <div>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 items-start sm:items-center">
              {/* Search */}
              <div className="relative flex-1 min-w-0">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs by ID, error, or result..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={cn("pl-10")}
                />
              </div>

              {/* Filter Controls */}
              <div className="flex flex-wrap gap-2 items-center">
                <Select value={statusFilter} onValueChange={(value: 'all' | 'pending' | 'running' | 'completed' | 'failed' | 'cancelled') => setStatusFilter(value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>

                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    onClick={clearFilters}
                    className="flex items-center gap-1 h-8 px-3 text-xs"
                  >
                    <X className="h-3 w-3" />
                    Clear
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Job History Table */}
          <Card>
            <CardContent className="p-0">
              {renderJobHistoryTable()}
            </CardContent>
          </Card>

          {/* Pagination Info */}
          {state.totalCount > state.limit && (
            <div className="flex justify-center items-center gap-2">
              <p className="text-sm text-muted-foreground">
                Showing {Math.min(filteredJobs.length, state.limit)} of {state.totalCount} jobs
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ScheduleHistory; 