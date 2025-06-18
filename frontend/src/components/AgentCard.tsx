import React from 'react';
import type { AgentInfo } from '@/lib/types';
import { useBreakpoint } from '@/lib/responsive';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, AlertCircle, Clock, Calendar, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  /** Agent information to display */
  agent: AgentInfo;
  /** Whether this card is in selection mode (for job creation) */
  selectionMode?: boolean;
  /** Whether to show additional details like creation date */
  showExtendedDetails?: boolean;
  /** Whether to show a compact view with less information */
  compact?: boolean;
  /** Custom CSS classes */
  className?: string;
  /** Agent selection callback */
  onSelect?: (agent: AgentInfo) => void;
  /** Agent configuration callback */
  onConfigure?: (agent: AgentInfo) => void;
  /** Show configuration button */
  showConfigButton?: boolean;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  agent, 
  selectionMode = false, 
  showExtendedDetails = false,
  compact = false,
  className,
  onSelect,
  onConfigure,
  showConfigButton = false
}) => {
  const { isMobile } = useBreakpoint();

  const isAgentAvailable = (agent: AgentInfo): boolean => {
    return agent.lifecycle_state === 'enabled' && agent.status === 'available' && !agent.has_error;
  };

  const getStatusInfo = (agent: AgentInfo) => {
    if (!isAgentAvailable(agent)) {
      if (agent.has_error) {
        return {
          icon: <XCircle className="h-4 w-4" />,
          badge: { variant: 'destructive' as const, text: 'Error' },
          className: 'text-red-500'
        };
      }
      if (agent.lifecycle_state !== 'enabled') {
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          badge: { variant: 'secondary' as const, text: 'Disabled' },
          className: 'text-yellow-500'
        };
      }
      if (agent.status !== 'available') {
        return {
          icon: <Clock className="h-4 w-4" />,
          badge: { variant: 'secondary' as const, text: agent.status === 'loading' ? 'Loading' : 'Unavailable' },
          className: 'text-blue-500'
        };
      }
    }

    return {
      icon: <CheckCircle className="h-4 w-4" />,
      badge: { variant: 'default' as const, text: 'Available' },
      className: 'text-green-500'
    };
  };

  const getStatusBadge = () => {
    const statusInfo = getStatusInfo(agent);
    return (
      <Badge variant={statusInfo.badge.variant} className={cn("flex items-center gap-1 text-xs", statusInfo.className)}>
        {statusInfo.icon}
        {statusInfo.badge.text}
      </Badge>
    );
  };

  const getVersionBadge = () => {
    if (compact || !agent.version) {
      return null;
    }

    return (
      <Badge variant="outline" className="text-xs">
        v{agent.version}
      </Badge>
    );
  };

  const getEnvironmentsBadges = () => {
    if (!showExtendedDetails || !agent.supported_environments || agent.supported_environments.length === 0) {
      return null;
    }

    const maxVisible = compact ? 1 : 2;
    const visibleEnvs = agent.supported_environments.slice(0, maxVisible);
    const remainingCount = agent.supported_environments.length - maxVisible;

    return (
      <div className="flex flex-wrap gap-1">
        {visibleEnvs.map((env) => (
          <Badge key={env} variant="outline" className="text-xs capitalize">
            {env}
          </Badge>
        ))}
        {remainingCount > 0 && (
          <Badge variant="outline" className="text-xs">
            +{remainingCount} more
          </Badge>
        )}
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    if (compact || isMobile) {
      return date.toLocaleDateString();
    }
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleCardClick = () => {
    if (selectionMode && onSelect && isAgentAvailable(agent)) {
      onSelect(agent);
    }
  };

  const handleConfigureClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onConfigure) {
      onConfigure(agent);
    }
  };

  return (
    <Card 
      className={cn(
        "touch-manipulation transition-all duration-200 cursor-pointer",
        selectionMode && "hover:ring-2 hover:ring-primary/20",
        !isAgentAvailable(agent) && "opacity-75",
        agent.has_error && "border-red-200 hover:border-red-300",
        className
      )}
      onClick={handleCardClick}
    >
      <CardHeader className={cn("pb-3", compact && "pb-2")}>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className={cn(
              "leading-tight truncate",
              compact ? "text-sm" : "text-base"
            )}>
              {agent.name}
            </CardTitle>
            <p className={cn(
              "text-muted-foreground font-mono mt-1",
              compact ? "text-xs" : "text-xs"
            )}>
              {agent.identifier}
            </p>
          </div>
          <div className="flex flex-col gap-1 ml-2">
            {getStatusBadge()}
            {!compact && getVersionBadge()}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className={cn("space-y-3", compact && "space-y-2")}>
        <p className={cn(
          "text-muted-foreground",
          compact ? "text-xs line-clamp-1" : "text-sm line-clamp-2"
        )}>
          {agent.description}
        </p>
        
        {showExtendedDetails && agent.supported_environments && agent.supported_environments.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Environments:</p>
            {getEnvironmentsBadges()}
          </div>
        )}

        {agent.error_message && (
          <div className="p-2 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-xs text-destructive font-medium">Error:</p>
            <p className="text-xs text-destructive mt-1 line-clamp-2">{agent.error_message}</p>
          </div>
        )}

        {showExtendedDetails && agent.created_at && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Created:
              </span>
              <span>{formatDate(agent.created_at)}</span>
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-border/50">
          <div className="flex justify-between items-center text-xs text-muted-foreground">
            <span>Updated:</span>
            <span>{agent.last_updated ? formatDate(agent.last_updated) : 'Unknown'}</span>
          </div>
        </div>

        {(selectionMode || showConfigButton) && (
          <div className={cn(
            "flex gap-2 mt-4",
            selectionMode && showConfigButton ? "flex-row" : "flex-col"
          )}>
            {selectionMode && (
              <Button 
                size="sm" 
                className="flex-1"
                disabled={!isAgentAvailable(agent)}
                onClick={() => onSelect?.(agent)}
              >
                Select Agent
              </Button>
            )}
            
            {showConfigButton && (
              <Button 
                size="sm" 
                variant="outline"
                className={cn("flex items-center gap-1", selectionMode ? "flex-shrink-0" : "w-full")}
                onClick={handleConfigureClick}
                disabled={!isAgentAvailable(agent)}
              >
                <Settings className="h-3 w-3" />
                {selectionMode ? "" : "Configure"}
              </Button>
            )}
          </div>
        )}

        {agent.runtime_info && showExtendedDetails && (
          <div className="mt-2 pt-2 border-t border-border/50">
            <p className="text-xs font-medium text-muted-foreground mb-1">Runtime:</p>
            <div className="text-xs text-muted-foreground space-y-1">
              {agent.instance_available !== undefined && (
                <div className="flex justify-between">
                  <span>Instance:</span>
                  <span className={agent.instance_available ? "text-green-600" : "text-orange-600"}>
                    {agent.instance_available ? "Available" : "Unavailable"}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AgentCard; 