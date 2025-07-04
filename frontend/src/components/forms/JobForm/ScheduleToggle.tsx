import React from 'react';
import { useBreakpoint, responsiveTextSizes } from '@/lib/responsive';
import { cn } from '@/lib/utils';

interface ScheduleToggleProps {
  /** Current execution mode: 'now' for immediate execution, 'schedule' for scheduled execution */
  mode: 'now' | 'schedule';
  
  /** Callback when the mode changes */
  onModeChange: (mode: 'now' | 'schedule') => void;
  
  /** Optional CSS class name */
  className?: string;
  
  /** Disable the toggle */
  disabled?: boolean;
  
  /** Show labels for the toggle options */
  showLabels?: boolean;
}

/**
 * ScheduleToggle Component
 * 
 * A toggle component that allows users to choose between immediate execution
 * ("Run Now") and scheduled execution ("Schedule") for agent jobs.
 * 
 * Features:
 * - Clean toggle UI with visual feedback
 * - Accessible keyboard navigation
 * - Optional labels for clarity
 * - Disabled state support
 * - Responsive design with mobile-first approach
 * - Touch-friendly interface
 * - Light and dark mode support
 */
const ScheduleToggle: React.FC<ScheduleToggleProps> = ({
  mode,
  onModeChange,
  className = '',
  disabled = false,
  showLabels = true
}) => {
  const { isMobile } = useBreakpoint();

  const baseClasses = cn(
    "flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 p-4 sm:p-3 rounded-lg border-2 transition-all duration-200",
    disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary/50 dark:hover:border-primary/40',
    mode === 'schedule' 
      ? 'border-primary bg-primary/5 dark:bg-primary/10' 
      : 'border-muted-foreground/30 bg-background dark:bg-card hover:bg-muted/50',
    className
  );

  return (
    <div className={baseClasses}>
      {/* Run Now Option */}
      <div className="flex items-center gap-3 sm:gap-2 flex-1">
        <input
          type="radio"
          id="run-now"
          name="execution-mode"
          value="now"
          checked={mode === 'now'}
          onChange={() => onModeChange('now')}
          disabled={disabled}
          className={cn(
            "text-primary focus:ring-primary border-muted-foreground/30 disabled:opacity-50 dark:border-muted-foreground/50",
            isMobile ? "h-5 w-5" : "h-4 w-4"
          )}
        />
        <label
          htmlFor="run-now"
          className={cn(
            "font-medium cursor-pointer flex-1",
            disabled ? 'cursor-not-allowed' : 'cursor-pointer',
            mode === 'now' ? 'text-primary dark:text-primary' : 'text-foreground dark:text-foreground',
            responsiveTextSizes.sm
          )}
        >
          <div className="flex items-center gap-2">
            <svg className={cn("flex-shrink-0", isMobile ? "h-5 w-5" : "h-4 w-4")} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span className="font-semibold">Run Now</span>
          </div>
          {showLabels && mode === 'now' && (
            <div className={cn("text-muted-foreground mt-1", isMobile ? "text-sm" : "text-xs")}>
              Execute immediately
            </div>
          )}
        </label>
      </div>

      {/* Divider */}
      <div className={cn(
        "bg-muted-foreground/30 dark:bg-muted-foreground/50",
        isMobile ? "h-px w-full" : "h-8 w-px"
      )} />

      {/* Schedule Option */}
      <div className="flex items-center gap-3 sm:gap-2 flex-1">
        <input
          type="radio"
          id="schedule"
          name="execution-mode"
          value="schedule"
          checked={mode === 'schedule'}
          onChange={() => onModeChange('schedule')}
          disabled={disabled}
          className={cn(
            "text-primary focus:ring-primary border-muted-foreground/30 disabled:opacity-50 dark:border-muted-foreground/50",
            isMobile ? "h-5 w-5" : "h-4 w-4"
          )}
        />
        <label
          htmlFor="schedule"
          className={cn(
            "font-medium cursor-pointer flex-1",
            disabled ? 'cursor-not-allowed' : 'cursor-pointer',
            mode === 'schedule' ? 'text-primary dark:text-primary' : 'text-foreground dark:text-foreground',
            responsiveTextSizes.sm
          )}
        >
          <div className="flex items-center gap-2">
            <svg className={cn("flex-shrink-0", isMobile ? "h-5 w-5" : "h-4 w-4")} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-semibold">Schedule</span>
          </div>
          {showLabels && mode === 'schedule' && (
            <div className={cn("text-muted-foreground mt-1", isMobile ? "text-sm" : "text-xs")}>
              Set up recurring execution
            </div>
          )}
        </label>
      </div>
    </div>
  );
};

export default ScheduleToggle; 