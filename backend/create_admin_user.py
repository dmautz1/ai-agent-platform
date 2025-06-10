#!/usr/bin/env python3
"""
Create Admin User Script

This script creates an initial admin user in Supabase using the service role key.
This should be run from the backend where the service role key is securely stored.

Usage:
    python create_admin_user.py <email> <password> [name]

Example:
    python create_admin_user.py admin@example.com mypassword123 "Admin User"
"""

import sys
import os
import asyncio
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

def get_supabase_admin_client() -> Client:
    """Create Supabase client with service role key for admin operations."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL")
        print("   SUPABASE_SERVICE_KEY") 
        print("")
        print("Please add these to your backend/.env file")
        sys.exit(1)
    
    return create_client(supabase_url, supabase_service_key)

async def create_admin_user(email: str, password: str, name: Optional[str] = None):
    """Create an admin user in Supabase."""
    try:
        print("🔐 Creating admin user...")
        
        supabase = get_supabase_admin_client()
        
        # Create user with admin role
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "user_metadata": {
                "name": name or email.split("@")[0],
                "role": "admin"
            },
            "email_confirm": True  # Skip email confirmation for admin setup
        })
        
        if response.user:
            print("✅ Admin user created successfully!")
            print(f"   Email: {email}")
            print(f"   User ID: {response.user.id}")
            if name:
                print(f"   Name: {name}")
            print("")
            print("🎉 You can now sign in to the application!")
        else:
            raise Exception("Failed to create user - no user returned")
            
    except Exception as error:
        print(f"❌ Failed to create admin user: {str(error)}")
        sys.exit(1)

def main():
    """Main function to parse arguments and create admin user."""
    args = sys.argv[1:]
    
    if len(args) < 2:
        print("📋 Create Admin User Script")
        print("")
        print("Usage:")
        print("  python create_admin_user.py <email> <password> [name]")
        print("")
        print("Examples:")
        print("  python create_admin_user.py admin@example.com mypassword123")
        print("  python create_admin_user.py admin@example.com mypassword123 \"Admin User\"")
        print("")
        print("Requirements:")
        print("  - Valid email address")
        print("  - Password (minimum 6 characters)")
        print("  - Name (optional)")
        print("")
        print("Environment Variables Required:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    email = args[0]
    password = args[1]
    name = args[2] if len(args) > 2 else None
    
    # Basic validation
    if "@" not in email:
        print("❌ Invalid email address")
        sys.exit(1)
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters long")
        sys.exit(1)
    
    # Create the admin user
    asyncio.run(create_admin_user(email, password, name))

if __name__ == "__main__":
    main() 