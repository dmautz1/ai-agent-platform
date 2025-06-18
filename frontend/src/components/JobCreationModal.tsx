import React, { Suspense } from 'react';
import { Dialog, DialogContent} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AgentSelector } from '@/components/AgentSelector';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentInfo } from '@/lib/types';

// Dynamic imports for heavy components
const JobForm = React.lazy(() => import('@/components/forms/JobForm').then(module => ({ default: module.JobForm })));
const AgentDirectory = React.lazy(() => import('@/components/AgentDirectory').then(module => ({ default: module.AgentDirectory })));

// Loading component for Suspense fallback
const ComponentLoader: React.FC<{ message?: string }> = ({ message = "Loading..." }) => (
  <div className="flex items-center justify-center p-8">
    <div className="flex items-center gap-2 text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm">{message}</span>
    </div>
  </div>
);

interface JobCreationModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  selectedAgentId: string;
  showAgentDirectory: boolean;
  recentAgents: string[];
  onJobCreated: (jobId: string) => void;
  onQuickAgentSelected: (agentId: string) => void;
  onBrowseAllAgents: () => void;
  onAgentDirectorySelected: (agent: AgentInfo) => void;
  onBackToAgentSelection: () => void;
}

export const JobCreationModal: React.FC<JobCreationModalProps> = ({
  isOpen,
  onOpenChange,
  selectedAgentId,
  showAgentDirectory,
  recentAgents,
  onJobCreated,
  onQuickAgentSelected,
  onBrowseAllAgents,
  onAgentDirectorySelected,
  onBackToAgentSelection,
}) => {
  const renderJobCreationContent = () => {
    if (selectedAgentId) {
      // Show job form for selected agent
      return (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onBackToAgentSelection}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Agent Selection
            </Button>
          </div>
          <Suspense fallback={<ComponentLoader message="Loading job form..." />}>
            <JobForm 
              agentId={selectedAgentId} 
              onJobCreated={onJobCreated} 
            />
          </Suspense>
        </div>
      );
    }

    if (showAgentDirectory) {
      // Show full agent directory browser
      return (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onBackToAgentSelection}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Quick Select
            </Button>
          </div>
          <Suspense fallback={<ComponentLoader message="Loading agent directory..." />}>
            <AgentDirectory 
              onSelectAgent={onAgentDirectorySelected}
              selectionMode={true}
              showFilters={true}
            />
          </Suspense>
        </div>
      );
    }

    // Show quick agent selector (default view)
    return (
      <div className="space-y-4">
        <div>
          <AgentSelector
            onAgentSelected={onQuickAgentSelected}
            onBrowseAll={onBrowseAllAgents}
            recentAgents={recentAgents}
            placeholder="Select an agent to create a job..."
          />
        </div>
        
        {recentAgents.length > 0 && (
          <div className="text-xs text-muted-foreground">
            💡 Tip: Your recently used agents appear at the top of the list
          </div>
        )}
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className={cn(
        "w-full max-w-[calc(100vw-1rem)] max-h-[calc(100vh-2rem)]",
        "sm:max-w-[600px] sm:max-h-[80vh]",
        "overflow-y-auto"
      )}>
        {renderJobCreationContent()}
      </DialogContent>
    </Dialog>
  );
}; 