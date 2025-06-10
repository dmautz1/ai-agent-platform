import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, type Job, handleApiError } from '@/lib/api';
import { useSingleJobPolling } from '@/lib/polling';
import { useBreakpoint, responsivePadding, responsiveSpacing, touchButtonSizes } from '@/lib/responsive';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ResultDisplay } from '@/components/ResultDisplay';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { 
  ArrowLeft, 
  Clock, 
  CheckCircle, 
  XCircle, 
  PlayCircle, 
  RefreshCw,
  Copy,
  Download,
  Calendar,
  Settings,
  FileText,
  AlertCircle,
  Wifi,
  WifiOff,
  Pause,
  Play,
  RotateCcw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/toast';

export const JobDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isMobile } = useBreakpoint();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [isRerunning, setIsRerunning] = useState(false);
  const toast = useToast();

  // Handle job updates from polling
  const handleJobUpdate = useCallback((updatedJob: Job) => {
    setJob(updatedJob);
    setLoading(false);
    setError('');
  }, []);

  // Initialize single job polling
  const { pollingState, startPolling, stopPolling, pausePolling, resumePolling, forceUpdate } = useSingleJobPolling(
    id || '',
    handleJobUpdate,
    {
      baseInterval: 3000
    }
  );

  // Start polling when component mounts or ID changes
  useEffect(() => {
    if (!id) return;

    startPolling();
    return () => stopPolling();
  }, [id, startPolling, stopPolling]);

  // Handle polling errors
  useEffect(() => {
    if (pollingState.error) {
      setError(pollingState.error);
    }
  }, [pollingState.error]);

  const handleRefresh = async () => {
    await forceUpdate();
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

  const handleRerunJob = async () => {
    if (!job) return;
    
    setIsRerunning(true);
    
    try {
      const result = await api.jobs.rerun(job.id);
      
      toast.success(
        `Job rerun successful! New job created.`,
        {
          title: `Original: ${job.id.slice(0, 8)}... → New: ${result.new_job_id.slice(0, 8)}...`,
          action: {
            label: 'View New Job',
            onClick: () => navigate(`/job/${result.new_job_id}`)
          }
        }
      );
      
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
      setIsRerunning(false);
    }
  };

  const getStatusBadge = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="secondary" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Pending
          </Badge>
        );
      case 'running':
        return (
          <Badge variant="default" className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600">
            <PlayCircle className="h-4 w-4" />
            Running
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="default" className="flex items-center gap-2 bg-green-500 hover:bg-green-600">
            <CheckCircle className="h-4 w-4" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getAgentIdentifierDisplay = (agentIdentifier: string) => {
    if (!agentIdentifier || agentIdentifier === 'unknown') {
      return (
        <span className="text-sm text-muted-foreground font-mono">
          UNKNOWN
        </span>
      );
    }
    
    return (
      <span className="text-sm font-mono text-muted-foreground">
        {agentIdentifier.replace(/_/g, ' ').toUpperCase()}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const formatJobResult = (result: unknown): string => {
    // Result from backend is already a JSON string
    if (typeof result === 'string') {
      return result;
    }
    // Fallback for any legacy data that might be objects
    return JSON.stringify(result, null, 2);
  };

  const downloadAsJson = (data: unknown, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Mobile header component
  const MobileHeader: React.FC<{ job: Job }> = ({ job }) => {
    const agentIdentifier = job.data?.agent_identifier || 'unknown';
    const title = job.data?.title || `Job ${job.id.slice(0, 8)}`;
    const isActiveJob = job.status === 'pending' || job.status === 'running';

    return (
      <div className="sticky top-0 z-40 bg-background/95 backdrop-blur border-b">
        <div className={cn(responsivePadding.section, "py-3 sm:py-4")}>
          {/* Header row */}
          <div className="flex items-center gap-3 mb-3">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => navigate('/')}
              className={cn(touchButtonSizes.sm, "flex-shrink-0")}
            >
              <ArrowLeft className="h-4 w-4" />
              {!isMobile && <span className="ml-2">Back</span>}
            </Button>
            
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-bold truncate sm:text-xl">{title}</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                ID: {job.id.slice(0, 8)}...
              </p>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRerunJob}
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
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={pollingState.isPolling}
              className={cn(touchButtonSizes.sm, "flex-shrink-0")}
            >
              <RefreshCw className={cn("h-4 w-4", pollingState.isPolling && "animate-spin")} />
            </Button>
          </div>
          
          {/* Status and badges */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              {getAgentIdentifierDisplay(agentIdentifier)}
              {getStatusBadge(job.status)}
            </div>
            
            {/* Connection status with pause/start control */}
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              {pollingState.error ? (
                <WifiOff className="h-3 w-3 text-red-500" />
              ) : pollingState.isPaused ? (
                <Pause className="h-3 w-3 text-orange-500" />
              ) : isActiveJob ? (
                <Wifi className="h-3 w-3 text-green-500" />
              ) : (
                <Wifi className="h-3 w-3 text-gray-400" />
              )}
              {pollingState.isPolling && !pollingState.isPaused && (
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              )}
              
              {/* Pause/Start button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleTogglePolling}
                className="h-5 w-5 p-0 text-muted-foreground hover:text-foreground ml-1"
                title={pollingState.isPaused ? "Start auto-refresh" : "Pause auto-refresh"}
              >
                {pollingState.isPaused ? (
                  <Play className="h-3 w-3" />
                ) : (
                  <Pause className="h-3 w-3" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className={cn(responsivePadding.page, "space-y-6")}>
          {/* Header Skeleton */}
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-20 sm:w-32" />
            <Skeleton className="h-8 w-8 sm:h-10 sm:w-24" />
          </div>
          
          {/* Main Content Skeleton */}
          <div className="grid gap-4 sm:gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-24 sm:h-6 sm:w-32" />
              </CardHeader>
              <CardContent className="space-y-3 sm:space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-24 sm:h-6 sm:w-32" />
              </CardHeader>
              <CardContent className="space-y-3 sm:space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className={cn(responsivePadding.page, "space-y-6")}>
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} className={touchButtonSizes.default}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
          
          <Card>
            <CardContent className={responsivePadding.card}>
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <span>{error}</span>
                  <Button variant="outline" size="sm" onClick={handleRefresh} className={touchButtonSizes.sm}>
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className={cn(responsivePadding.page, "space-y-6")}>
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/')} className={touchButtonSizes.default}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </div>
          
          <Card>
            <CardContent className={responsivePadding.card}>
              <p className="text-center text-muted-foreground">Job not found</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const agentIdentifier = job.data?.agent_identifier || 'unknown';
  const title = job.data?.title || `Job ${job.id.slice(0, 8)}`;
  const isActiveJob = job.status === 'pending' || job.status === 'running';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {isMobile ? <MobileHeader job={job} /> : null}
      
      <div className={cn(responsivePadding.page, responsiveSpacing.component)}>
        {/* Desktop Header */}
        {!isMobile && (
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={() => navigate('/')} className={touchButtonSizes.default}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-2xl font-bold">{title}</h1>
                <p className="text-sm text-muted-foreground">
                  ID: {job.id.slice(0, 8)}... | {getAgentIdentifierDisplay(agentIdentifier)}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <ThemeSwitcher />
              
              <Button
                variant="outline"
                onClick={handleRerunJob}
                disabled={isRerunning}
                className={touchButtonSizes.default}
                title="Rerun this job with the same configuration"
              >
                {isRerunning ? (
                  <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <RotateCcw className="h-4 w-4 mr-2" />
                )}
                Rerun Job
              </Button>
              
              <Button
                variant="outline"
                onClick={handleRefresh}
                disabled={pollingState.isPolling}
                className={touchButtonSizes.default}
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", pollingState.isPolling && "animate-spin")} />
                Refresh
              </Button>
            </div>
          </div>
        )}

        {/* Connection error alert (when job data is available but polling failed) */}
        {pollingState.error && job && (
          <Alert variant="destructive" className="mb-6">
            <WifiOff className="h-4 w-4" />
            <AlertDescription className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <span>Live updates temporarily unavailable: {pollingState.error}</span>
              <Button variant="outline" size="sm" onClick={handleRefresh} className={touchButtonSizes.sm}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content - Responsive Grid */}
        <div className="grid gap-4 sm:gap-6 lg:grid-cols-2">
          {/* Job Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Job Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Agent Identifier:</span>
                  {getAgentIdentifierDisplay(agentIdentifier)}
                </div>
                
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Status:</span>
                  {getStatusBadge(job.status)}
                </div>
                
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Created:</span>
                  <span className="text-sm flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(job.created_at)}
                  </span>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Updated:</span>
                  <span className="text-sm flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(job.updated_at)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Input Data */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Input Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <span className="text-sm font-medium text-muted-foreground">Data:</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(JSON.stringify(job.data, null, 2))}
                    className={touchButtonSizes.sm}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto max-h-48 text-wrap break-all">
                  {JSON.stringify(job.data, null, 2)}
                </pre>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadAsJson(job.data, `job-${job.id}-input.json`)}
                  className={cn("w-full", touchButtonSizes.sm)}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download Input Data
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        {job.status === 'completed' && job.result && (
          <Card className="mt-4 sm:mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Results
              </CardTitle>
              <CardDescription>
                Job completed successfully
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <span className="text-sm font-medium text-muted-foreground">Output:</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(formatJobResult(job.result))}
                    className={touchButtonSizes.sm}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
                
                <ResultDisplay 
                  result={formatJobResult(job.result)} 
                  result_format={job.result_format}
                />
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadAsJson({ result: job.result }, `job-${job.id}-result.json`)}
                  className={cn("w-full", touchButtonSizes.sm)}
                >
                  <Download className="h-3 w-3 mr-2" />
                  Download Results
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error Section */}
        {job.status === 'failed' && job.error_message && (
          <Card className="mt-4 sm:mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                Error Details
              </CardTitle>
              <CardDescription>
                Job failed with the following error
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <ResultDisplay 
                    result={formatJobResult(job.error_message)} 
                  />
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        )}

        {/* Running/Pending Status */}
        {isActiveJob && (
          <Card className="mt-4 sm:mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PlayCircle className="h-5 w-5 text-blue-500" />
                Job Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">
                  {job.status === 'running' ? 'Job is currently running...' : 'Job is pending execution...'}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  This page will automatically refresh with live updates
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default JobDetails; 