import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { SignInForm } from '../../components/SignInForm'
import { AuthProvider } from '../../contexts/AuthContext'
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

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('SignInForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSupabaseClient.auth.getUser.mockResolvedValue({
      data: { user: null },
      error: null
    })
    mockSupabaseClient.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null
    })
    mockSupabaseClient.auth.onAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } }
    })
  })

  it('renders email and password fields', () => {
    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    const emailField = screen.getByRole('textbox', { name: /email/i })
    await user.type(emailField, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument()
    })
  })

  it('successfully signs in with valid credentials', async () => {
    const user = userEvent.setup()
    
    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: {
        user: { id: 'user123', email: 'test@example.com' },
        session: { access_token: 'token123' }
      },
      error: null
    })

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Fill in valid credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')

    // Submit form
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('handles authentication errors gracefully', async () => {
    const user = userEvent.setup()
    
    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: 'Invalid credentials' }
    })

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Fill in credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')

    // Submit form
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during sign in', async () => {
    const user = userEvent.setup()
    
    // Mock delayed response
    mockSupabaseClient.auth.signInWithPassword.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ 
          data: { user: { id: 'user123' }, session: { access_token: 'token' } }, 
          error: null 
        }), 100)
      )
    )

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Fill in credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')

    // Submit form
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
  })

  it('clears errors when user starts typing', async () => {
    const user = userEvent.setup()
    
    mockSupabaseClient.auth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: 'Invalid credentials' }
    })

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Trigger error by submitting invalid credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })

    // Start typing in email field
    await user.clear(screen.getByRole('textbox', { name: /email/i }))
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'new@example.com')

    // Error should be cleared
    expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument()
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    const passwordField = screen.getByLabelText(/password/i)
    const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i })

    // Initially password should be hidden
    expect(passwordField).toHaveAttribute('type', 'password')

    // Click toggle to show password
    await user.click(toggleButton)
    expect(passwordField).toHaveAttribute('type', 'text')

    // Click toggle again to hide password
    await user.click(toggleButton)
    expect(passwordField).toHaveAttribute('type', 'password')
  })

  it('redirects to dashboard if user is already authenticated', async () => {
    mockSupabaseClient.auth.getUser.mockResolvedValue({
      data: { user: { id: 'user123', email: 'test@example.com' } },
      error: null
    })

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('handles network errors appropriately', async () => {
    const user = userEvent.setup()
    
    mockSupabaseClient.auth.signInWithPassword.mockRejectedValue(
      new Error('Network error')
    )

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Fill in credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')

    // Submit form
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    })
  })

  it('disables form during submission', async () => {
    const user = userEvent.setup()
    
    // Mock delayed response
    mockSupabaseClient.auth.signInWithPassword.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ 
          data: { user: { id: 'user123' }, session: { access_token: 'token' } }, 
          error: null 
        }), 100)
      )
    )

    render(
      <TestWrapper>
        <SignInForm />
      </TestWrapper>
    )

    // Fill in credentials
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')

    // Submit form
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    // Form fields should be disabled during submission
    expect(screen.getByRole('textbox', { name: /email/i })).toBeDisabled()
    expect(screen.getByLabelText(/password/i)).toBeDisabled()
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
  })
}) 