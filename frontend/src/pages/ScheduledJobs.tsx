import React, { useState, useEffect, useCallback, useRef } from 'react';
import { api, handleApiError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Clock, 
  Play, 
  Pause, 
  Search,
  RefreshCw,
  Settings,
  X,
  Trash2,
  Edit,
  AlertCircle,
  CheckCircle,
  XCircle,
  History,
  Zap
} from 'lucide-react';
import { RefreshLoading } from '@/components/ui/loading';
import { EmptyState } from '@/components/ui/empty-state';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';
import { responsivePadding, touchButtonSizes, responsiveTextSizes, responsiveTable } from '@/lib/responsive';
import { PageLoading } from '@/components/ui/loading';
import { JobForm } from '@/components/forms/JobForm';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
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
  user_id: string;
  last_run?: string | null;
  success_count?: number;
  failure_count?: number;
  agent_config_data: any;
}

interface ScheduledJobsState {
  schedules: Schedule[];
  loading: boolean;
  error: string | null;
  refreshing: boolean;
  operationInProgress: Set<string>; // Track which schedules have operations in progress
}

export const ScheduledJobs: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  
  const [state, setState] = useState<ScheduledJobsState>({
    schedules: [],
    loading: true,
    error: null,
    refreshing: false,
    operationInProgress: new Set()
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [retryCount, setRetryCount] = useState(0);
  const toast = useToast();
  const navigate = useNavigate();

  // Modal state for editing schedules
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Track component mount state to prevent memory leaks
  const isMountedRef = useRef(true);

  // Cleanup on unmount and reset on mount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Load schedules with exponential backoff retry
  const loadSchedules = useCallback(async (isRefresh = false, retryAttempt = 0) => {
    // Don't make API calls if component is unmounted
    if (!isMountedRef.current) {
      return;
    }

    if (isRefresh) {
      setState(prev => ({ ...prev, refreshing: true }));
    } else {
      setState(prev => ({ ...prev, loading: true, error: null }));
    }

    try {
      const schedules = await api.schedules.getAll();
      
      // Check if component is still mounted before updating state
      if (!isMountedRef.current) return;
      
      setState(prev => ({
        ...prev,
        schedules,
        loading: false,
        refreshing: false,
        error: null
      }));
      setRetryCount(0);
    } catch (error) {
      // Check if component is still mounted before handling error
      if (!isMountedRef.current) return;
      
      console.error('Failed to load schedules:', error);
      const errorMessage = handleApiError(error);
      
      // Implement exponential backoff for retries - but prevent infinite loops in tests
      const isTestEnvironment = process.env.NODE_ENV === 'test' || (typeof global !== 'undefined' && (global as any).vi);
      if (retryAttempt < 3 && !isTestEnvironment) {
        const delay = Math.pow(2, retryAttempt) * 1000; // 1s, 2s, 4s
        setTimeout(() => {
          if (isMountedRef.current) { // Only retry if component is still mounted
            loadSchedules(isRefresh, retryAttempt + 1);
          }
        }, delay);
        return;
      }
      
      setState(prev => ({
        ...prev,
        loading: false,
        refreshing: false,
        error: errorMessage
      }));
      setRetryCount(retryAttempt + 1);
    }
  }, []);

  // Load schedules when user is authenticated
  useEffect(() => {
    if (!authLoading && user) {
      loadSchedules();
    }
  }, [user, authLoading, loadSchedules]);

  // Set operation in progress for a schedule
  const setOperationInProgress = (scheduleId: string, inProgress: boolean) => {
    setState(prev => {
      const newSet = new Set(prev.operationInProgress);
      if (inProgress) {
        newSet.add(scheduleId);
      } else {
        newSet.delete(scheduleId);
      }
      return {
        ...prev,
        operationInProgress: newSet
      };
    });
  };

  // Toggle schedule enabled/disabled with better error handling
  const toggleSchedule = async (scheduleId: string, currentEnabled: boolean) => {
    setOperationInProgress(scheduleId, true);
    
    try {
      if (currentEnabled) {
        await api.schedules.disable(scheduleId);
        toast.success('Schedule disabled successfully');
      } else {
        await api.schedules.enable(scheduleId);
        toast.success('Schedule enabled successfully');
      }
      
      // Update local state
      setState(prev => ({
        ...prev,
        schedules: prev.schedules.map(schedule =>
          schedule.id === scheduleId
            ? { ...schedule, enabled: !currentEnabled }
            : schedule
        )
      }));
    } catch (error) {
      console.error('Failed to toggle schedule:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to ${currentEnabled ? 'disable' : 'enable'} schedule`, {
        title: errorMessage,
        action: {
          label: 'Retry',
          onClick: () => toggleSchedule(scheduleId, currentEnabled)
        }
      });
    } finally {
      setOperationInProgress(scheduleId, false);
    }
  };

  // Delete schedule with enhanced confirmation and error handling
  const deleteSchedule = async (scheduleId: string, title: string) => {
    // Enhanced confirmation dialog with more details
    const schedule = state.schedules.find(s => s.id === scheduleId);
    if (!schedule) return;

    const confirmMessage = `Are you sure you want to delete the schedule "${title}"?\n\n` +
      `This will:\n` +
      `• Stop all future scheduled executions\n` +
      `• Remove the schedule permanently\n` +
      `• Keep existing job history\n\n` +
      `This action cannot be undone.`;

    if (!confirm(confirmMessage)) {
      return;
    }

    setOperationInProgress(scheduleId, true);

    try {
      await api.schedules.delete(scheduleId);
      toast.success(`Schedule "${title}" deleted successfully`);
      
      // Remove from local state
      setState(prev => ({
        ...prev,
        schedules: prev.schedules.filter(schedule => schedule.id !== scheduleId)
      }));
    } catch (error) {
      console.error('Failed to delete schedule:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to delete schedule "${title}"`, {
        title: errorMessage,
        action: {
          label: 'Retry',
          onClick: () => deleteSchedule(scheduleId, title)
        }
      });
    } finally {
      setOperationInProgress(scheduleId, false);
    }
  };

  // Run schedule immediately
  const runScheduleNow = async (scheduleId: string, title: string) => {
    setOperationInProgress(scheduleId, true);
    
    try {
      const result = await api.schedules.runNow(scheduleId);
      toast.success(`Job "${title}" started successfully`, {
        title: `Job ID: ${result.job_id}`,
        action: {
          label: 'View Jobs',
          onClick: () => navigate('/dashboard')
        }
      });
      
      // Optionally reload schedules to reflect any changes
      await loadSchedules(true);
    } catch (error) {
      console.error('Failed to run schedule immediately:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to run "${title}" immediately`, {
        title: errorMessage,
        action: {
          label: 'Retry',
          onClick: () => runScheduleNow(scheduleId, title)
        }
      });
    } finally {
      setOperationInProgress(scheduleId, false);
    }
  };

  // Filter schedules
  const filteredSchedules = state.schedules.filter(schedule => {
    const matchesSearch = !searchQuery || 
      schedule.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      schedule.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      schedule.agent_name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'enabled' && schedule.enabled) ||
      (statusFilter === 'disabled' && !schedule.enabled);
    
    const matchesAgent = agentFilter === 'all' || schedule.agent_name === agentFilter;
    
    return matchesSearch && matchesStatus && matchesAgent;
  });

  // Get unique agents for filter
  const uniqueAgents = [...new Set(state.schedules.map(s => s.agent_name))].sort();

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setAgentFilter('all');
  };

  const hasActiveFilters = searchQuery || statusFilter !== 'all' || agentFilter !== 'all';

  // Format dates
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Format cron expression to human readable
  const formatCronExpression = (cron: string) => {
    // Simple mapping for common patterns
    const patterns: Record<string, string> = {
      '0 9 * * *': 'Daily at 9:00 AM',
      '0 */6 * * *': 'Every 6 hours',
      '0 0 * * 0': 'Weekly on Sunday',
      '0 0 1 * *': 'Monthly on 1st'
    };
    
    return patterns[cron] || cron;
  };

  // Render schedules table
  const renderSchedulesTable = () => {
    if (filteredSchedules.length === 0) {
      return (
        <EmptyState
          title={state.schedules.length === 0 ? "No Schedules Found" : "No Matching Schedules"}
          description={
            state.schedules.length === 0
              ? "Create your first schedule to automate agent jobs"
              : "Try adjusting your search criteria or filters"
          }
          className="py-12"
        />
      );
    }

    return (
      <div className={responsiveTable.container}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className={responsiveTable.header}>Title</TableHead>
              <TableHead className={responsiveTable.header}>Agent</TableHead>
              <TableHead className={responsiveTable.header}>Schedule</TableHead>
              <TableHead className={responsiveTable.header}>Next Run</TableHead>
              <TableHead className={responsiveTable.header}>Status</TableHead>
              <TableHead className={responsiveTable.header}>Stats</TableHead>
              <TableHead className={cn(responsiveTable.header, "text-right")}>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredSchedules.map((schedule) => {
              const isOperationInProgress = state.operationInProgress.has(schedule.id);
              
              return (
                <TableRow 
                  key={schedule.id} 
                  className="hover:bg-muted/50"
                >
                  <TableCell className={cn(responsiveTable.cell, "font-medium")}>
                    <div>
                      <div className="font-semibold">{schedule.title}</div>
                      <div className="text-xs text-muted-foreground truncate">{schedule.description}</div>
                    </div>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <Badge variant="outline" className="flex items-center gap-1 text-xs">
                      <Settings className="h-3 w-3" />
                      {schedule.agent_name}
                    </Badge>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatCronExpression(schedule.cron_expression)}
                    </span>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <span className="text-sm text-muted-foreground">
                      {schedule.next_run ? formatDate(schedule.next_run) : 'Not scheduled'}
                    </span>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <Badge 
                      variant={schedule.enabled ? "default" : "secondary"}
                      className="flex items-center gap-1 text-xs"
                    >
                      {schedule.enabled ? (
                        <CheckCircle className="h-3 w-3" />
                      ) : (
                        <Pause className="h-3 w-3" />
                      )}
                      {schedule.enabled ? 'Active' : 'Paused'}
                    </Badge>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <div className="flex items-center gap-2 text-xs">
                      {schedule.success_count !== undefined && (
                        <span className="flex items-center gap-1 text-green-600">
                          <CheckCircle className="h-3 w-3" />
                          {schedule.success_count}
                        </span>
                      )}
                      {schedule.failure_count !== undefined && schedule.failure_count > 0 && (
                        <span className="flex items-center gap-1 text-red-600">
                          <XCircle className="h-3 w-3" />
                          {schedule.failure_count}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className={cn(responsiveTable.cell, "text-right")}>
                    <div className="flex items-center gap-1 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => runScheduleNow(schedule.id, schedule.title)}
                        disabled={isOperationInProgress}
                        className="h-7 px-2 text-xs"
                      >
                        {isOperationInProgress ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : (
                          <Zap className="h-3 w-3" />
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleSchedule(schedule.id, schedule.enabled)}
                        disabled={isOperationInProgress}
                        className="h-7 px-2 text-xs"
                      >
                        {isOperationInProgress ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : schedule.enabled ? (
                          <Pause className="h-3 w-3" />
                        ) : (
                          <Play className="h-3 w-3" />
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/schedule-history/${schedule.id}`)}
                        disabled={isOperationInProgress}
                        className="h-7 px-2 text-xs"
                      >
                        <History className="h-3 w-3" />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditSchedule(schedule.id)}
                        disabled={isOperationInProgress}
                        className="h-7 px-2 text-xs"
                      >
                        <Edit className="h-3 w-3" />
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteSchedule(schedule.id, schedule.title)}
                        disabled={isOperationInProgress}
                        className="h-7 px-2 text-xs text-red-600 hover:text-red-700 hover:border-red-300"
                      >
                        {isOperationInProgress ? (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : (
                          <Trash2 className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    );
  };

  // Handle edit button click
  const handleEditSchedule = async (scheduleId: string) => {
    try {
      setModalLoading(true);
      const scheduleData = await api.schedules.getById(scheduleId);
      if (scheduleData) {
        setEditingSchedule(scheduleData);
        setIsEditModalOpen(true);
      } else {
        toast.error('Schedule not found');
      }
    } catch (err) {
      console.error('Error loading schedule:', err);
      const errorMessage = handleApiError(err);
      toast.error(`Failed to load schedule: ${errorMessage}`);
    } finally {
      setModalLoading(false);
    }
  };

  // Handle schedule update completion
  const handleScheduleUpdated = useCallback(() => {
    toast.success('Schedule updated successfully');
    setIsEditModalOpen(false);
    setEditingSchedule(null);
    loadSchedules(); // Refresh the schedules list
  }, [loadSchedules]);

  // Handle modal close
  const handleModalClose = (open: boolean) => {
    if (!open) {
      setIsEditModalOpen(false);
      setEditingSchedule(null);
    }
  };

  // Add authentication state check
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <AppHeader 
          subtitle="Scheduled Jobs Management"
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
          subtitle="Scheduled Jobs Management"
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
                    <p className={responsiveTextSizes.sm}>Please log in to view scheduled jobs.</p>
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
          subtitle="Scheduled Jobs Management"
          showCreateJobButton={false}
          currentPage="scheduled-jobs"
        />
        
        <main className={cn(responsivePadding.section, "pt-6")}>
          <div className="space-y-6">
            <div className="h-8 bg-gray-200 rounded animate-pulse" />
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className={responsivePadding.card}>
                    <div className="space-y-3">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                      <div className="h-3 bg-gray-200 rounded w-2/3" />
                    </div>
                  </CardContent>
                </Card>
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
          subtitle="Scheduled Jobs Management"
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
                    <p className="font-medium">Failed to Load Scheduled Jobs</p>
                    <p className={responsiveTextSizes.sm}>{state.error}</p>
                    {retryCount > 0 && (
                      <p className="text-xs text-muted-foreground">
                        Failed after {retryCount} attempt{retryCount !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
              <div className="mt-4 flex flex-col sm:flex-row gap-2">
                <Button 
                  onClick={() => loadSchedules()} 
                  disabled={state.refreshing}
                  variant="outline"
                  className={touchButtonSizes.default}
                >
                  <RefreshCw className={cn("mr-2 h-4 w-4", state.refreshing && "animate-spin")} />
                  {state.refreshing ? 'Retrying...' : 'Retry'}
                </Button>
                <Button 
                  onClick={() => navigate('/dashboard')} 
                  variant="ghost"
                  className={touchButtonSizes.default}
                >
                  Back to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppHeader 
        subtitle="Scheduled Jobs Management"
        showCreateJobButton={false}
        currentPage="scheduled-jobs"
      />

      {/* Main Content */}
      <main className={cn(responsivePadding.section, "pt-6")}>
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h2 className={cn("font-bold", responsiveTextSizes['2xl'])}>Scheduled Jobs</h2>
                <p className={cn("text-muted-foreground", responsiveTextSizes.base)}>
                  Manage your automated agent schedules
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={responsiveTextSizes.sm}>
                  {filteredSchedules.length} schedule{filteredSchedules.length !== 1 ? 's' : ''}
                </Badge>
                <RefreshLoading
                  isRefreshing={state.refreshing}
                  onRefresh={() => loadSchedules(true)}
                  size="sm"
                />
              </div>
            </div>
          </div>

          {/* Filters */}
          <div>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 items-start sm:items-center">
                {/* Search */}
                <div className="relative flex-1 min-w-0">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search schedules by title, description, or agent..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className={cn("pl-10")}
                  />
                </div>

                {/* Filter Controls */}
                <div className="flex flex-wrap gap-2 items-center">
                  <Select value={statusFilter} onValueChange={(value: 'all' | 'enabled' | 'disabled') => setStatusFilter(value)}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="enabled">Enabled Only</SelectItem>
                      <SelectItem value="disabled">Disabled Only</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={agentFilter} onValueChange={setAgentFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Agent" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Agents</SelectItem>
                      {uniqueAgents.map((agent) => (
                        <SelectItem key={agent} value={agent}>
                          {agent}
                        </SelectItem>
                      ))}
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

          {/* Schedules List */}
          <Card>
            <CardContent className="p-0">
              {renderSchedulesTable()}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Edit Schedule Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={handleModalClose}>
        <DialogContent className={cn(
          "w-full max-w-[calc(100vw-1rem)] max-h-[calc(100vh-2rem)]",
          "sm:max-w-[700px] sm:max-h-[90vh]",
          "overflow-y-auto"
        )}>
          <DialogHeader>
            <DialogTitle>Edit Schedule: {editingSchedule?.title}</DialogTitle>
          </DialogHeader>
          
          {modalLoading ? (
            <div className="flex items-center justify-center p-8">
              <PageLoading text="Loading schedule..." />
            </div>
          ) : editingSchedule ? (
            <JobForm
              agentId={editingSchedule.agent_name}
              onJobCreated={handleScheduleUpdated}
              editMode={{
                scheduleId: editingSchedule.id,
                initialData: {
                  title: editingSchedule.title,
                  cronExpression: editingSchedule.cron_expression,
                  scheduleEnabled: editingSchedule.enabled,
                  // Map the agent config data to form fields
                  ...editingSchedule.agent_config_data.job_data
                }
              }}
            />
          ) : (
            <div className="text-center text-muted-foreground p-8">
              Schedule not found
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ScheduledJobs; 