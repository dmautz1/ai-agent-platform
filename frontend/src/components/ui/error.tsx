import React from 'react';
import { cn } from '@/lib/utils';
import { 
  AlertTriangle, 
  XCircle, 
  AlertCircle, 
  WifiOff, 
  ServerCrash, 
  FileX,
  RefreshCw,
  ArrowLeft,
  Bug,
  Shield
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './alert';
import { Button } from './button';
import { Card, CardContent, CardHeader, CardTitle } from './card';

// Base error message component
interface ErrorMessageProps {
  title?: string;
  message: string;
  variant?: 'default' | 'destructive' | 'warning';
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
  };
  className?: string;
  showIcon?: boolean;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title,
  message,
  variant = 'destructive',
  icon,
  action,
  className,
  showIcon = true
}) => {
  const getDefaultIcon = () => {
    switch (variant) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'destructive':
        return <XCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  // Map our variant to actual Alert component variants
  const alertVariant = variant === 'warning' ? 'default' : variant;

  return (
    <Alert variant={alertVariant} className={cn(
      variant === 'warning' && 'border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-200',
      className
    )}>
      {showIcon && (icon || getDefaultIcon())}
      {title && <AlertTitle>{title}</AlertTitle>}
      <AlertDescription className="flex items-center justify-between">
        <span>{message}</span>
        {action && (
          <Button
            variant={action.variant || 'outline'}
            size="sm"
            onClick={action.onClick}
            className="ml-4"
          >
            {action.label}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
};

// Network error component
interface NetworkErrorProps {
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  showRetry?: boolean;
}

export const NetworkError: React.FC<NetworkErrorProps> = ({
  onRetry,
  retryLabel = 'Retry',
  className,
  showRetry = true
}) => {
  return (
    <ErrorMessage
      title="Connection Problem"
      message="Unable to connect to the server. Please check your internet connection."
      icon={<WifiOff className="h-4 w-4" />}
      action={showRetry && onRetry ? {
        label: retryLabel,
        onClick: onRetry,
        variant: 'outline'
      } : undefined}
      className={className}
    />
  );
};

// Server error component
interface ServerErrorProps {
  onRetry?: () => void;
  onReport?: () => void;
  className?: string;
  showActions?: boolean;
}

export const ServerError: React.FC<ServerErrorProps> = ({
  onRetry,
  onReport,
  className,
  showActions = true
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <ErrorMessage
        title="Server Error"
        message="Something went wrong on our servers. Our team has been notified."
        icon={<ServerCrash className="h-4 w-4" />}
      />
      {showActions && (
        <div className="flex gap-2">
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="h-3 w-3 mr-2" />
              Try Again
            </Button>
          )}
          {onReport && (
            <Button variant="secondary" size="sm" onClick={onReport}>
              <Bug className="h-3 w-3 mr-2" />
              Report Issue
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

// Not found error component
interface NotFoundErrorProps {
  title?: string;
  message?: string;
  onGoBack?: () => void;
  onRetry?: () => void;
  className?: string;
  showActions?: boolean;
}

export const NotFoundError: React.FC<NotFoundErrorProps> = ({
  title = "Not Found",
  message = "The requested resource could not be found.",
  onGoBack,
  onRetry,
  className,
  showActions = true
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <ErrorMessage
        title={title}
        message={message}
        icon={<FileX className="h-4 w-4" />}
        variant="default"
      />
      {showActions && (
        <div className="flex gap-2">
          {onGoBack && (
            <Button variant="outline" size="sm" onClick={onGoBack}>
              <ArrowLeft className="h-3 w-3 mr-2" />
              Go Back
            </Button>
          )}
          {onRetry && (
            <Button variant="secondary" size="sm" onClick={onRetry}>
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

// Access denied error component
interface AccessDeniedErrorProps {
  message?: string;
  onSignIn?: () => void;
  className?: string;
  showSignIn?: boolean;
}

export const AccessDeniedError: React.FC<AccessDeniedErrorProps> = ({
  message = "You don't have permission to access this resource.",
  onSignIn,
  className,
  showSignIn = true
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <ErrorMessage
        title="Access Denied"
        message={message}
        icon={<Shield className="h-4 w-4" />}
        variant="warning"
      />
      {showSignIn && onSignIn && (
        <Button variant="outline" size="sm" onClick={onSignIn}>
          Sign In
        </Button>
      )}
    </div>
  );
};

// Full page error display
interface ErrorPageProps {
  title?: string;
  message: string;
  icon?: React.ReactNode;
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
    icon?: React.ReactNode;
  }>;
  className?: string;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
  title = "Something went wrong",
  message,
  icon,
  actions = [],
  className
}) => {
  return (
    <div className={cn(
      "min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6",
      className
    )}>
      <div className="max-w-md w-full">
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
              {icon || <XCircle className="h-6 w-6 text-destructive" />}
            </div>
            <CardTitle className="text-xl">{title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-center text-muted-foreground">{message}</p>
            {actions.length > 0 && (
              <div className="flex flex-col gap-2">
                {actions.map((action, index) => (
                  <Button
                    key={index}
                    variant={action.variant || 'default'}
                    onClick={action.onClick}
                    className="w-full"
                  >
                    {action.icon && <span className="mr-2">{action.icon}</span>}
                    {action.label}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Error card for sections
interface ErrorCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
  variant?: 'default' | 'destructive' | 'warning';
}

export const ErrorCard: React.FC<ErrorCardProps> = ({
  title = "Error",
  message,
  onRetry,
  className,
  variant = 'destructive'
}) => {
  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <ErrorMessage
          title={title}
          message={message}
          variant={variant}
          action={onRetry ? {
            label: 'Try Again',
            onClick: onRetry
          } : undefined}
        />
      </CardContent>
    </Card>
  );
};

// Inline error for form fields
interface FieldErrorProps {
  message: string;
  className?: string;
}

export const FieldError: React.FC<FieldErrorProps> = ({ message, className }) => {
  return (
    <p className={cn("text-sm text-destructive flex items-center gap-1", className)}>
      <XCircle className="h-3 w-3" />
      {message}
    </p>
  );
};

// Error boundary fallback component
interface ErrorBoundaryFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

export const ErrorBoundaryFallback: React.FC<ErrorBoundaryFallbackProps> = ({
  error,
  resetErrorBoundary
}) => {
  return (
    <ErrorPage
      title="Application Error"
      message={process.env.NODE_ENV === 'development' 
        ? `An unexpected error occurred: ${error.message}` 
        : "An unexpected error occurred. Please try refreshing the page."
      }
      icon={<Bug className="h-6 w-6 text-destructive" />}
      actions={[
        {
          label: 'Try Again',
          onClick: resetErrorBoundary,
          variant: 'default',
          icon: <RefreshCw className="h-4 w-4" />
        },
        {
          label: 'Reload Page',
          onClick: () => window.location.reload(),
          variant: 'outline',
          icon: <RefreshCw className="h-4 w-4" />
        }
      ]}
    />
  );
};

// Validation error summary component
interface ValidationErrorSummaryProps {
  errors: string[];
  title?: string;
  className?: string;
}

export const ValidationErrorSummary: React.FC<ValidationErrorSummaryProps> = ({
  errors,
  title = "Please fix the following errors:",
  className
}) => {
  if (errors.length === 0) return null;

  return (
    <Alert variant="destructive" className={className}>
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        <ul className="mt-2 space-y-1 list-disc list-inside">
          {errors.map((error, index) => (
            <li key={index} className="text-sm">{error}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}; 