import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { api, handleApiError } from '@/lib/api';
import type { AgentInfo } from '@/lib/types';
import { getResponsiveGrid, responsivePadding } from '@/lib/responsive';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Search, Filter, X, RefreshCw, Wifi, WifiOff, Zap, Globe, Database, Users } from 'lucide-react';
import { RefreshLoading } from '@/components/ui/loading';
import { EmptyState } from '@/components/ui/empty-state';
import { AgentCard } from '@/components/AgentCard';
import { cn } from '@/lib/utils';

interface AgentDirectoryProps {
  /** Pre-fetched agents data */
  agents?: AgentInfo[];
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Refresh function */
  onRefresh?: () => void | Promise<void>;
  /** Whether a refresh is currently in progress */
  isRefreshing?: boolean;
  /** Filter by environment (deprecated - use showEnvironmentFilter) */
  environmentFilter?: string;
  /** Filter by lifecycle state (deprecated - use showStateFilter) */
  stateFilter?: string;
  /** Agent selection callback */
  onSelectAgent?: (agent: AgentInfo) => void;
  /** Whether this is a selection mode (for job creation) */
  selectionMode?: boolean;
  /** Whether to show environment filter (typically only in dev/test) */
  showEnvironmentFilter?: boolean;
  /** Whether to show lifecycle state filter */
  showStateFilter?: boolean;
  /** Whether to show the search and filter controls */
  showFilters?: boolean;
}

// Enhanced loading states for better UX
interface DirectoryLoadingState {
  isLoading: boolean;
  stage: 'connecting' | 'fetching' | 'processing' | 'ready';
  progress: number;
  message: string;
  hasError: boolean;
  canRetry: boolean;
  retryCount: number;
  isNetworkError: boolean;
  lastFetchTime?: Date;
}

// Error categorization for better recovery
interface DirectoryError {
  type: 'network' | 'server' | 'timeout' | 'parsing' | 'auth' | 'unknown';
  message: string;
  canRetry: boolean;
  suggestedAction?: string;
  details?: unknown;
}

// Enhanced agent card skeleton component
const AgentCardSkeleton: React.FC<{ index: number }> = ({ index }) => (
  <Card className="h-64 animate-pulse" style={{ animationDelay: `${index * 100}ms` }}>
    <CardContent className={responsivePadding.card}>
      <div className="space-y-3">
        <div className="h-4 bg-muted rounded w-3/4"></div>
        <div className="h-3 bg-muted rounded w-1/2"></div>
        <div className="space-y-2">
          <div className="h-3 bg-muted rounded"></div>
          <div className="h-3 bg-muted rounded w-5/6"></div>
          <div className="h-3 bg-muted rounded w-4/5"></div>
        </div>
        <div className="flex gap-2">
          <div className="h-5 bg-muted rounded w-16"></div>
          <div className="h-5 bg-muted rounded w-16"></div>
          <div className="h-5 bg-muted rounded w-12"></div>
        </div>
        <div className="flex justify-between items-center">
          <div className="h-4 bg-muted rounded w-16"></div>
          <div className="h-6 bg-muted rounded w-20"></div>
        </div>
      </div>
    </CardContent>
  </Card>
);

// Enhanced loading progress component
const DirectoryLoadingProgress: React.FC<{
  loadingState: DirectoryLoadingState;
  onRetry?: () => void;
  totalExpected?: number;
}> = ({ loadingState, onRetry, totalExpected = 6 }) => {
  const toast = useToast();

  const getStageIcon = () => {
    switch (loadingState.stage) {
      case 'connecting':
        return <Wifi className="h-4 w-4 animate-pulse" />;
      case 'fetching':
        return <Database className="h-4 w-4 animate-spin" />;
      case 'processing':
        return <Zap className="h-4 w-4 animate-pulse" />;
      default:
        return <CheckCircle className="h-4 w-4" />;
    }
  };

  const getStageDescription = () => {
    switch (loadingState.stage) {
      case 'connecting':
        return 'Establishing connection to agent registry...';
      case 'fetching':
        return 'Retrieving available agents...';
      case 'processing':
        return 'Processing agent metadata and capabilities...';
      default:
        return 'Loading complete';
    }
  };

  // Error state rendering
  if (loadingState.hasError) {
    const getErrorIcon = () => {
      if (loadingState.isNetworkError) {
        return <WifiOff className="h-4 w-4" />;
      }
      return <AlertCircle className="h-4 w-4" />;
    };

    const getErrorColor = () => {
      if (loadingState.isNetworkError) {
        return 'border-orange-200 bg-orange-50';
      }
      return 'border-red-200 bg-red-50';
    };

    return (
      <div className="space-y-4">
        <Alert variant={loadingState.isNetworkError ? 'default' : 'destructive'} 
               className={cn(loadingState.isNetworkError && getErrorColor())}>
          {getErrorIcon()}
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">
                {loadingState.isNetworkError ? 'Connection Issue' : 'Failed to Load Agent Directory'}
              </p>
              <p className="text-sm">{loadingState.message}</p>
              {loadingState.retryCount > 0 && (
                <p className="text-xs text-muted-foreground">
                  {loadingState.retryCount === 1 
                    ? `Attempted ${loadingState.retryCount} retry` 
                    : `Attempted ${loadingState.retryCount} retries`}
                </p>
              )}
              {loadingState.isNetworkError && (
                <p className="text-xs text-muted-foreground">
                  💡 Check your internet connection and try again
                </p>
              )}
            </div>
          </AlertDescription>
        </Alert>

        {loadingState.canRetry && onRetry && (
          <div className="flex gap-2">
            <Button
              variant={loadingState.isNetworkError ? 'default' : 'outline'}
              onClick={onRetry}
              className="flex-1"
              disabled={loadingState.isLoading}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", loadingState.isLoading && "animate-spin")} />
              {loadingState.isLoading ? 'Retrying...' : 
               loadingState.retryCount >= 2 ? 'Try Again' : 'Retry'}
            </Button>
            {loadingState.isNetworkError && (
              <Button
                variant="outline"
                onClick={() => {
                  toast.info('Checking connection status...');
                  // Simple network check
                  if (navigator.onLine) {
                    toast.success('Network appears to be available');
                  } else {
                    toast.error('No network connection detected');
                  }
                }}
                disabled={loadingState.isLoading}
              >
                <Globe className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
      </div>
    );
  }

  // Loading progress rendering
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {getStageIcon()}
        <div className="flex-1">
          <p className="text-sm font-medium">{loadingState.message}</p>
          <p className="text-xs text-muted-foreground">{getStageDescription()}</p>
          {loadingState.lastFetchTime && (
            <p className="text-xs text-muted-foreground">
              Last updated: {loadingState.lastFetchTime.toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Discovery Progress</span>
          <span>{Math.round(loadingState.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${loadingState.progress}%` }}
          />
        </div>
      </div>

      {/* Agent skeleton grid */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Users className="h-3 w-3" />
          <span>Discovering available agents...</span>
        </div>
        <div className={getResponsiveGrid({ sm: 1, md: 2, lg: 3, xl: 4 }, 4)}>
          {[...Array(totalExpected)].map((_, i) => (
            <AgentCardSkeleton key={i} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
};

// Parse and categorize API errors
const parseDirectoryError = (error: unknown): DirectoryError => {
  const errorMessage = handleApiError(error);
  const lowerMessage = errorMessage.toLowerCase();

  if (lowerMessage.includes('network') || lowerMessage.includes('connection') || 
      lowerMessage.includes('timeout') || lowerMessage.includes('fetch')) {
    return {
      type: 'network',
      message: errorMessage,
      canRetry: true,
      suggestedAction: 'Check your internet connection and try again'
    };
  }

  if (lowerMessage.includes('unauthorized') || lowerMessage.includes('forbidden')) {
    return {
      type: 'auth',
      message: errorMessage,
      canRetry: false,
      suggestedAction: 'Please check your authentication credentials'
    };
  }

  if (lowerMessage.includes('server') || lowerMessage.includes('500') || lowerMessage.includes('503')) {
    return {
      type: 'server',
      message: errorMessage,
      canRetry: true,
      suggestedAction: 'The server is temporarily unavailable. Please try again in a moment.'
    };
  }

  if (lowerMessage.includes('timeout')) {
    return {
      type: 'timeout',
      message: errorMessage,
      canRetry: true,
      suggestedAction: 'The request timed out. Please try again.'
    };
  }

  if (lowerMessage.includes('parse') || lowerMessage.includes('json')) {
    return {
      type: 'parsing',
      message: errorMessage,
      canRetry: true,
      suggestedAction: 'There was an issue processing the response. Please try again.'
    };
  }

  return {
    type: 'unknown',
    message: errorMessage,
    canRetry: true,
    suggestedAction: 'An unexpected error occurred. Please try again.'
  };
};

export const AgentDirectory: React.FC<AgentDirectoryProps> = ({
  agents: externalAgents,
  loading: externalLoading,
  error: externalError,
  onRefresh,
  isRefreshing: externalRefreshing,
  environmentFilter,
  stateFilter,
  onSelectAgent,
  selectionMode = false,
  showEnvironmentFilter,
  showStateFilter,
  showFilters = true
}) => {
  const toast = useToast();
  const [internalAgents, setInternalAgents] = useState<AgentInfo[]>([]);
  const [internalLoading, setInternalLoading] = useState(true);
  const [internalError, setInternalError] = useState<string>('');
  const [internalRefreshing, setInternalRefreshing] = useState(false);

  // Enhanced loading state management
  const [loadingState, setLoadingState] = useState<DirectoryLoadingState>({
    isLoading: true,
    stage: 'connecting',
    progress: 0,
    message: 'Initializing agent discovery...',
    hasError: false,
    canRetry: false,
    retryCount: 0,
    isNetworkError: false
  });

  // Internal filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>(environmentFilter || 'all');
  const [selectedState, setSelectedState] = useState<string>(stateFilter || 'all');

  // Use external data if provided, otherwise fall back to internal management
  const agents = externalAgents ?? internalAgents;
  const loading = externalLoading ?? internalLoading;
  const error = externalError ?? internalError;
  const refreshing = externalRefreshing ?? internalRefreshing;

  // Enhanced fetch function with comprehensive loading states
  const fetchAgents = useCallback(async (isRetry = false) => {
    // If external data management is provided, use the external refresh function
    if (externalAgents && onRefresh) {
      await onRefresh();
      return;
    }

    try {
      // Update retry count if this is a retry
      if (isRetry) {
        setLoadingState(prev => ({ 
          ...prev, 
          retryCount: prev.retryCount + 1,
          isLoading: true,
          hasError: false,
          canRetry: false
        }));
      } else {
        setLoadingState(prev => ({
          ...prev,
          isLoading: true,
          stage: 'connecting',
          progress: 0,
          message: 'Connecting to agent registry...',
          hasError: false,
          canRetry: false,
          retryCount: 0,
          isNetworkError: false
        }));
      }

      if (isRetry) {
        setInternalRefreshing(true);
      } else {
        setInternalLoading(true);
      }
      setInternalError('');

      // Simulate realistic connection time
      await new Promise(resolve => setTimeout(resolve, 300));

      // Stage 2: Fetching
      setLoadingState(prev => ({
        ...prev,
        stage: 'fetching',
        progress: 25,
        message: 'Retrieving agent information...'
      }));

      await new Promise(resolve => setTimeout(resolve, 200));

      const agentsData = await api.agents.getAll();

      // Stage 3: Processing
      setLoadingState(prev => ({
        ...prev,
        stage: 'processing',
        progress: 75,
        message: 'Processing agent metadata...'
      }));

      await new Promise(resolve => setTimeout(resolve, 300));

      // Success
      setLoadingState(prev => ({
        ...prev,
        stage: 'ready',
        progress: 100,
        message: `Successfully loaded ${agentsData.length} agent${agentsData.length !== 1 ? 's' : ''}`,
        isLoading: false,
        hasError: false,
        lastFetchTime: new Date(),
        retryCount: 0
      }));

      setInternalAgents(agentsData);
      
      // Show success toast for retries
      if (isRetry) {
        toast.success(`Successfully loaded ${agentsData.length} agents`);
      }

    } catch (err: unknown) {
      const parsedError = parseDirectoryError(err);
      
      setLoadingState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        message: parsedError.message,
        canRetry: parsedError.canRetry && prev.retryCount < 3,
        isNetworkError: parsedError.type === 'network' || parsedError.type === 'timeout',
        progress: 0
      }));

      setInternalError(parsedError.message);

      // Show appropriate toast messages
      if (parsedError.type === 'network') {
        if (!isRetry) {
          toast.error('Connection failed. Please check your network.');
        }
      } else if (parsedError.type === 'server') {
        toast.error('Server temporarily unavailable. Will retry automatically.');
        // Note: Auto-retry will be handled by external retry logic if needed
      } else if (!isRetry) {
        toast.error('Failed to load agents. Please try again.');
      }

    } finally {
      setInternalLoading(false);
      setInternalRefreshing(false);
    }
  }, [externalAgents, onRefresh, toast]);

  // Store fetchAgents in a ref to break circular dependency
  const fetchAgentsRef = useRef(fetchAgents);
  fetchAgentsRef.current = fetchAgents;

  // Stable fetch function that doesn't change
  const stableFetchAgents = useCallback(() => {
    fetchAgentsRef.current();
  }, []);

  useEffect(() => {
    // Only set up internal data fetching if no external data is provided
    if (externalAgents) return;

    stableFetchAgents();
  }, [externalAgents, stableFetchAgents]);

  // Get available filter options from agents data
  const availableEnvironments = useMemo(() => {
    const environments = new Set<string>();
    agents.forEach(agent => {
      agent.supported_environments?.forEach(env => environments.add(env));
    });
    return Array.from(environments).sort();
  }, [agents]);

  const availableStates = useMemo(() => {
    const states = new Set<string>();
    agents.forEach(agent => {
      if (agent.lifecycle_state) {
        states.add(agent.lifecycle_state);
      }
    });
    return Array.from(states).sort();
  }, [agents]);

  // Comprehensive filtering logic
  const filteredAgents = useMemo(() => {
    return agents.filter(agent => {
      // Search by name, identifier, or description
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = 
          agent.name.toLowerCase().includes(query) ||
          agent.identifier.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }

      // Filter by environment (typically for dev/test)
      if (selectedEnvironment !== 'all') {
        if (!agent.supported_environments?.includes(selectedEnvironment)) {
          return false;
        }
      }

      // Filter by lifecycle state
      if (selectedState !== 'all') {
        if (agent.lifecycle_state !== selectedState) {
          return false;
        }
      }

      return true;
    });
  }, [agents, searchQuery, selectedEnvironment, selectedState]);

  // Check if any filters are active
  const hasActiveFilters = 
    searchQuery.trim() !== '' || 
    selectedEnvironment !== 'all' || 
    selectedState !== 'all';

  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedEnvironment('all');
    setSelectedState('all');
  };

  // Enhanced retry function
  const handleRetry = () => {
    fetchAgents(true);
  };

  // Grid configuration based on screen size
  const gridColumns = {
    sm: 1,
    md: 2,
    lg: 3,
    xl: 4
  };

  // Enhanced loading state
  if (loading && loadingState.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">
            {selectionMode ? 'Select Agent' : 'Agent Directory'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DirectoryLoadingProgress 
            loadingState={loadingState}
            onRetry={handleRetry}
            totalExpected={6}
          />
        </CardContent>
      </Card>
    );
  }

  // Enhanced error state
  if (error && loadingState.hasError) {
    const parsedError = parseDirectoryError(error);
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">
            {selectionMode ? 'Select Agent' : 'Agent Directory'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert variant={parsedError.type === 'network' ? 'default' : 'destructive'}
                   className={cn(parsedError.type === 'network' && 'border-orange-200 bg-orange-50')}>
              {parsedError.type === 'network' ? (
                <WifiOff className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Failed to Load Agent Directory</p>
                  <p className="text-sm">{parsedError.message}</p>
                  {parsedError.suggestedAction && (
                    <p className="text-xs text-muted-foreground">
                      💡 {parsedError.suggestedAction}
                    </p>
                  )}
                  {loadingState.retryCount > 0 && (
                    <p className="text-xs text-muted-foreground">
                      Retry attempts: {loadingState.retryCount}/3
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>

            {loadingState.canRetry && (
              <div className="flex gap-2">
                <Button
                  variant={parsedError.type === 'network' ? 'default' : 'outline'}
                  onClick={handleRetry}
                  className="flex-1"
                  disabled={loadingState.isLoading}
                >
                  <RefreshCw className={cn("mr-2 h-4 w-4", loadingState.isLoading && "animate-spin")} />
                  {loadingState.isLoading ? 'Retrying...' : 'Retry Loading'}
                </Button>
                {parsedError.type === 'network' && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      toast.info('Checking connection status...');
                      // Simple network check
                      if (navigator.onLine) {
                        toast.success('Network appears to be available');
                      } else {
                        toast.error('No network connection detected');
                      }
                    }}
                  >
                    <Globe className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="space-y-4">
        <div className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-lg sm:text-xl">
            {selectionMode ? 'Select Agent' : 'Agent Directory'}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
              {hasActiveFilters && (
                <span className="ml-1 text-muted-foreground">
                  of {agents.length}
                </span>
              )}
            </Badge>
            <RefreshLoading
              isRefreshing={refreshing}
              onRefresh={() => fetchAgents(true)}
              size="sm"
            />
          </div>
        </div>

        {showFilters && (
          <div className="space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search agents by name, identifier, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filter Controls */}
            <div className="flex flex-wrap gap-3 items-center">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Filter className="h-4 w-4" />
                <span>Filters:</span>
              </div>

              {/* Environment Filter (dev/test only) */}
              {(showEnvironmentFilter || availableEnvironments.length > 1) && (
                <div className="min-w-[120px]">
                  <Select value={selectedEnvironment} onValueChange={setSelectedEnvironment}>
                    <SelectTrigger className="h-8">
                      <SelectValue placeholder="Environment" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Environments</SelectItem>
                      {availableEnvironments.map((env) => (
                        <SelectItem key={env} value={env}>
                          {env.charAt(0).toUpperCase() + env.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* State Filter */}
              {(showStateFilter || availableStates.length > 1) && (
                <div className="min-w-[100px]">
                  <Select value={selectedState} onValueChange={setSelectedState}>
                    <SelectTrigger className="h-8">
                      <SelectValue placeholder="State" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All States</SelectItem>
                      {availableStates.map((state) => (
                        <SelectItem key={state} value={state}>
                          {state.charAt(0).toUpperCase() + state.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Clear Filters Button */}
              {hasActiveFilters && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllFilters}
                  className="h-8 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {filteredAgents.length === 0 ? (
          <EmptyState
            title={hasActiveFilters ? "No agents match your filters" : "No Agents Available"}
            description={
              hasActiveFilters
                ? "Try adjusting your search criteria or clearing filters."
                : agents.length > 0 
                  ? "No agents match the current filters." 
                  : "No agents are currently registered in the system."
            }
            className="py-8"
            action={hasActiveFilters ? {
              label: "Clear Filters",
              onClick: clearAllFilters,
              variant: "outline" as const
            } : undefined}
          />
        ) : (
          <div className={getResponsiveGrid(gridColumns, 4)}>
            {filteredAgents.map((agent) => (
              <AgentCard 
                key={agent.identifier} 
                agent={agent} 
                selectionMode={selectionMode}
                onSelect={onSelectAgent}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AgentDirectory; 