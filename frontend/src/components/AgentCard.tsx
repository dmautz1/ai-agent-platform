import React from 'react';
import type { AgentInfo } from '@/lib/models';
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

  const getStatusBadge = () => {
    if (agent.has_error) {
      return (
        <Badge variant="destructive" className="flex items-center gap-1 text-xs">
          <XCircle className="h-3 w-3" />
          Error
        </Badge>
      );
    }

    if (!agent.enabled) {
      return (
        <Badge variant="secondary" className="flex items-center gap-1 text-xs">
          <Clock className="h-3 w-3" />
          Disabled
        </Badge>
      );
    }

    if (agent.lifecycle_state === 'enabled') {
      return (
        <Badge variant="default" className="flex items-center gap-1 bg-green-500 hover:bg-green-600 text-xs">
          <CheckCircle className="h-3 w-3" />
          Ready
        </Badge>
      );
    }

    return (
      <Badge variant="outline" className="flex items-center gap-1 text-xs">
        <AlertCircle className="h-3 w-3" />
        {agent.lifecycle_state}
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
    if (!showExtendedDetails || agent.supported_environments.length === 0) {
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
    if (selectionMode && onSelect && agent.enabled && !agent.has_error) {
      onSelect(agent);
    }
  };

  const handleConfigureClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when clicking configure button
    if (onConfigure) {
      onConfigure(agent);
    }
  };

  return (
    <Card 
      className={cn(
        "h-full transition-all duration-200",
        selectionMode 
          ? "cursor-pointer hover:shadow-md hover:scale-[1.02] active:scale-[0.98]"
          : "hover:shadow-sm",
        agent.has_error && "border-destructive/50",
        !agent.enabled && "opacity-75",
        compact && "text-sm",
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
        
        {showExtendedDetails && agent.supported_environments.length > 0 && (
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

        {showExtendedDetails && (
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
            <span>{formatDate(agent.last_updated)}</span>
          </div>
        </div>

        {(selectionMode || showConfigButton) && (
          <div className={cn(
            "flex gap-2",
            selectionMode && showConfigButton ? "flex-row" : "flex-col"
          )}>
            {selectionMode && (
              <Button 
                size="sm" 
                className="flex-1"
                disabled={!agent.enabled || agent.has_error}
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
                disabled={!agent.enabled}
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