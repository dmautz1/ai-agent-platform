import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Plus, Calendar, User, Home, Users } from 'lucide-react';
import { responsivePadding, touchButtonSizes } from '@/lib/responsive';
import { cn } from '@/lib/utils';

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  showCreateJobButton?: boolean;
  onCreateJob?: () => void;
  currentPage?: 'dashboard' | 'scheduled-jobs' | 'agent-directory';
}

export const AppHeader: React.FC<AppHeaderProps> = ({ 
  title = "AI Agent Platform",
  subtitle = "Job Management Dashboard",
  showCreateJobButton = true,
  onCreateJob,
  currentPage = 'dashboard'
}) => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const isCurrentPage = (page: string) => currentPage === page;

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className={cn(responsivePadding.section, "py-3 sm:py-4")}>
        <div className="flex items-center justify-between">
          {/* Platform title and breadcrumb */}
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">{title}</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                {subtitle}
              </p>
            </div>
          </div>
          
          {/* Navigation actions */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Dashboard button */}
            {!isCurrentPage('dashboard') && (
              <Button 
                variant="outline"
                size="sm" 
                className={cn(
                  "flex items-center gap-2 touch-manipulation",
                  touchButtonSizes.sm
                )} 
                onClick={() => navigate('/dashboard')}
              >
                <Home className="h-4 w-4" />
                <span className="hidden sm:inline">Dashboard</span>
              </Button>
            )}
            
            {/* Agent Directory button */}
            {!isCurrentPage('agent-directory') && (
              <Button 
                variant="outline"
                size="sm" 
                className={cn(
                  "flex items-center gap-2 touch-manipulation",
                  touchButtonSizes.sm
                )} 
                onClick={() => navigate('/agent-directory')}
              >
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Agents</span>
              </Button>
            )}
            
            {/* Scheduled Jobs button */}
            {!isCurrentPage('scheduled-jobs') && (
              <Button 
                variant="outline"
                size="sm" 
                className={cn(
                  "flex items-center gap-2 touch-manipulation",
                  touchButtonSizes.sm
                )} 
                onClick={() => navigate('/scheduled-jobs')}
              >
                <Calendar className="h-4 w-4" />
                <span className="hidden sm:inline">Schedules</span>
              </Button>
            )}
            
            {/* Create job button */}
            {showCreateJobButton && onCreateJob && (
              <Button 
                size="sm" 
                className={cn(
                  "flex items-center gap-2 touch-manipulation",
                  touchButtonSizes.sm
                )} 
                onClick={onCreateJob}
              >
                <Plus className="h-4 w-4" />
                <span className="hidden sm:inline">New Job</span>
                <span className="sm:hidden">New</span>
              </Button>
            )}
            
            {/* Theme switcher */}
            <ThemeSwitcher />
            
            {/* User menu */}
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg border sm:px-3 sm:py-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium max-w-[100px] truncate sm:max-w-none">
                {user?.email}
              </span>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={signOut}
                className="h-6 px-2 text-xs sm:ml-2"
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AppHeader; 