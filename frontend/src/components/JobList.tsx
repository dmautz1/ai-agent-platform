import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, handleApiError, type Job } from '@/lib/api';
import { useBreakpoint, responsiveTable, responsivePadding, touchButtonSizes } from '@/lib/responsive';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Clock, CheckCircle, XCircle, PlayCircle, ChevronRight } from 'lucide-react';
import { TableLoading, RefreshLoading } from '@/components/ui/loading';
import { ErrorCard } from '@/components/ui/error';
import { EmptyJobs } from '@/components/ui/empty-state';
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
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();

  // Use external data if provided, otherwise fall back to internal management
  const jobs = externalJobs ?? internalJobs;
  const loading = externalLoading ?? internalLoading;
  const error = externalError ?? internalError;
  const refreshing = externalRefreshing ?? internalRefreshing;

  const fetchJobs = async (isRefresh = false) => {
    // If external data management is provided, use the external refresh function
    if (externalJobs && onRefresh) {
      await onRefresh();
      return;
    }

    // Fall back to internal data management
    try {
      if (isRefresh) {
        setInternalRefreshing(true);
      } else {
        setInternalLoading(true);
      }
      setInternalError('');

      const jobsData = await api.jobs.getAll();
      setInternalJobs(jobsData);
    } catch (err: any) {
      setInternalError(handleApiError(err));
    } finally {
      setInternalLoading(false);
      setInternalRefreshing(false);
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
  }, [refreshInterval, externalJobs]);

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

  const getAgentTypeFromJob = (job: Job): string => {
    return job.data?.agent_type || 'unknown';
  };

  const getTitleFromJob = (job: Job): string => {
    return job.data?.title || `Job ${job.id.slice(0, 8)}`;
  };

  const getAgentTypeBadge = (agentType: string) => {
    const colors = {
      'text_processing': 'bg-purple-500 hover:bg-purple-600',
      'summarization': 'bg-orange-500 hover:bg-orange-600',
      'web_scraping': 'bg-teal-500 hover:bg-teal-600',
    };
    
    const colorClass = colors[agentType as keyof typeof colors] || 'bg-gray-500 hover:bg-gray-600';
    
    return (
      <Badge variant="default" className={`${colorClass} text-white text-xs`}>
        {agentType.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  // Mobile card component for each job
  const MobileJobCard: React.FC<{ job: Job }> = ({ job }) => (
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
          {getAgentTypeBadge(getAgentTypeFromJob(job))}
          {getStatusBadge(job.status)}
        </div>
        
        {/* Dates */}
        <div className="space-y-1 text-xs text-muted-foreground">
          <div>Created: {formatDate(job.created_at, true)}</div>
          <div>Updated: {formatDate(job.updated_at, true)}</div>
        </div>
      </CardContent>
    </Card>
  );

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
                  <TableHead className={responsiveTable.header}>Agent Type</TableHead>
                  <TableHead className={responsiveTable.header}>Status</TableHead>
                  <TableHead className={responsiveTable.header}>Created</TableHead>
                  <TableHead className={responsiveTable.header}>Updated</TableHead>
                  <TableHead className={cn(responsiveTable.header, "text-right")}>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id} className="hover:bg-muted/50 cursor-pointer" onClick={() => navigate(`/job/${job.id}`)}>
                    <TableCell className={cn(responsiveTable.cell, "font-mono text-xs")}>
                      {job.id.slice(0, 8)}...
                    </TableCell>
                    <TableCell className={cn(responsiveTable.cell, "font-medium")}>
                      {getTitleFromJob(job)}
                    </TableCell>
                    <TableCell className={responsiveTable.cell}>
                      {getAgentTypeBadge(getAgentTypeFromJob(job))}
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
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default JobList; 