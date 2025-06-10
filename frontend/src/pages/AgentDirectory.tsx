import React, { Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useBreakpoint, responsivePadding, responsiveSpacing } from '@/lib/responsive';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Button } from '@/components/ui/button';
import { ArrowLeft, User, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentInfo } from '@/lib/models';

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
  const { isMobile } = useBreakpoint();

  const handleAgentSelect = (agent: AgentInfo) => {
    // Navigate to dashboard and trigger job creation with this agent
    // We can pass the agent identifier as a query parameter
    navigate(`/?agent=${agent.identifier}`);
  };

  const handleBackToDashboard = () => {
    navigate('/');
  };

  // Mobile header component
  const MobileHeader: React.FC = () => (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className={cn(responsivePadding.section, "py-3 sm:py-4")}>
        <div className="flex items-center justify-between">
          {/* Navigation and title */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBackToDashboard}
              className="flex items-center gap-2 -ml-2"
            >
              <ArrowLeft className="h-4 w-4" />
              {!isMobile && <span>Dashboard</span>}
            </Button>
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Agent Directory</h1>
              <p className="text-xs text-muted-foreground sm:text-sm">
                Browse and select AI agents
              </p>
            </div>
          </div>
          
          {/* Theme switcher and user menu */}
          <div className="flex items-center gap-2">
            <ThemeSwitcher />
            
            {/* User menu */}
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg border sm:px-3 sm:py-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium max-w-[100px] truncate sm:max-w-none">
                {user?.name || user?.email}
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
      <MobileHeader />

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