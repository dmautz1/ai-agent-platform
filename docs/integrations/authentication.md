# Authentication Integration

> **User management and security** - Complete authentication setup with Supabase Auth

## Overview

The AI Agent Template uses **Supabase Authentication** for comprehensive user management:

- **Multiple Authentication Methods** - Email/password, OAuth providers
- **JWT Token Security** - Secure API access with JSON Web Tokens
- **Row Level Security** - Database-level access control
- **Real-time Session Management** - Automatic token refresh and validation
- **Frontend Integration** - React context for authentication state

## Authentication Architecture

```
Frontend (React) ←→ Supabase Auth ←→ Backend (FastAPI) ←→ Database (RLS)
     ↓                    ↓                ↓                ↓
Context Provider      JWT Tokens      Token Validation   User Policies
Session State         Refresh          Middleware         Data Access
```

## Quick Setup

### 1. Supabase Auth Configuration

Authentication is automatically configured when you set up your Supabase project. No additional setup required for basic email/password authentication.

### 2. Environment Configuration

**Frontend** (`frontend/.env.local`):
```bash
VITE_SUPABASE_URL=your-supabase-project-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

**Backend** (`backend/.env`):
```bash
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
JWT_SECRET=your-32-character-secret-key
```

### 3. Create First User

```bash
cd frontend
npm run create-admin admin@example.com password123 "Admin User"
```

## Frontend Authentication

### Authentication Context

The template includes a comprehensive authentication context:

```typescript
// frontend/src/contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null
  session: Session | null
  signIn: (email: string, password: string) => Promise<AuthResponse>
  signUp: (email: string, password: string, metadata?: any) => Promise<AuthResponse>
  signOut: () => Promise<void>
  loading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)
```

### Using Authentication

```typescript
// In your React components
import { useAuth } from '@/contexts/AuthContext'

function MyComponent() {
  const { user, isAuthenticated, signIn, signOut } = useAuth()
  
  if (!isAuthenticated) {
    return <LoginForm onSignIn={signIn} />
  }
  
  return (
    <div>
      <p>Welcome, {user?.email}!</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}
```

### Protected Routes

Protect routes that require authentication:

```typescript
// frontend/src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return <div>Loading...</div>
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}
```

### Login Component

```typescript
// frontend/src/components/LoginForm.tsx
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { signIn } = useAuth()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const { error } = await signIn(email, password)
      if (error) {
        setError(error.message)
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Signing In...' : 'Sign In'}
      </button>
    </form>
  )
}
```

## Backend Authentication

### JWT Verification Middleware

The backend automatically validates JWT tokens:

```python
# backend/auth.py
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token and extract user information"""
    try:
        # Decode JWT token
        token = credentials.credentials
        secret = os.getenv("JWT_SECRET")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        # Extract user information
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from Supabase
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Protected Endpoints

Use authentication in your API endpoints:

```python
# In your agent endpoints
from auth import verify_token

@endpoint("/protected-endpoint", methods=["POST"], auth_required=True)
async def protected_endpoint(self, request_data: dict, user: dict):
    # User is automatically verified and available
    user_id = user["id"]
    user_email = user["email"]
    
    # Process request with authenticated user context
    return {"message": f"Hello {user_email}!"}
```

### Optional Authentication

For endpoints that can work with or without authentication:

```python
@endpoint("/optional-auth", methods=["GET"], auth_required=False)
async def optional_auth_endpoint(self, user: dict = None):
    if user:
        return {"message": f"Hello {user['email']}!", "authenticated": True}
    else:
        return {"message": "Hello anonymous user!", "authenticated": False}
```

## User Management

### Creating Users Programmatically

```python
# backend/user_management.py
from supabase import create_client

async def create_user(email: str, password: str, metadata: dict = None):
    """Create a new user account"""
    supabase = get_supabase_client()
    
    try:
        result = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Skip email confirmation
            "user_metadata": metadata or {}
        })
        
        return result.user
        
    except Exception as e:
        raise ValueError(f"Failed to create user: {str(e)}")
```

### User Roles and Permissions

Add role-based access control:

```python
# Add roles to user metadata
metadata = {
    "name": "John Doe",
    "role": "admin",  # or "user", "moderator", etc.
    "permissions": ["read", "write", "delete"]
}

# Check roles in endpoints
@endpoint("/admin-only", methods=["POST"], auth_required=True)
async def admin_only_endpoint(self, request_data: dict, user: dict):
    user_role = user.get("user_metadata", {}).get("role")
    
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Admin-only logic here
    return {"message": "Admin access granted"}
```

## Advanced Authentication Features

### Password Reset

```typescript
// Frontend password reset
import { supabase } from '@/lib/supabase'

const resetPassword = async (email: string) => {
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`
  })
  
  if (error) throw error
}
```

### OAuth Providers

Configure OAuth providers in Supabase dashboard:

```typescript
// Google OAuth sign-in
const signInWithGoogle = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/dashboard`
    }
  })
  
  if (error) throw error
}
```

### Session Management

```typescript
// Automatic session refresh
useEffect(() => {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    (event, session) => {
      if (event === 'SIGNED_IN') {
        setUser(session?.user ?? null)
        setSession(session)
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setSession(null)
      } else if (event === 'TOKEN_REFRESHED') {
        setSession(session)
      }
    }
  )
  
  return () => subscription.unsubscribe()
}, [])
```

## Security Best Practices

### Frontend Security

1. **Never store sensitive data** in localStorage or sessionStorage
2. **Use HTTPS only** in production
3. **Validate user input** before sending to backend
4. **Handle token expiration** gracefully
5. **Clear tokens on logout** completely

### Backend Security

1. **Validate all JWT tokens** on protected endpoints
2. **Use Row Level Security** for database access
3. **Implement rate limiting** on auth endpoints
4. **Log authentication events** for monitoring
5. **Use strong JWT secrets** (32+ characters)

### Database Security (RLS)

```sql
-- Example RLS policies
CREATE POLICY "Users can only see own data" ON jobs
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Admins can see all data" ON jobs
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'admin'
    );
```

## Troubleshooting

### Common Issues

**Token Validation Errors:**
```bash
# Check JWT secret configuration
echo $JWT_SECRET

# Verify token format
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me
```

**Supabase Connection Issues:**
```bash
# Test Supabase connection
curl "$SUPABASE_URL/rest/v1/" \
     -H "apikey: $SUPABASE_ANON_KEY"
```

**CORS Issues:**
```python
# Backend CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Debugging Authentication

```typescript
// Frontend debugging
const debugAuth = async () => {
  const { data: { session } } = await supabase.auth.getSession()
  console.log('Current session:', session)
  
  const { data: { user } } = await supabase.auth.getUser()
  console.log('Current user:', user)
}
```

```python
# Backend debugging
import logging

logger = logging.getLogger(__name__)

async def debug_token(token: str):
    try:
        payload = jwt.decode(token, verify=False)  # Don't verify for debugging
        logger.info(f"Token payload: {payload}")
    except Exception as e:
        logger.error(f"Token decode error: {e}")
```

---

**Next Steps:**
- **[Supabase Database](supabase.md)** - Database integration details
- **[API Reference](../development/api-reference.md)** - Authentication endpoints
- **[Agent Development](../development/agent-development.md)** - Build authenticated agents 