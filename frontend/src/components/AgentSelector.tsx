import React, { useState, useEffect, useMemo } from 'react';
import { api, handleApiError } from '@/lib/api';
import type { AgentInfo } from '@/lib/models';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle, Clock, Search, Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentSelectorProps {
  /** Callback when an agent is selected */
  onAgentSelected: (agentId: string) => void;
  /** Callback to open the full agent directory browser */
  onBrowseAll?: () => void;
  /** Show the browse all agents button */
  showBrowseButton?: boolean;
  /** Pre-fetched agents data */
  agents?: AgentInfo[];
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Recently used agent IDs (will be shown first) */
  recentAgents?: string[];
  /** Favorite agent IDs (will be shown with star) */
  favoriteAgents?: string[];
  /** Disabled state */
  disabled?: boolean;
  /** Custom placeholder text */
  placeholder?: string;
}

// Helper function to get agent status icon and color
const getAgentStatusInfo = (agent: AgentInfo) => {
  if (agent.has_error) {
    return {
      icon: <XCircle className="h-3 w-3" />,
      color: 'text-red-500',
      badge: 'destructive' as const,
      text: 'Error'
    };
  }
  
  if (!agent.enabled) {
    return {
      icon: <AlertCircle className="h-3 w-3" />,
      color: 'text-yellow-500',
      badge: 'secondary' as const,
      text: 'Disabled'
    };
  }
  
  if (agent.lifecycle_state === 'loading') {
    return {
      icon: <Clock className="h-3 w-3" />,
      color: 'text-blue-500',
      badge: 'secondary' as const,
      text: 'Loading'
    };
  }
  
  return {
    icon: <CheckCircle className="h-3 w-3" />,
    color: 'text-green-500',
    badge: 'secondary' as const,
    text: 'Ready'
  };
};

// Custom SelectItem for agents with status and metadata
const AgentSelectItem: React.FC<{
  agent: AgentInfo;
  isRecent?: boolean;
  isFavorite?: boolean;
}> = ({ agent, isRecent = false, isFavorite = false }) => {
  const statusInfo = getAgentStatusInfo(agent);
  
  return (
    <SelectItem 
      value={agent.identifier} 
      className="py-3"
      disabled={agent.has_error || !agent.enabled}
    >
      <div className="flex items-start justify-between w-full gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium truncate">{agent.name}</span>
            {isFavorite && <Star className="h-3 w-3 text-yellow-500 fill-current flex-shrink-0" />}
            {isRecent && !isFavorite && <Clock className="h-3 w-3 text-blue-500 flex-shrink-0" />}
          </div>
          
          <div className="flex items-center gap-2">
            <div className={cn("flex items-center gap-1", statusInfo.color)}>
              {statusInfo.icon}
              <span className="text-xs">{statusInfo.text}</span>
            </div>
          </div>
          
          {agent.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {agent.description}
            </p>
          )}
        </div>
      </div>
    </SelectItem>
  );
};

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  onAgentSelected,
  onBrowseAll,
  showBrowseButton = true,
  agents: externalAgents,
  loading: externalLoading,
  error: externalError,
  recentAgents = [],
  favoriteAgents = [],
  disabled = false,
  placeholder = "Select an agent..."
}) => {
  const [internalAgents, setInternalAgents] = useState<AgentInfo[]>([]);
  const [internalLoading, setInternalLoading] = useState(true);
  const [internalError, setInternalError] = useState<string>('');

  // Use external data if provided, otherwise fall back to internal management
  const agents = externalAgents ?? internalAgents;
  const loading = externalLoading ?? internalLoading;
  const error = externalError ?? internalError;

  // Fetch agents if not provided externally
  useEffect(() => {
    if (externalAgents) return;

    const fetchAgents = async () => {
      try {
        setInternalLoading(true);
        setInternalError('');
        const agentsData = await api.agents.getAll();
        setInternalAgents(agentsData);
      } catch (err: unknown) {
        setInternalError(handleApiError(err));
      } finally {
        setInternalLoading(false);
      }
    };

    fetchAgents();
  }, [externalAgents]);

  // Sort agents: favorites first, then recent, then alphabetical
  const sortedAgents = useMemo(() => {
    return [...agents].sort((a, b) => {
      // Favorites first
      const aIsFavorite = favoriteAgents.includes(a.identifier);
      const bIsFavorite = favoriteAgents.includes(b.identifier);
      if (aIsFavorite && !bIsFavorite) return -1;
      if (!aIsFavorite && bIsFavorite) return 1;

      // Then recent (among non-favorites)
      if (!aIsFavorite && !bIsFavorite) {
        const aIsRecent = recentAgents.includes(a.identifier);
        const bIsRecent = recentAgents.includes(b.identifier);
        if (aIsRecent && !bIsRecent) return -1;
        if (!aIsRecent && bIsRecent) return 1;
        
        // Within recent, sort by recency order
        if (aIsRecent && bIsRecent) {
          return recentAgents.indexOf(a.identifier) - recentAgents.indexOf(b.identifier);
        }
      }

      // Finally alphabetical
      return a.name.localeCompare(b.name);
    });
  }, [agents, recentAgents, favoriteAgents]);

  // Filter out agents that are available (not in error state)
  const availableAgents = useMemo(() => {
    return sortedAgents.filter(agent => !agent.has_error && agent.enabled);
  }, [sortedAgents]);

  // Get section headers
  const getSectionHeader = (index: number, agent: AgentInfo) => {
    const isFavorite = favoriteAgents.includes(agent.identifier);
    const isRecent = recentAgents.includes(agent.identifier);
    
    // Check if this is the first item in a section
    const prevAgent = sortedAgents[index - 1];
    if (!prevAgent) {
      if (isFavorite) return "Favorites";
      if (isRecent) return "Recently Used";
      return "All Agents";
    }
    
    const prevIsFavorite = favoriteAgents.includes(prevAgent.identifier);
    const prevIsRecent = recentAgents.includes(prevAgent.identifier);
    
    // Section transitions
    if (isFavorite && !prevIsFavorite) return "Favorites";
    if (isRecent && !prevIsRecent && !isFavorite) return "Recently Used";
    if (!isFavorite && !isRecent && (prevIsFavorite || prevIsRecent)) return "All Agents";
    
    return null;
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <Select disabled>
          <SelectTrigger>
            <SelectValue placeholder="Loading agents..." />
          </SelectTrigger>
        </Select>
        {showBrowseButton && (
          <Button 
            variant="outline" 
            size="sm" 
            disabled 
            className="w-full"
          >
            <Search className="h-4 w-4 mr-2" />
            Browse All Agents
          </Button>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <div className="text-sm text-red-500 p-3 bg-red-50 rounded-md border border-red-200">
          Failed to load agents: {error}
        </div>
        {showBrowseButton && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onBrowseAll}
            className="w-full"
          >
            <Search className="h-4 w-4 mr-2" />
            Browse All Agents
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Select 
        onValueChange={onAgentSelected}
        disabled={disabled || availableAgents.length === 0}
      >
        <SelectTrigger>
          <SelectValue placeholder={
            availableAgents.length === 0 
              ? "No agents available" 
              : placeholder
          } />
        </SelectTrigger>
        <SelectContent className="max-h-80">
          {sortedAgents.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No agents found
            </div>
          ) : (
            sortedAgents.map((agent, index) => {
              const sectionHeader = getSectionHeader(index, agent);
              const isFavorite = favoriteAgents.includes(agent.identifier);
              const isRecent = recentAgents.includes(agent.identifier);
              
              return (
                <React.Fragment key={agent.identifier}>
                  {sectionHeader && (
                    <div className="px-2 py-1 text-xs font-semibold text-muted-foreground border-b">
                      {sectionHeader}
                    </div>
                  )}
                  <AgentSelectItem 
                    agent={agent}
                    isFavorite={isFavorite}
                    isRecent={isRecent && !isFavorite}
                  />
                </React.Fragment>
              );
            })
          )}
        </SelectContent>
      </Select>
      
      {showBrowseButton && (
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onBrowseAll}
          className="w-full"
          disabled={disabled}
        >
          <Search className="h-4 w-4 mr-2" />
          Browse All Agents
        </Button>
      )}
      
      {/* Status summary */}
      {agents.length > 0 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{availableAgents.length} of {agents.length} agents available</span>
          {agents.length - availableAgents.length > 0 && (
            <Badge variant="secondary" className="text-xs">
              {agents.length - availableAgents.length} unavailable
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}; 