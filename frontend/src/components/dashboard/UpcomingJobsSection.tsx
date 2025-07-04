import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, handleApiError } from '@/lib/api';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Calendar,
  Clock,
  AlertCircle,
  Play,
  RefreshCw,
  Pause,
  ChevronRight,
  Plus,
  ArrowRight,
  Settings,
  TrendingUp,
  ExternalLink,
  Zap
} from 'lucide-react';
import { responsiveTable, touchButtonSizes } from '@/lib/responsive';
import { cn } from '@/lib/utils';

interface UpcomingJob {
  id: string;
  title: string;
  agent_name: string;
  cron_expression: string;
  next_run: string;
  enabled: boolean;
  description?: string;
}

interface UpcomingJobsSectionProps {
  /** Maximum number of upcoming jobs to display */
  limit?: number;
  
  /** Whether the section is collapsible */
  collapsible?: boolean;
  
  /** Initial collapsed state if collapsible */
  initiallyCollapsed?: boolean;
  
  /** Additional CSS class */
  className?: string;
  
  /** Show management actions */
  showActions?: boolean;
  
  /** External polling control */
  onRefresh?: () => void | Promise<void>;
  
  /** Whether a refresh is currently in progress */
  isRefreshing?: boolean;
  
  /** Force refresh function for external control */
  forceRefresh?: number;
}

/**
 * UpcomingJobsSection Component
 * 
 * Displays upcoming scheduled jobs with:
 * - Next scheduled executions
 * - Schedule details and status
 * - Quick enable/disable actions
 * - Navigation to full schedule management
 * - Collapsible design for dashboard integration
 */
export const UpcomingJobsSection: React.FC<UpcomingJobsSectionProps> = ({
  limit = 5,
  collapsible = true,
  initiallyCollapsed = false,
  className = '',
  showActions = true,
  isRefreshing,
  forceRefresh
}) => {
  const navigate = useNavigate();
  const toast = useToast();
  
  const [upcomingJobs, setUpcomingJobs] = useState<UpcomingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [isCollapsed, setIsCollapsed] = useState(initiallyCollapsed);
  const [retryCount, setRetryCount] = useState(0);
  const [operationsInProgress, setOperationsInProgress] = useState<Set<string>>(new Set());

  // Set operation in progress for a schedule
  const setOperationInProgress = (scheduleId: string, inProgress: boolean) => {
    setOperationsInProgress(prev => {
      const newSet = new Set(prev);
      if (inProgress) {
        newSet.add(scheduleId);
      } else {
        newSet.delete(scheduleId);
      }
      return newSet;
    });
  };

  // Load upcoming jobs with retry mechanism
  const loadUpcomingJobs = async (retryAttempt = 0) => {
    setLoading(true);
    setError('');

    try {
      const jobs = await api.schedules.getAllUpcoming(limit);
      setUpcomingJobs(jobs);
      setError('');
      setRetryCount(0);
    } catch (err) {
      console.error('Failed to load upcoming jobs:', err);
      const errorMessage = handleApiError(err);
      
      // Implement exponential backoff for retries
      if (retryAttempt < 2) {
        const delay = Math.pow(2, retryAttempt) * 1000; // 1s, 2s
        setTimeout(() => {
          loadUpcomingJobs(retryAttempt + 1);
        }, delay);
        return;
      }
      
      setError(errorMessage);
      setRetryCount(retryAttempt + 1);
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadUpcomingJobs();
  }, [limit]);

  // Handle external refresh calls
  useEffect(() => {
    if (forceRefresh && forceRefresh > 0) {
      loadUpcomingJobs();
    }
  }, [forceRefresh]);

  // Toggle schedule enabled/disabled with enhanced error handling
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
      setUpcomingJobs(prev => prev.map(job =>
        job.id === scheduleId
          ? { ...job, enabled: !currentEnabled }
          : job
      ));
      
      // Reload to get updated next run times
      await loadUpcomingJobs();
    } catch (err) {
      console.error('Failed to toggle schedule:', err);
      const errorMessage = handleApiError(err);
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

  // Run schedule immediately
  const runScheduleNow = async (scheduleId: string, title: string) => {
    setOperationInProgress(scheduleId, true);
    
    try {
      const result = await api.schedules.runNow(scheduleId);
      toast.success(`Job "${title}" started successfully`, {
        title: `Job ID: ${result.job_id}`,
        action: {
          label: 'View Job',
          onClick: () => navigate('/dashboard')
        }
      });
      
      // Optionally reload upcoming jobs to reflect any changes
      await loadUpcomingJobs();
    } catch (err) {
      console.error('Failed to run schedule immediately:', err);
      const errorMessage = handleApiError(err);
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

  // Format next run time
  const formatNextRun = (nextRunString: string) => {
    const nextRun = new Date(nextRunString);
    const now = new Date();
    const diffMs = nextRun.getTime() - now.getTime();
    
    if (diffMs < 0) return 'Overdue';
    
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours < 1) {
      return diffMinutes <= 1 ? 'In 1 minute' : `In ${diffMinutes} minutes`;
    }
    
    if (diffHours < 24) {
      return `In ${diffHours}h ${diffMinutes}m`;
    }
    
    const diffDays = Math.floor(diffHours / 24);
    return `In ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
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

  const renderContent = () => {
    if (loading) {
      return (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center space-x-3 p-3 animate-pulse">
              <div className="w-2 h-2 bg-gray-200 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (error) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">Failed to Load Upcoming Jobs</p>
              <p className="text-sm">{error}</p>
              {retryCount > 0 && (
                <p className="text-xs text-muted-foreground">
                  Failed after {retryCount} attempt{retryCount !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          </AlertDescription>
        </Alert>
      );
    }

    if (upcomingJobs.length === 0) {
      return (
        <div className="text-center py-8 text-muted-foreground">
          <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="font-medium">No Upcoming Scheduled Jobs</p>
          <p className="text-sm">Create your first schedule to see upcoming executions here.</p>
          {showActions && (
            <div className="mt-4 space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/scheduled-jobs')}
                className="flex items-center gap-1"
              >
                <Plus className="h-3 w-3" />
                Create Schedule
              </Button>
            </div>
          )}
        </div>
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
              {showActions && (
                <TableHead className={cn(responsiveTable.header, "text-right")}>Actions</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {upcomingJobs.map((job) => {
              const isOperationInProgress = operationsInProgress.has(job.id);
              
              return (
                <TableRow 
                  key={job.id} 
                  className="hover:bg-muted/50 cursor-pointer" 
                  onClick={() => navigate(`/schedule-history/${job.id}`)}
                >
                  <TableCell className={cn(responsiveTable.cell, "font-medium")}>
                    {job.title}
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <Badge variant="outline" className="flex items-center gap-1 text-xs">
                      <Settings className="h-3 w-3" />
                      {job.agent_name}
                    </Badge>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatCronExpression(job.cron_expression)}
                    </span>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <span className="text-sm font-medium text-blue-600">
                      {formatNextRun(job.next_run)}
                    </span>
                  </TableCell>
                  <TableCell className={responsiveTable.cell}>
                    <Badge 
                      variant={job.enabled ? "default" : "secondary"}
                      className="flex items-center gap-1 text-xs"
                    >
                      <Calendar className="h-2 w-2" />
                      {job.enabled ? 'Active' : 'Paused'}
                    </Badge>
                  </TableCell>
                  {showActions && (
                    <TableCell className={cn(responsiveTable.cell, "text-right")}>
                      <div className="flex gap-1 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            runScheduleNow(job.id, job.title);
                          }}
                          disabled={isOperationInProgress}
                          className={cn(touchButtonSizes.sm, "h-7 px-2")}
                          title="Run schedule now"
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
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleSchedule(job.id, job.enabled);
                          }}
                          disabled={isOperationInProgress}
                          className={cn(touchButtonSizes.sm, "h-7 px-2")}
                          title={job.enabled ? 'Disable schedule' : 'Enable schedule'}
                        >
                          {isOperationInProgress ? (
                            <RefreshCw className="h-3 w-3 animate-spin" />
                          ) : job.enabled ? (
                            <Pause className="h-3 w-3" />
                          ) : (
                            <Play className="h-3 w-3" />
                          )}
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/schedule-history/${job.id}`);
                          }}
                          disabled={isOperationInProgress}
                          className={cn(touchButtonSizes.sm, "h-7 px-2")}
                          title="View schedule history"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    );
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 sm:pb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <CardTitle className="text-lg sm:text-xl">Upcoming Jobs</CardTitle>
          {isRefreshing && (
            <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {upcomingJobs.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {upcomingJobs.length} upcoming
            </Badge>
          )}
          
          {showActions && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadUpcomingJobs()}
                disabled={isRefreshing}
                className="h-7 px-2 text-xs"
              >
                <RefreshCw className={cn("h-3 w-3 mr-1", isRefreshing && "animate-spin")} />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/scheduled-jobs')}
                className="h-7 px-2 text-xs"
              >
                Manage All
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </>
          )}
          
          {collapsible && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="h-6 w-6 p-0"
            >
              <ChevronRight
                className={cn(
                  "h-4 w-4 transition-transform",
                  !isCollapsed && "rotate-90"
                )}
              />
            </Button>
          )}
        </div>
      </CardHeader>
      
      {!isCollapsed && (
        <CardContent className="pt-0">
          {renderContent()}
        </CardContent>
      )}
    </Card>
  );
};

export default UpcomingJobsSection; 