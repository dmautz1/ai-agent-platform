import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Clock, CheckCircle, XCircle, ChevronRight, RefreshCw, Wifi, WifiOff, Pause, Play } from 'lucide-react';
import { StatsGridLoading } from '@/components/ui/loading';
import { ErrorMessage } from '@/components/ui/error';
import { cn } from '@/lib/utils';

interface Stats {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

interface PollingState {
  error: string | null;
  isPaused: boolean;
  isPolling: boolean;
  lastUpdate: Date | null;
}

interface StatsOverviewSectionProps {
  stats: Stats;
  loading: boolean;
  pollingState: PollingState;
  onRefresh: () => void;
  onTogglePolling: () => void;
  collapsible?: boolean;
  initiallyCollapsed?: boolean;
}

const StatCard: React.FC<{ 
  title: string; 
  value: number; 
  icon: React.ReactNode; 
  color: string;
}> = ({ title, value, icon, color }) => (
  <Card className="touch-manipulation">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium leading-none">{title}</CardTitle>
      <div className={`${color}`}>{icon}</div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold tabular-nums">{value}</div>
    </CardContent>
  </Card>
);

export const StatsOverviewSection: React.FC<StatsOverviewSectionProps> = ({
  stats,
  loading,
  pollingState,
  onRefresh,
  onTogglePolling,
  collapsible = true,
  initiallyCollapsed = false
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(initiallyCollapsed);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 sm:pb-6">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-600" />
          <CardTitle className="text-lg sm:text-xl">System Overview</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {stats.total} total jobs
          </Badge>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {pollingState.error ? (
              <WifiOff className="h-3 w-3 text-red-500" />
            ) : pollingState.isPaused ? (
              <Pause className="h-3 w-3 text-orange-500" />
            ) : (
              <Wifi className="h-3 w-3 text-green-500" />
            )}
            <span className="hidden sm:inline">
              {pollingState.error ? 'Connection Issues' : 
               pollingState.isPaused ? 'Auto-refresh paused' :
               pollingState.lastUpdate ? `Updated: ${pollingState.lastUpdate.toLocaleTimeString()}` :
               'Connecting...'}
            </span>
            {pollingState.isPolling && !pollingState.isPaused && (
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            )}
            
            {/* Pause/Start button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onTogglePolling}
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              title={pollingState.isPaused ? "Start auto-refresh" : "Pause auto-refresh"}
            >
              {pollingState.isPaused ? (
                <Play className="h-3 w-3" />
              ) : (
                <Pause className="h-3 w-3" />
              )}
            </Button>
          </div>
          
          {/* Collapsible button */}
          {collapsible && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="h-6 w-6 p-0"
            >
              <ChevronRight
                className={cn(
                  "h-4 w-4 transition-transform",
                  !isCollapsed && "rotate-90"
                )}
              />
            </Button>
          )}
        </div>
      </CardHeader>
      {!isCollapsed && (
        <CardContent>
          {/* Stats Grid - Responsive */}
          <div className="grid gap-3 grid-cols-2 sm:gap-4 md:grid-cols-3 lg:grid-cols-5">
            {loading ? (
              <StatsGridLoading count={5} />
            ) : pollingState.error && !pollingState.lastUpdate ? (
              <div className="col-span-full">
                <ErrorMessage
                  title="Failed to Load Statistics"
                  message={pollingState.error}
                  action={{
                    label: 'Retry',
                    onClick: onRefresh
                  }}
                />
              </div>
            ) : (
              <>
                <StatCard
                  title="Total Jobs"
                  value={stats.total}
                  icon={<Activity className="h-4 w-4" />}
                  color="text-blue-600"
                />
                <StatCard
                  title="Pending"
                  value={stats.pending}
                  icon={<Clock className="h-4 w-4" />}
                  color="text-yellow-600"
                />
                <StatCard
                  title="Running"
                  value={stats.running}
                  icon={<Activity className="h-4 w-4" />}
                  color="text-blue-600"
                />
                <StatCard
                  title="Completed"
                  value={stats.completed}
                  icon={<CheckCircle className="h-4 w-4" />}
                  color="text-green-600"
                />
                <StatCard
                  title="Failed"
                  value={stats.failed}
                  icon={<XCircle className="h-4 w-4" />}
                  color="text-red-600"
                />
              </>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default StatsOverviewSection; 