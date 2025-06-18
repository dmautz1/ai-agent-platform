import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, type Job, handleApiError } from '@/lib/api';
import { useBreakpoint, responsivePadding, responsiveTable, touchButtonSizes } from '@/lib/responsive';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle, XCircle, Clock, PlayCircle, ChevronRight, RotateCcw, RefreshCw } from 'lucide-react';
import { TableLoading, RefreshLoading } from '@/components/ui/loading';
import { ErrorCard } from '@/components/ui/error';
import { EmptyJobs } from '@/components/ui/empty-state';
import { useToast } from '@/components/ui/toast';
import { cn } from '@/lib/utils';

interface JobListProps {
  /** Pre-fetched jobs data */
  jobs?: Job[];
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Refresh function */
  onRefresh?: () => void | Promise<void>;
  /** Whether a refresh is currently in progress */
  isRefreshing?: boolean;
  /** Refresh interval for backward compatibility */
  refreshInterval?: number;
  /** Create job callback */
  onCreateJob?: () => void;
}

export const JobList: React.FC<JobListProps> = ({ 
  jobs: externalJobs,
  loading: externalLoading,
  error: externalError,
  onRefresh,
  isRefreshing: externalRefreshing,
  refreshInterval = 5000,
  onCreateJob
}) => {
  const [internalJobs, setInternalJobs] = useState<Job[]>([]);
  const [internalLoading, setInternalLoading] = useState(true);
  const [internalError, setInternalError] = useState<string>('');
  const [internalRefreshing, setInternalRefreshing] = useState(false);
  const [rerunningJobs, setRerunningJobs] = useState<Set<string>>(new Set());
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const toast = useToast();

  // Use external data if provided, otherwise fall back to internal management
  const jobs = externalJobs ?? internalJobs;
  const loading = externalLoading ?? internalLoading;
  const error = externalError ?? internalError;
  const refreshing = externalRefreshing ?? internalRefreshing;

  const fetchJobs = useCallback(async (isRefresh = false) => {
    // If external data management is provided, use the external refresh function
    if (externalJobs && onRefresh) {
      try {
        await onRefresh();
      } catch (err) {
        // Handle external refresh errors gracefully
        console.warn('External refresh failed:', err);
        if (isRefresh) {
          const errorMessage = handleApiError(err);
          toast.error('Failed to refresh jobs', { title: errorMessage });
        }
        // Re-throw the error so the caller knows it failed
        throw err;
      }
      return;
    }

    try {
      if (isRefresh) {
        setInternalRefreshing(true);
      } else {
        setInternalLoading(true);
      }
      setInternalError('');

      const jobsData = await api.jobs.getAll();
      setInternalJobs(jobsData);
      
      if (isRefresh) {
        toast.success(`Refreshed ${jobsData.length} jobs`);
      }

    } catch (err: unknown) {
      const errorMessage = handleApiError(err);
      setInternalError(errorMessage);
      
      if (!isRefresh) {
        toast.error('Failed to load jobs');
      } else {
        toast.error('Failed to refresh jobs');
      }
      // Re-throw the error so the caller knows it failed
      throw err;
    } finally {
      setInternalLoading(false);
      setInternalRefreshing(false);
    }
  }, [externalJobs, onRefresh, toast, handleApiError]);

  const handleRerunJob = async (job: Job, event: React.MouseEvent) => {
    event.stopPropagation();
    
    setRerunningJobs(prev => new Set(prev).add(job.id));
    
    try {
      const result = await api.jobs.rerun(job.id);
      
      toast.success(
        `Job rerun initiated successfully! Processing new job...`,
        {
          title: `Original: ${job.id.slice(0, 8)}... → New: ${result.new_job_id.slice(0, 8)}...`,
          action: {
            label: 'View New Job',
            onClick: () => navigate(`/job/${result.new_job_id}`)
          }
        }
      );
      
      // Try to refresh job list to show the new job, but don't fail if refresh fails
      try {
        await fetchJobs(true);
      } catch (refreshError) {
        // Silently handle refresh errors - the rerun was successful regardless
        console.warn('Failed to refresh job list after rerun:', refreshError);
      }
      
      // Navigate to the new job after a short delay
      setTimeout(() => {
        navigate(`/job/${result.new_job_id}`);
      }, 1000);
      
    } catch (err: unknown) {
      const errorMessage = handleApiError(err);
      toast.error('Failed to rerun job', {
        title: errorMessage
      });
    } finally {
      setRerunningJobs(prev => {
        const next = new Set(prev);
        next.delete(job.id);
        return next;
      });
    }
  };

  useEffect(() => {
    // Only set up internal polling if no external data is provided
    if (externalJobs) return;

    fetchJobs();
    
    // Set up polling for job updates
    const interval = setInterval(() => {
      fetchJobs(true);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, externalJobs, fetchJobs]);

  const getStatusBadge = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="secondary" className="flex items-center gap-1 text-xs">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      case 'running':
        return (
          <Badge variant="default" className="flex items-center gap-1 bg-blue-500 hover:bg-blue-600 text-xs">
            <PlayCircle className="h-3 w-3" />
            Running
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="default" className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-xs">
            <CheckCircle className="h-3 w-3" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="flex items-center gap-1 text-xs">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="outline" className="text-xs">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string, isMobile = false) => {
    const date = new Date(dateString);
    if (isMobile) {
      return date.toLocaleDateString();
    }
    return date.toLocaleString();
  };

  const getAgentIdentifierFromJob = (job: Job): string => {
    // Agent identifier can be at top level or in job.data
    const dataAgentId = typeof job.data?.agent_identifier === 'string' ? job.data.agent_identifier : undefined;
    return job.agent_identifier || dataAgentId || 'unknown';
  };

  const getAgentDisplayName = (agentIdentifier: string): string => {
    if (!agentIdentifier || agentIdentifier === 'unknown') {
      return 'UNKNOWN';
    }
    
    // Convert identifier to display name (simple_prompt -> Simple Prompt)
    return agentIdentifier
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getAgentIdentifierDisplay = (agentIdentifier: string) => {
    if (!agentIdentifier || agentIdentifier === 'unknown') {
      return (
        <span className="text-xs text-muted-foreground font-mono">
          UNKNOWN
        </span>
      );
    }
    
    const displayName = getAgentDisplayName(agentIdentifier);
    
    return (
      <span className="text-xs text-muted-foreground" title={agentIdentifier}>
        {displayName}
      </span>
    );
  };

  const getTitleFromJob = (job: Job): string => {
    const dataTitle = typeof job.data?.title === 'string' ? job.data.title : undefined;
    return job.title || dataTitle || `Job ${job.id.slice(0, 8)}`;
  };

  // Mobile card component for each job
  const MobileJobCard: React.FC<{ job: Job }> = ({ job }) => {
    const isRerunning = rerunningJobs.has(job.id);
    
    return (
      <Card 
        className="touch-manipulation cursor-pointer transition-colors hover:bg-muted/50 active:bg-muted" 
        onClick={() => navigate(`/job/${job.id}`)}
      >
        <CardContent className={cn(responsivePadding.card, "space-y-3")}>
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-sm leading-tight truncate">
                {getTitleFromJob(job)}
              </h3>
              <p className="text-xs text-muted-foreground font-mono mt-1">
                ID: {job.id.slice(0, 8)}...
              </p>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
          </div>
          
          {/* Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {getAgentIdentifierDisplay(getAgentIdentifierFromJob(job))}
            {getStatusBadge(job.status)}
          </div>
          
          {/* Dates */}
          <div className="space-y-1 text-xs text-muted-foreground">
            <div>Created: {formatDate(job.created_at, true)}</div>
            <div>Updated: {formatDate(job.updated_at, true)}</div>
          </div>
          
          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/job/${job.id}`);
              }}
              className={cn(touchButtonSizes.sm, "flex-1")}
            >
              View Details
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => handleRerunJob(job, e)}
              disabled={isRerunning}
              className={cn(touchButtonSizes.sm, "flex-shrink-0")}
            >
              {isRerunning ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Jobs Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          {isMobile ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className={responsivePadding.card}>
                    <div className="space-y-2">
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                      <div className="h-3 bg-muted rounded w-1/2"></div>
                      <div className="flex gap-2">
                        <div className="h-5 bg-muted rounded w-16"></div>
                        <div className="h-5 bg-muted rounded w-16"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <TableLoading rows={5} columns={7} showHeader />
          )}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <ErrorCard
        title="Failed to Load Jobs"
        message={error}
        onRetry={() => fetchJobs()}
      />
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 sm:pb-6">
        <CardTitle className="text-lg sm:text-xl">Jobs Dashboard</CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {jobs.length} job{jobs.length !== 1 ? 's' : ''}
          </Badge>
          <RefreshLoading
            isRefreshing={refreshing}
            onRefresh={() => fetchJobs(true)}
            size="sm"
          />
        </div>
      </CardHeader>
      <CardContent>
        {jobs.length === 0 ? (
          <EmptyJobs 
            onCreateJob={onCreateJob}
            className="py-8"
          />
        ) : isMobile ? (
          /* Mobile card layout */
          <div className="space-y-3">
            {jobs.map((job) => (
              <MobileJobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          /* Desktop table layout */
          <div className={responsiveTable.container}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className={responsiveTable.header}>ID</TableHead>
                  <TableHead className={responsiveTable.header}>Title</TableHead>
                  <TableHead className={responsiveTable.header}>Agent Identifier</TableHead>
                  <TableHead className={responsiveTable.header}>Status</TableHead>
                  <TableHead className={responsiveTable.header}>Created</TableHead>
                  <TableHead className={responsiveTable.header}>Updated</TableHead>
                  <TableHead className={cn(responsiveTable.header, "text-right")}>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => {
                  const isRerunning = rerunningJobs.has(job.id);
                  
                  return (
                    <TableRow key={job.id} className="hover:bg-muted/50 cursor-pointer" onClick={() => navigate(`/job/${job.id}`)}>
                      <TableCell className={cn(responsiveTable.cell, "font-mono text-xs")}>
                        {job.id.slice(0, 8)}...
                      </TableCell>
                      <TableCell className={cn(responsiveTable.cell, "font-medium")}>
                        {getTitleFromJob(job)}
                      </TableCell>
                      <TableCell className={responsiveTable.cell}>
                        {getAgentIdentifierDisplay(getAgentIdentifierFromJob(job))}
                      </TableCell>
                      <TableCell className={responsiveTable.cell}>
                        {getStatusBadge(job.status)}
                      </TableCell>
                      <TableCell className={cn(responsiveTable.cell, "text-muted-foreground")}>
                        {formatDate(job.created_at)}
                      </TableCell>
                      <TableCell className={cn(responsiveTable.cell, "text-muted-foreground")}>
                        {formatDate(job.updated_at)}
                      </TableCell>
                      <TableCell className={cn(responsiveTable.cell, "text-right")}>
                        <div className="flex gap-2 justify-end">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/job/${job.id}`);
                            }}
                            className={touchButtonSizes.sm}
                          >
                            View Details
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => handleRerunJob(job, e)}
                            disabled={isRerunning}
                            className={cn(touchButtonSizes.sm, "flex-shrink-0")}
                            title="Rerun this job with the same configuration"
                          >
                            {isRerunning ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : (
                              <RotateCcw className="h-4 w-4" />
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
        )}
      </CardContent>
    </Card>
  );
};

export default JobList; 