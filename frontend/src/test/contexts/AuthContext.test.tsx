import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../../contexts/AuthContext'
import { mockSupabaseClient } from '../utils'

// Mock Supabase
vi.mock('../../lib/supabase', () => ({
  supabase: mockSupabaseClient,
}))

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Test component to access auth context
const TestComponent = () => {
  const { user, loading, signIn, signOut } = useAuth()
  
  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? user.email : 'No User'}</div>
      <button
        onClick={() => signIn({ email: 'test@example.com', password: 'password123', remember_me: false })}
      >
        Sign In
      </button>
      <button onClick={() => signOut()}>Sign Out</button>
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
    mockSupabaseClient.auth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } }
    })
  })

  it('provides initial loading state', () => {
    mockSupabaseClient.auth.getSession.mockResolvedValue({
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
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
      error: null
    })

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })
  })

  it('handles session retrieval errors', async () => {
    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: { message: 'Session error' }
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
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: mockUser, session: mockSession },
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
      expect(mockSupabaseClient.auth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('handles sign in errors', async () => {
    const user = userEvent.setup()

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: 'Invalid credentials' }
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
    
    await expect(user.click(signInButton)).rejects.toThrow('Invalid credentials')
  })

  it('successfully signs out user', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
      error: null
    })

    mockSupabaseClient.auth.signOut.mockResolvedValue({
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
      expect(mockSupabaseClient.auth.signOut).toHaveBeenCalled()
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
      expect(mockNavigate).toHaveBeenCalledWith('/auth')
    })
  })

  it('handles sign out errors', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
      error: null
    })

    mockSupabaseClient.auth.signOut.mockResolvedValue({
      error: { message: 'Sign out error' }
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
    
    await expect(user.click(signOutButton)).rejects.toThrow('Sign out error')
  })

  it('handles auth state changes', async () => {
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    let authStateChangeCallback: any

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockSupabaseClient.auth.onAuthStateChange.mockImplementation((callback) => {
      authStateChangeCallback = callback
      return { data: { subscription: { unsubscribe: vi.fn() } } }
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
      authStateChangeCallback('SIGNED_IN', mockSession)
    })

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    // Simulate auth state change (user signs out)
    act(() => {
      authStateChangeCallback('SIGNED_OUT', null)
    })

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
    })
  })

  it('unsubscribes from auth state changes on unmount', async () => {
    const mockUnsubscribe = vi.fn()

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    mockSupabaseClient.auth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: mockUnsubscribe } }
    })

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
    const mockUser = { id: 'user123', email: 'test@example.com' }
    const mockSession = { access_token: 'token123', user: mockUser }

    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })

    // Mock delayed sign in response
    mockSupabaseClient.auth.signInWithPassword.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          data: { user: mockUser, session: mockSession },
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
    await user.click(signInButton)

    // Should show loading during sign in
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading')

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })
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