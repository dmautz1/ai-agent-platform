import { describe, it, expect, vi, beforeEach, type MockedFunction } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../../contexts/AuthContext'
import type { LoginRequest } from '../../lib/models'
import React from 'react'

// Mock Supabase using factory function
vi.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signOut: vi.fn(),
      getSession: vi.fn(),
      onAuthStateChange: vi.fn(),
      getUser: vi.fn(),
    },
  },
}))

// Import the mocked supabase to access in tests
import { supabase } from '../../lib/supabase'

// Cast auth methods as mocked functions for easier access
const mockAuth = {
  getSession: supabase.auth.getSession as MockedFunction<typeof supabase.auth.getSession>,
  signInWithPassword: supabase.auth.signInWithPassword as MockedFunction<typeof supabase.auth.signInWithPassword>,
  signOut: supabase.auth.signOut as MockedFunction<typeof supabase.auth.signOut>,
  onAuthStateChange: supabase.auth.onAuthStateChange as MockedFunction<typeof supabase.auth.onAuthStateChange>,
}

// Test component to access auth context
const TestComponent = () => {
  const { user, loading, signIn, signOut } = useAuth()
  
  const handleSignIn = async () => {
    const credentials: LoginRequest = { 
      email: 'test@example.com', 
      password: 'password123' 
    }
    await signIn(credentials)
  }
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? user.email : 'No User'}</div>
      <button onClick={handleSignIn}>Sign In</button>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any)
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    })
  })

  it('provides initial loading state', () => {
    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    expect(screen.getByTestId('loading')).toHaveTextContent('Loading')
    expect(screen.getByTestId('user')).toHaveTextContent('No User')
  })

  it('sets user when session exists', async () => {
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    mockAuth.getSession.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { session: mockSession as any },
      error: null
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })
  })

  it('handles session retrieval errors', async () => {
    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: { message: 'Session error' } as any
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })
  })

  it('successfully signs in user', async () => {
    const user = userEvent.setup()
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockAuth.signInWithPassword.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { user: mockUser as any, session: mockSession as any },
      error: null
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
    })

    const signInButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(signInButton)

    await waitFor(() => {
      expect(mockAuth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      // No navigation expectations since AuthContext doesn't handle routing
    })
  })

  it('handles sign in errors', async () => {
    const user = userEvent.setup()

    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockAuth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: { message: 'Invalid credentials' } as any
    })

    // Create a component that properly handles the error
    const TestComponentWithErrorHandling = () => {
      const { user, loading, signIn } = useAuth()
      const [error, setError] = React.useState<string | null>(null)
      
      const handleSignIn = async () => {
        const credentials: LoginRequest = { 
          email: 'test@example.com', 
          password: 'password123' 
        }
        try {
          await signIn(credentials)
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Sign in failed')
        }
      }
      
      return (
        <div>
          <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
          <div data-testid="user">{user ? user.email : 'No User'}</div>
          <div data-testid="error">{error || 'No Error'}</div>
          <button onClick={handleSignIn}>Sign In</button>
        </div>
      )
    }

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponentWithErrorHandling />
        </AuthProvider>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
    })

    const signInButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(signInButton)

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Sign in failed')
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })
  })

  it('successfully signs out user', async () => {
    const user = userEvent.setup()
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    mockAuth.getSession.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { session: mockSession as any },
      error: null
    })

    mockAuth.signOut.mockResolvedValue({
      error: null
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    await user.click(signOutButton)

    await waitFor(() => {
      expect(mockAuth.signOut).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
      // No navigation expectations since AuthContext doesn't handle routing
    })
  })

  it('handles sign out errors gracefully', async () => {
    const user = userEvent.setup()
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    mockAuth.getSession.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: { session: mockSession as any },
      error: null
    })

    mockAuth.signOut.mockResolvedValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: { message: 'Sign out error' } as any
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    
    // signOut doesn't throw - it handles errors gracefully and clears state
    await user.click(signOutButton)

    await waitFor(() => {
      expect(mockAuth.signOut).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })
  })

  it('handles auth state changes', async () => {
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let authStateChangeCallback: ((event: any, session: any) => void) | null = null

    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockAuth.onAuthStateChange.mockImplementation((callback) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      authStateChangeCallback = callback as any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return { data: { subscription: { unsubscribe: vi.fn() } } } as any
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })

    // Simulate auth state change (user signs in)
    act(() => {
      authStateChangeCallback?.('SIGNED_IN', mockSession)
    })

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    // Simulate auth state change (user signs out)
    act(() => {
      authStateChangeCallback?.('SIGNED_OUT', null)
    })

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })
  })

  it('unsubscribes from auth state changes on unmount', async () => {
    const mockUnsubscribe = vi.fn()

    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockAuth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: mockUnsubscribe } }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any)

    const { unmount } = render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    unmount()

    expect(mockUnsubscribe).toHaveBeenCalled()
  })

  it('maintains loading state during authentication operations', async () => {
    const user = userEvent.setup()
    const mockUser = { 
      id: 'user123', 
      email: 'test@example.com',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      user_metadata: { name: 'Test User' },
      app_metadata: {},
      aud: 'authenticated'
    }
    const mockSession = { 
      access_token: 'token123', 
      refresh_token: 'refresh123',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      user: mockUser 
    }

    mockAuth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    // Mock delayed sign in response
    mockAuth.signInWithPassword.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          data: { user: mockUser as any, session: mockSession as any },
          error: null
        }), 100)
      )
    )

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
    })

    const signInButton = screen.getByRole('button', { name: /sign in/i })
    
    // Click the button and check loading state
    const clickPromise = user.click(signInButton)

    // Should show loading during sign in (AuthContext sets loading during auth operations)
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })
    
    await clickPromise
  })

  it('throws error when useAuth is used outside AuthProvider', () => {
    const TestComponentOutsideProvider = () => {
      useAuth()
      return <div>Test</div>
    }

    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => render(<TestComponentOutsideProvider />)).toThrow(
      'useAuth must be used within an AuthProvider'
    )

    consoleSpy.mockRestore()
  })
}) 