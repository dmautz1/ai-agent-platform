import React, { Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { responsivePadding, responsiveSpacing, touchButtonSizes } from '@/lib/responsive';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Button } from '@/components/ui/button';
import { User, Loader2, Home, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentInfo } from '@/lib/types';

// Dynamic import for heavy component
const AgentDirectoryComponent = React.lazy(() => import('@/components/AgentDirectory').then(module => ({ default: module.AgentDirectory })));

// Loading component for Suspense fallback
const DirectoryLoader: React.FC = () => (
  <div className="flex items-center justify-center p-12">
    <div className="flex items-center gap-3 text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
      <div>
        <div className="text-base font-medium">Loading Agent Directory</div>
        <div className="text-sm">Preparing available agents...</div>
      </div>
    </div>
  </div>
);

export const AgentDirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const handleAgentSelect = (agent: AgentInfo) => {
    // Navigate to dashboard and trigger job creation with this agent
    // We can pass the agent identifier as a query parameter
    navigate(`/?agent=${agent.identifier}`);
  };

  // Navigation header component
  const NavigationHeader: React.FC = () => (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className={cn(responsivePadding.section, "py-3 sm:py-4")}>
        <div className="flex items-center justify-between">
          {/* Platform title and breadcrumb */}
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">AI Agent Platform</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                Agent Directory
              </p>
            </div>
          </div>
          
          {/* Navigation actions */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Dashboard button */}
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
            
            {/* Scheduled Jobs button */}
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <NavigationHeader />

      {/* Main Content */}
      <main className={cn(responsivePadding.section, responsiveSpacing.component)}>
        <div className="space-y-6 sm:space-y-8">
          {/* Agent Directory Component */}
          <Suspense fallback={<DirectoryLoader />}>
            <AgentDirectoryComponent
              onSelectAgent={handleAgentSelect}
              selectionMode={true}
              showFilters={true}
              showEnvironmentFilter={false}
              showStateFilter={true}
            />
          </Suspense>
        </div>
      </main>
    </div>
  );
};

export default AgentDirectoryPage; 