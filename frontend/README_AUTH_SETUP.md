# Authentication Setup Guide

This guide explains how to set up authentication for the AI Agent Template using Supabase with manual user management.

## Overview

This template uses a **secure, manual user management approach** instead of public sign-up registration. This provides:

- ✅ **Better security** - No unauthorized account creation
- ✅ **Simpler setup** - No email configuration required
- ✅ **Developer-friendly** - Perfect for team environments
- ✅ **Full control** - Admins decide who gets access

## Quick Setup

### 1. Supabase Project Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **Settings** → **API** in your Supabase dashboard
3. Copy your **Project URL** and **anon public key**
4. Go to **Settings** → **API** → **Service Role** and copy the **service_role key**

### 2. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.local.example .env.local
   ```

2. Update `.env.local` with your Supabase credentials:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_SUPABASE_URL=your-supabase-project-url
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   ```

### 3. Create Your First Admin User

Use the built-in script to create your first admin user:

```bash
# Basic usage
npm run create-admin admin@example.com mypassword123

# With user name
npm run create-admin admin@example.com mypassword123 "Admin User"
```

The script will:
- Create a new user in Supabase
- Skip email verification (immediate access)
- Set admin role in user metadata
- Provide confirmation of successful creation

### 4. Start the Application

```bash
npm run dev
```

Navigate to the application and sign in with your admin credentials!

## User Management

### Adding New Users

You have several options to add new users:

#### Option 1: Supabase Dashboard (Recommended)
1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Users**
3. Click **Add User**
4. Fill in email, password, and optionally name in user metadata
5. Toggle **Email Confirmed** to skip verification

#### Option 2: Admin Script
```bash
npm run create-admin new-user@example.com password123 "User Name"
```

#### Option 3: SQL Query
Execute in Supabase SQL Editor:
```sql
-- Insert new user (replace with actual values)
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  created_at,
  updated_at,
  raw_user_meta_data,
  raw_app_meta_data
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'user@example.com',
  crypt('password123', gen_salt('bf')),
  now(),
  now(),
  now(),
  '{"name": "User Name"}',
  '{}'
);
```

### Removing Users

#### Via Supabase Dashboard:
1. Go to **Authentication** → **Users**
2. Find the user and click the delete icon

#### Via SQL:
```sql
DELETE FROM auth.users WHERE email = 'user@example.com';
```

## Security Considerations

### Why No Public Sign-up?

Public sign-up forms introduce several challenges:
- **Security risks** - Anyone can create accounts
- **Spam prevention** - Need CAPTCHA and rate limiting
- **Email verification** - Requires SMTP configuration
- **Moderation overhead** - Managing unwanted accounts

### Best Practices

1. **Use strong passwords** - Minimum 12 characters recommended
2. **Regular access review** - Remove unused accounts periodically
3. **Role-based access** - Use user metadata to assign roles
4. **Monitor usage** - Check Supabase logs for suspicious activity

## Development Workflow

### Local Development
1. Set up local environment variables
2. Create test users as needed
3. Use the same credentials across team members

### Production Deployment
1. Update environment variables in your hosting platform
2. Create production admin users
3. Remove or change default test credentials

## Troubleshooting

### Common Issues

**Script fails with "Missing environment variables"**
- Ensure `.env.local` exists and contains all required variables
- Check that variable names match exactly (case-sensitive)

**"User already exists" error**
- The email is already registered in Supabase
- Use a different email or delete the existing user first

**Cannot sign in after creating user**
- Verify the email and password match exactly
- Check that `email_confirmed_at` is set (not null)
- Ensure the user appears in Supabase Authentication → Users

**Script shows "command not found"**
- Run `npm install` first to install dependencies
- Ensure you're in the frontend directory

### Getting Help

1. Check Supabase project logs in the dashboard
2. Verify environment variables are correct
3. Test authentication directly in Supabase dashboard
4. Review this documentation for missed steps

## Advanced Configuration

### Custom User Roles

Add roles to user metadata during creation:

```javascript
// In the create-admin script or Supabase dashboard
user_metadata: {
  name: "User Name",
  role: "admin",        // or "user", "manager", etc.
  department: "IT",
  permissions: ["read", "write"]
}
```

### Password Policies

Configure in Supabase dashboard under **Authentication** → **Settings**:
- Minimum password length
- Require special characters
- Password strength requirements

### Session Configuration

Adjust session settings in **Authentication** → **Settings**:
- Session timeout duration
- Refresh token expiry
- Multi-device sessions

## Migration from Public Sign-up

If you previously had public sign-up enabled:

1. **Export existing users** from Supabase dashboard
2. **Disable sign-up** in Authentication settings
3. **Update frontend** to remove sign-up forms
4. **Communicate changes** to existing users
5. **Set up manual user creation** process

This ensures a smooth transition to the more secure manual approach. 