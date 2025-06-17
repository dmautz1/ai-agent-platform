import React from 'react';
import { Loader2, RefreshCw, CheckCircle, Wifi, WifiOff, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { SchemaLoadingProgressProps } from './types';

export const SchemaLoadingProgress: React.FC<SchemaLoadingProgressProps> = ({ 
  loadingState, 
  onRetry, 
  agentName 
}) => {
  const getStageIcon = () => {
    switch (loadingState.stage) {
      case 'fetching':
        return <Wifi className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'parsing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'validating':
        return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />;
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Loader2 className="h-4 w-4 text-gray-500 animate-spin" />;
    }
  };

  const getStageDescription = () => {
    switch (loadingState.stage) {
      case 'fetching':
        return 'Retrieving agent schema from server...';
      case 'parsing':
        return 'Processing schema definitions...';
      case 'validating':
        return 'Validating schema structure...';
      case 'ready':
        return 'Schema loaded successfully!';
      default:
        return 'Initializing...';
    }
  };

  const getProgressColor = () => {
    if (loadingState.hasError) return 'bg-red-500';
    if (loadingState.progress === 100) return 'bg-green-500';
    return 'bg-blue-500';
  };

  if (loadingState.hasError) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-red-700">
            <WifiOff className="h-5 w-5" />
            Schema Loading Failed
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-red-600">
              Failed to load schema for agent: <span className="font-medium">{agentName || 'Unknown'}</span>
            </p>
            <p className="text-xs text-red-500">
              {loadingState.message || 'An unexpected error occurred while loading the agent schema.'}
            </p>
          </div>
          
          {loadingState.canRetry && onRetry && (
            <Button
              onClick={onRetry}
              variant="outline"
              size="sm"
              className="text-red-700 border-red-300 hover:bg-red-100"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  if (!loadingState.isLoading && loadingState.stage === 'ready') {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Schema loaded successfully</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-blue-700">
          <Zap className="h-5 w-5" />
          Loading Agent Schema
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-600">
              {agentName && <span className="font-medium">{agentName}</span>}
            </span>
            <span className="text-xs text-blue-500">
              {loadingState.progress}%
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-blue-100 rounded-full h-2">
            <div
              className={cn("h-2 rounded-full transition-all duration-300", getProgressColor())}
              style={{ width: `${loadingState.progress}%` }}
            />
          </div>
        </div>

        {/* Current stage */}
        <div className="flex items-center gap-2">
          {getStageIcon()}
          <span className="text-sm text-blue-600">
            {getStageDescription()}
          </span>
        </div>

        {/* Custom message */}
        {loadingState.message && (
          <p className="text-xs text-blue-500 italic">
            {loadingState.message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}; 