#!/usr/bin/env node

/**
 * Create Admin User Script
 * 
 * This script creates an initial admin user in Supabase.
 * Run this after setting up your Supabase project.
 * 
 * Usage:
 *   node scripts/create-admin-user.js <email> <password> [name]
 * 
 * Example:
 *   node scripts/create-admin-user.js admin@example.com mypassword123 "Admin User"
 */

import { createClient } from '@supabase/supabase-js';
import { config } from 'dotenv';

// Load environment variables
config({ path: '.env.local' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceRoleKey) {
  console.error('❌ Missing required environment variables:');
  console.error('   VITE_SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  console.error('');
  console.error('Please add these to your .env.local file');
  process.exit(1);
}

// Create Supabase client with service role key for admin operations
const supabase = createClient(supabaseUrl, supabaseServiceRoleKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

async function createAdminUser(email, password, name = null) {
  try {
    console.log('🔐 Creating admin user...');
    
    const { data, error } = await supabase.auth.admin.createUser({
      email: email,
      password: password,
      user_metadata: {
        name: name,
        role: 'admin'
      },
      email_confirm: true // Skip email confirmation for admin setup
    });

    if (error) {
      throw error;
    }

    console.log('✅ Admin user created successfully!');
    console.log(`   Email: ${email}`);
    console.log(`   User ID: ${data.user.id}`);
    if (name) {
      console.log(`   Name: ${name}`);
    }
    console.log('');
    console.log('🎉 You can now sign in to the application!');
    
  } catch (error) {
    console.error('❌ Failed to create admin user:', error.message);
    process.exit(1);
  }
}

// Parse command line arguments
const args = process.argv.slice(2);

if (args.length < 2) {
  console.log('📋 Create Admin User Script');
  console.log('');
  console.log('Usage:');
  console.log('  node scripts/create-admin-user.js <email> <password> [name]');
  console.log('');
  console.log('Examples:');
  console.log('  node scripts/create-admin-user.js admin@example.com mypassword123');
  console.log('  node scripts/create-admin-user.js admin@example.com mypassword123 "Admin User"');
  console.log('');
  console.log('Requirements:');
  console.log('  - Valid email address');
  console.log('  - Password (minimum 6 characters)');
  console.log('  - Name (optional)');
  console.log('');
  console.log('Environment Variables Required:');
  console.log('  - VITE_SUPABASE_URL');
  console.log('  - SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const [email, password, name] = args;

// Basic validation
if (!email.includes('@')) {
  console.error('❌ Invalid email address');
  process.exit(1);
}

if (password.length < 6) {
  console.error('❌ Password must be at least 6 characters long');
  process.exit(1);
}

// Create the admin user
createAdminUser(email, password, name); 