import React from 'react';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ValidationErrorDisplayProps } from './types';

// Enhanced error display component
export const ValidationErrorDisplay: React.FC<ValidationErrorDisplayProps> = ({ error, className }) => {
  const getErrorIcon = () => {
    switch (error.severity) {
      case 'warning':
        return <AlertCircle className="h-3 w-3 text-yellow-500" />;
      default:
        return <AlertCircle className="h-3 w-3 text-red-500" />;
    }
  };

  const getErrorColor = () => {
    switch (error.severity) {
      case 'warning':
        return 'text-yellow-600';
      default:
        return 'text-red-500';
    }
  };

  return (
    <div className={cn("space-y-1", className)}>
      <div className={cn("text-sm flex items-center gap-1", getErrorColor())}>
        {getErrorIcon()}
        <span className="font-medium">{error.message}</span>
      </div>
      {error.suggestion && (
        <p className="text-xs text-muted-foreground pl-4">
          💡 {error.suggestion}
        </p>
      )}
    </div>
  );
}; 