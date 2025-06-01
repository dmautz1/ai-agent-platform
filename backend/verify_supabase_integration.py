#!/usr/bin/env python3
"""
Quick Supabase integration verification script.

This script performs basic connectivity and operation tests to verify
that Supabase integration is working correctly. It's designed to be
run as a quick health check without requiring the full test suite.
"""

import sys
import os
import asyncio
import uuid
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def verify_supabase_integration():
    """Perform basic Supabase integration verification."""
    print("🔍 Supabase Integration Verification")
    print("=" * 40)
    
    try:
        # Import required modules
        from database import get_database_operations, check_database_health
        from config.environment import get_settings, validate_required_settings
        
        print("✅ Modules imported successfully")
        
        # Validate environment
        try:
            validate_required_settings()
            settings = get_settings()
            print(f"✅ Environment configuration loaded ({settings.environment})")
        except Exception as e:
            print(f"❌ Environment validation failed: {e}")
            return False
        
        # Test database health
        try:
            health = await check_database_health()
            if health["status"] == "healthy":
                print(f"✅ Database health check passed ({health['connection_time_ms']}ms)")
            else:
                print(f"❌ Database health check failed: {health.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Database health check error: {e}")
            return False
        
        # Test basic operations
        try:
            db_ops = get_database_operations()
            print("✅ Database operations instance created")
            
            # Test job creation
            test_job_data = {
                "user_id": str(uuid.uuid4()),
                "type": "verification_test",
                "status": "pending",
                "data": {
                    "test": True,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
            
            created_job = await db_ops.create_job(test_job_data)
            print(f"✅ Job creation successful (ID: {created_job['id'][:8]}...)")
            
            # Test job retrieval
            retrieved_job = await db_ops.get_job(created_job["id"])
            if retrieved_job and retrieved_job["id"] == created_job["id"]:
                print("✅ Job retrieval successful")
            else:
                print("❌ Job retrieval failed")
                return False
            
            # Test job update
            updated_job = await db_ops.update_job_status(
                created_job["id"], 
                "completed",
                result={"verification": "success"}
            )
            if updated_job["status"] == "completed":
                print("✅ Job status update successful")
            else:
                print("❌ Job status update failed")
                return False
            
            # Test job deletion (cleanup)
            deleted = await db_ops.delete_job(created_job["id"])
            if deleted:
                print("✅ Job deletion successful")
            else:
                print("❌ Job deletion failed")
                return False
                
        except Exception as e:
            print(f"❌ Database operation error: {e}")
            return False
        
        print("\n🎉 All verification tests passed!")
        print("   Supabase integration is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main entry point."""
    try:
        # Check if we're in the right directory
        if not (Path.cwd() / "backend").exists():
            backend_path = Path.cwd() / "backend"
            if backend_path.exists():
                os.chdir(backend_path)
            else:
                print("❌ Please run this script from the project root directory")
                sys.exit(1)
        
        # Run verification
        success = asyncio.run(verify_supabase_integration())
        
        if success:
            print("\n✅ Verification completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Verification failed. Check the errors above.")
            print("   Common issues:")
            print("   - Missing environment variables (SUPABASE_URL, SUPABASE_KEY)")
            print("   - Database not accessible")
            print("   - Missing database migrations")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Script error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 