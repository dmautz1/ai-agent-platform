import React from 'react';
import { cn } from '@/lib/utils';
import { 
  FileX, 
  Search, 
  Plus, 
  Inbox, 
  Database,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  Zap
} from 'lucide-react';
import { Button } from './button';
import { Card, CardContent } from './card';

// Base empty state component
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
    icon?: React.ReactNode;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
    icon?: React.ReactNode;
  };
  className?: string;
  variant?: 'default' | 'minimal' | 'card';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
  variant = 'default'
}) => {
  const defaultIcon = <Inbox className="h-12 w-12 text-muted-foreground/50" />;

  const Content = () => (
    <>
      <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-muted/30">
        {icon || defaultIcon}
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
          {description}
        </p>
      )}
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {action && (
            <Button
              variant={action.variant || 'default'}
              onClick={action.onClick}
              className="flex items-center gap-2"
            >
              {action.icon}
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant={secondaryAction.variant || 'outline'}
              onClick={secondaryAction.onClick}
              className="flex items-center gap-2"
            >
              {secondaryAction.icon}
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </>
  );

  if (variant === 'card') {
    return (
      <Card className={className}>
        <CardContent className="text-center py-12">
          <Content />
        </CardContent>
      </Card>
    );
  }

  if (variant === 'minimal') {
    return (
      <div className={cn("text-center py-8", className)}>
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted/30">
          {icon || <Inbox className="h-6 w-6 text-muted-foreground/50" />}
        </div>
        <p className="text-sm text-muted-foreground">{title}</p>
        {action && (
          <Button
            variant="ghost"
            size="sm"
            onClick={action.onClick}
            className="mt-2"
          >
            {action.icon}
            {action.label}
          </Button>
        )}
      </div>
    );
  }

  // default variant
  return (
    <div className={cn("text-center py-12", className)}>
      <Content />
    </div>
  );
};

// Empty jobs list
interface EmptyJobsProps {
  onCreateJob?: () => void;
  onLearnMore?: () => void;
  className?: string;
}

export const EmptyJobs: React.FC<EmptyJobsProps> = ({
  onCreateJob,
  onLearnMore,
  className
}) => {
  return (
    <EmptyState
      icon={<Zap className="h-12 w-12 text-muted-foreground/50" />}
      title="No jobs found"
      description="Get started by creating your first AI agent job. You can process text, summarize content, or scrape web data."
      action={onCreateJob ? {
        label: 'Create First Job',
        onClick: onCreateJob,
        icon: <Plus className="h-4 w-4" />
      } : undefined}
      secondaryAction={onLearnMore ? {
        label: 'Learn More',
        onClick: onLearnMore,
        variant: 'outline'
      } : undefined}
      className={className}
    />
  );
};

// Empty search results
interface EmptySearchProps {
  query?: string;
  onClearSearch?: () => void;
  onCreateNew?: () => void;
  className?: string;
}

export const EmptySearch: React.FC<EmptySearchProps> = ({
  query,
  onClearSearch,
  onCreateNew,
  className
}) => {
  return (
    <EmptyState
      icon={<Search className="h-12 w-12 text-muted-foreground/50" />}
      title={query ? `No results for "${query}"` : "No results found"}
      description="Try adjusting your search terms or create a new item."
      action={onClearSearch ? {
        label: 'Clear Search',
        onClick: onClearSearch,
        variant: 'outline'
      } : undefined}
      secondaryAction={onCreateNew ? {
        label: 'Create New',
        onClick: onCreateNew,
        icon: <Plus className="h-4 w-4" />
      } : undefined}
      className={className}
    />
  );
};

// Empty filtered results
interface EmptyFilterProps {
  onClearFilters?: () => void;
  onViewAll?: () => void;
  filterCount?: number;
  className?: string;
}

export const EmptyFilter: React.FC<EmptyFilterProps> = ({
  onClearFilters,
  onViewAll,
  filterCount,
  className
}) => {
  return (
    <EmptyState
      icon={<Database className="h-12 w-12 text-muted-foreground/50" />}
      title="No items match your filters"
      description={`${filterCount ? `${filterCount} filter${filterCount > 1 ? 's' : ''} applied.` : ''} Try adjusting your filters or view all items.`}
      action={onClearFilters ? {
        label: 'Clear Filters',
        onClick: onClearFilters,
        variant: 'outline'
      } : undefined}
      secondaryAction={onViewAll ? {
        label: 'View All',
        onClick: onViewAll
      } : undefined}
      className={className}
    />
  );
};

// Empty user list
interface EmptyUsersProps {
  onInviteUser?: () => void;
  onImportUsers?: () => void;
  className?: string;
}

export const EmptyUsers: React.FC<EmptyUsersProps> = ({
  onInviteUser,
  onImportUsers,
  className
}) => {
  return (
    <EmptyState
      icon={<Users className="h-12 w-12 text-muted-foreground/50" />}
      title="No users yet"
      description="Start building your team by inviting users or importing them from your existing systems."
      action={onInviteUser ? {
        label: 'Invite User',
        onClick: onInviteUser,
        icon: <Plus className="h-4 w-4" />
      } : undefined}
      secondaryAction={onImportUsers ? {
        label: 'Import Users',
        onClick: onImportUsers,
        variant: 'outline'
      } : undefined}
      className={className}
    />
  );
};

// Empty by job status
interface EmptyJobsByStatusProps {
  status: 'pending' | 'running' | 'completed' | 'failed';
  onViewAll?: () => void;
  onCreateJob?: () => void;
  className?: string;
}

export const EmptyJobsByStatus: React.FC<EmptyJobsByStatusProps> = ({
  status,
  onViewAll,
  onCreateJob,
  className
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          icon: <Clock className="h-12 w-12 text-yellow-500/50" />,
          title: 'No pending jobs',
          description: 'All jobs are currently being processed or have completed.'
        };
      case 'running':
        return {
          icon: <Zap className="h-12 w-12 text-blue-500/50" />,
          title: 'No running jobs',
          description: 'No jobs are currently being processed. Create a new job to get started.'
        };
      case 'completed':
        return {
          icon: <CheckCircle className="h-12 w-12 text-green-500/50" />,
          title: 'No completed jobs',
          description: 'Jobs that finish successfully will appear here.'
        };
      case 'failed':
        return {
          icon: <XCircle className="h-12 w-12 text-red-500/50" />,
          title: 'No failed jobs',
          description: 'Great! All your jobs have completed successfully.'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <EmptyState
      icon={config.icon}
      title={config.title}
      description={config.description}
      action={onCreateJob && status !== 'failed' ? {
        label: 'Create Job',
        onClick: onCreateJob,
        icon: <Plus className="h-4 w-4" />
      } : undefined}
      secondaryAction={onViewAll ? {
        label: 'View All Jobs',
        onClick: onViewAll,
        variant: 'outline'
      } : undefined}
      className={className}
    />
  );
};

// Generic empty data state
interface EmptyDataProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyData: React.FC<EmptyDataProps> = ({
  title = "No data available",
  description = "There's nothing to show here yet.",
  actionLabel,
  onAction,
  className
}) => {
  return (
    <EmptyState
      icon={<FileX className="h-12 w-12 text-muted-foreground/50" />}
      title={title}
      description={description}
      action={onAction && actionLabel ? {
        label: actionLabel,
        onClick: onAction
      } : undefined}
      className={className}
      variant="minimal"
    />
  );
}; 