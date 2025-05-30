import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader } from './card';
import { Skeleton } from './skeleton';

// Simple loading spinner
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  variant?: 'default' | 'subtle';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className,
  variant = 'default'
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  const variantClasses = {
    default: 'text-primary',
    subtle: 'text-muted-foreground',
  };

  return (
    <Loader2 
      className={cn(
        'animate-spin',
        sizeClasses[size],
        variantClasses[variant],
        className
      )} 
    />
  );
};

// Loading overlay for sections or full page
interface LoadingOverlayProps {
  children?: React.ReactNode;
  loading: boolean;
  text?: string;
  variant?: 'overlay' | 'inline' | 'card';
  className?: string;
  spinnerSize?: 'sm' | 'md' | 'lg';
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  children,
  loading,
  text = 'Loading...',
  variant = 'overlay',
  className,
  spinnerSize = 'md'
}) => {
  if (!loading && variant === 'overlay') {
    return <>{children}</>;
  }

  if (!loading && variant === 'inline') {
    return <>{children}</>;
  }

  const LoadingContent = () => (
    <div className="flex flex-col items-center justify-center gap-3">
      <LoadingSpinner size={spinnerSize} />
      {text && (
        <p className="text-sm text-muted-foreground font-medium">{text}</p>
      )}
    </div>
  );

  if (variant === 'overlay') {
    return (
      <div className="relative">
        {children}
        {loading && (
          <div className={cn(
            "absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10",
            className
          )}>
            <LoadingContent />
          </div>
        )}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <LoadingContent />
        </CardContent>
      </Card>
    );
  }

  // inline variant
  return (
    <div className={cn("flex items-center justify-center py-8", className)}>
      <LoadingContent />
    </div>
  );
};

// Full page loading screen
interface PageLoadingProps {
  text?: string;
  className?: string;
}

export const PageLoading: React.FC<PageLoadingProps> = ({ 
  text = 'Loading...', 
  className 
}) => {
  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800",
      className
    )}>
      <div className="text-center space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-muted-foreground font-medium">{text}</p>
      </div>
    </div>
  );
};

// Loading button with spinner
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading = false,
  loadingText,
  children,
  disabled,
  className,
  ...props
}) => {
  return (
    <button
      {...props}
      disabled={loading || disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50",
        className
      )}
    >
      {loading && <LoadingSpinner size="sm" />}
      {loading ? (loadingText || children) : children}
    </button>
  );
};

// Table loading skeleton
interface TableLoadingProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  className?: string;
}

export const TableLoading: React.FC<TableLoadingProps> = ({
  rows = 5,
  columns = 4,
  showHeader = true,
  className
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      {showHeader && (
        <div className="flex items-center space-x-4">
          {Array.from({ length: columns }, (_, i) => (
            <Skeleton key={i} className="h-4 w-20" />
          ))}
        </div>
      )}
      {Array.from({ length: rows }, (_, rowIndex) => (
        <div key={rowIndex} className="flex items-center space-x-4">
          {Array.from({ length: columns }, (_, colIndex) => (
            <Skeleton
              key={colIndex}
              className={cn(
                "h-4",
                colIndex === 0 ? "w-12" : colIndex === 1 ? "w-32" : "w-20"
              )}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

// Card loading skeleton
interface CardLoadingProps {
  count?: number;
  className?: string;
  showTitle?: boolean;
  contentLines?: number;
}

export const CardLoading: React.FC<CardLoadingProps> = ({
  count = 1,
  className,
  showTitle = true,
  contentLines = 3
}) => {
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <Card key={index} className={className}>
          <CardHeader>
            {showTitle && <Skeleton className="h-5 w-32" />}
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: contentLines }, (_, lineIndex) => (
              <Skeleton
                key={lineIndex}
                className={cn(
                  "h-4",
                  lineIndex === contentLines - 1 ? "w-3/4" : "w-full"
                )}
              />
            ))}
          </CardContent>
        </Card>
      ))}
    </>
  );
};

// Stats grid loading skeleton
export const StatsGridLoading: React.FC<{ count?: number; className?: string }> = ({ 
  count = 5, 
  className 
}) => {
  return (
    <div className={cn("grid gap-4 md:grid-cols-2 lg:grid-cols-5", className)}>
      {Array.from({ length: count }, (_, i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-12" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Refresh loading indicator
interface RefreshLoadingProps {
  isRefreshing: boolean;
  onRefresh: () => void;
  disabled?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const RefreshLoading: React.FC<RefreshLoadingProps> = ({
  isRefreshing,
  onRefresh,
  disabled = false,
  className,
  size = 'sm'
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  return (
    <button
      onClick={onRefresh}
      disabled={isRefreshing || disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-md border border-input bg-background text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50",
        size === 'sm' ? 'h-8 w-8' : size === 'md' ? 'h-9 w-9' : 'h-10 w-10',
        className
      )}
    >
      <RefreshCw className={cn(sizeClasses[size], isRefreshing && 'animate-spin')} />
    </button>
  );
}; 