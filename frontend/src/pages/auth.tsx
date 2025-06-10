import React from 'react';
import { SignInForm } from '../components/SignInForm';
import { useAuth } from '../contexts/AuthContext';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Badge } from '@/components/ui/badge';

export const AuthPage: React.FC = () => {
  const { loading } = useAuth();

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      {/* Theme switcher in top-right corner */}
      <div className="absolute top-4 right-4">
        <ThemeSwitcher />
      </div>
      
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Agent Platform</h1>
          <p className="text-muted-foreground">Sign in to manage your AI agents and jobs</p>
          <div className="inline-flex items-center gap-2 mt-4">
            <Badge variant="secondary" className="text-xs">
              Manual User Management
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Users must be added manually via Supabase dashboard
          </p>
        </div>

        <SignInForm />
      </div>
    </div>
  );
};

export default AuthPage; 