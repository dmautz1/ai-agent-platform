import React, { createContext, useContext, useEffect, useState } from 'react';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { User, AuthTokens, LoginRequest, RegisterRequest } from '@/lib/types';

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase environment variables');
}

const supabase: SupabaseClient = createClient(supabaseUrl, supabaseKey);

interface AuthState {
  user: User | null;
  loading: boolean;
  session: any;
  tokens?: AuthTokens;
}

interface AuthContextType extends AuthState {
  signIn: (credentials: LoginRequest) => Promise<{ user: User; tokens: AuthTokens }>;
  signUp: (userData: RegisterRequest) => Promise<{ user: User; tokens: AuthTokens }>;
  signOut: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    session: null,
    tokens: undefined,
  });

  const signIn = async (credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password,
      });

      if (error) throw error;

      if (!data.user || !data.session) {
        throw new Error('Sign in failed - no user or session returned');
      }

      const user: User = {
        id: data.user.id,
        email: data.user.email!,
        name: data.user.user_metadata?.name || data.user.email!.split('@')[0],
        role: data.user.user_metadata?.role || 'user',
        is_active: true,
        created_at: data.user.created_at,
        updated_at: data.user.updated_at || data.user.created_at,
        last_login: new Date().toISOString(),
      };

      const tokens: AuthTokens = {
        access_token: data.session.access_token,
        refresh_token: data.session.refresh_token,
        token_type: data.session.token_type || 'bearer',
        expires_in: data.session.expires_in || 3600,
      };

      setAuthState({
        user,
        loading: false,
        session: data.session,
        tokens,
      });

      // Store token in localStorage for API calls
      localStorage.setItem('auth_token', data.session.access_token);

      return { user, tokens };
    } catch (error: any) {
      console.error('Sign in error:', error);
      throw new Error(error.message || 'Sign in failed');
    }
  };

  const signUp = async (userData: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email: userData.email,
        password: userData.password,
        options: {
          data: {
            name: userData.name,
            role: 'user',
          },
        },
      });

      if (error) throw error;

      if (!data.user) {
        throw new Error('Sign up failed - no user returned');
      }

      // For sign up, user might need email confirmation
      // Handle both confirmed and unconfirmed cases
      const user: User = {
        id: data.user.id,
        email: data.user.email!,
        name: userData.name || data.user.email!.split('@')[0],
        role: 'user',
        is_active: !!data.user.email_confirmed_at,
        created_at: data.user.created_at,
        updated_at: data.user.updated_at || data.user.created_at,
      };

      let tokens: AuthTokens | undefined;

      if (data.session) {
        tokens = {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token,
          token_type: data.session.token_type || 'bearer',
          expires_in: data.session.expires_in || 3600,
        };

        setAuthState({
          user,
          loading: false,
          session: data.session,
          tokens,
        });

        // Store token in localStorage for API calls
        localStorage.setItem('auth_token', data.session.access_token);
      } else {
        // User needs email confirmation
        setAuthState({
          user: null,
          loading: false,
          session: null,
          tokens: undefined,
        });
      }

      return { 
        user, 
        tokens: tokens || {
          access_token: '',
          token_type: 'bearer',
          expires_in: 0,
        }
      };
    } catch (error: any) {
      console.error('Sign up error:', error);
      throw new Error(error.message || 'Sign up failed');
    }
  };

  const signOut = async (): Promise<void> => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;

      setAuthState({
        user: null,
        loading: false,
        session: null,
        tokens: undefined,
      });

      // Clear stored token
      localStorage.removeItem('auth_token');
    } catch (error: any) {
      console.error('Sign out error:', error);
      // Even if Supabase sign out fails, clear local state
      setAuthState({
        user: null,
        loading: false,
        session: null,
        tokens: undefined,
      });
      localStorage.removeItem('auth_token');
    }
  };

  const refreshAuth = async (): Promise<void> => {
    try {
      const { data, error } = await supabase.auth.getSession();
      
      if (error) throw error;

      if (data.session && data.session.user) {
        const user: User = {
          id: data.session.user.id,
          email: data.session.user.email!,
          name: data.session.user.user_metadata?.name || data.session.user.email!.split('@')[0],
          role: data.session.user.user_metadata?.role || 'user',
          is_active: true,
          created_at: data.session.user.created_at,
          updated_at: data.session.user.updated_at || data.session.user.created_at,
          last_login: data.session.user.last_sign_in_at || new Date().toISOString(),
        };

        const tokens: AuthTokens = {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token,
          token_type: data.session.token_type || 'bearer',
          expires_in: data.session.expires_in || 3600,
        };

        setAuthState({
          user,
          loading: false,
          session: data.session,
          tokens,
        });

        // Update stored token
        localStorage.setItem('auth_token', data.session.access_token);
      } else {
        setAuthState({
          user: null,
          loading: false,
          session: null,
          tokens: undefined,
        });
        localStorage.removeItem('auth_token');
      }
    } catch (error: any) {
      console.error('Auth refresh error:', error);
      setAuthState({
        user: null,
        loading: false,
        session: null,
        tokens: undefined,
      });
      localStorage.removeItem('auth_token');
    }
  };

  useEffect(() => {
    // Get initial session
    refreshAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event, session?.user?.email);
      
      if (session && session.user) {
        const user: User = {
          id: session.user.id,
          email: session.user.email!,
          name: session.user.user_metadata?.name || session.user.email!.split('@')[0],
          role: session.user.user_metadata?.role || 'user',
          is_active: true,
          created_at: session.user.created_at,
          updated_at: session.user.updated_at || session.user.created_at,
          last_login: session.user.last_sign_in_at || new Date().toISOString(),
        };

        const tokens: AuthTokens = {
          access_token: session.access_token,
          refresh_token: session.refresh_token,
          token_type: session.token_type || 'bearer',
          expires_in: session.expires_in || 3600,
        };

        setAuthState({
          user,
          loading: false,
          session,
          tokens,
        });

        localStorage.setItem('auth_token', session.access_token);
      } else {
        setAuthState({
          user: null,
          loading: false,
          session: null,
          tokens: undefined,
        });
        localStorage.removeItem('auth_token');
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const value: AuthContextType = {
    ...authState,
    signIn,
    signUp,
    signOut,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider; 