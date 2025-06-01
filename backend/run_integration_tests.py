#!/usr/bin/env python3
"""
Integration test runner for Supabase database operations.

This script provides an easy way to run integration tests with proper
environment configuration and safety checks.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_environment():
    """Set up the environment for testing."""
    # Add the backend directory to Python path
    backend_dir = Path(__file__).parent
    sys.path.insert(0, str(backend_dir))
    
    # Set default environment variables for testing
    test_env = {
        "ENVIRONMENT": "testing",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": str(backend_dir)
    }
    
    # Load test environment file if it exists
    test_env_file = backend_dir / ".env.test"
    if test_env_file.exists():
        print(f"Loading test environment from: {test_env_file}")
        with open(test_env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        test_env[key.strip()] = value.strip()
    else:
        print(f"⚠️  Test environment file not found: {test_env_file}")
        print(f"   Copy {backend_dir}/test_config_example.env to .env.test")
        print(f"   and update with your test Supabase credentials.")
        return False
    
    # Update environment
    os.environ.update(test_env)
    
    # Verify required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Safety check - ensure we're not in production
    if os.environ.get("ENVIRONMENT") == "production":
        print("❌ Cannot run integration tests in production environment!")
        return False
    
    print("✅ Environment setup complete")
    print(f"   Supabase URL: {os.environ.get('SUPABASE_URL')}")
    print(f"   Environment: {os.environ.get('ENVIRONMENT')}")
    
    return True

def run_tests(test_pattern=None, verbose=True, fail_fast=False):
    """Run the integration tests."""
    backend_dir = Path(__file__).parent
    test_dir = backend_dir / "tests" / "integration"
    
    if not test_dir.exists():
        print(f"❌ Integration test directory not found: {test_dir}")
        return False
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if fail_fast:
        cmd.append("-x")
    
    # Add test path
    if test_pattern:
        cmd.append(str(test_dir / f"test_supabase_integration.py::{test_pattern}"))
    else:
        cmd.append(str(test_dir))
    
    # Add additional pytest options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--durations=10",  # Show 10 slowest tests
        "--strict-markers",  # Strict marker checking
        "-W", "ignore::DeprecationWarning"  # Ignore deprecation warnings
    ])
    
    print(f"🧪 Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=backend_dir, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Supabase integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run all integration tests
  %(prog)s --test connectivity               # Run connectivity tests only
  %(prog)s --test TestJobCRUDOperations      # Run CRUD operation tests
  %(prog)s --test test_database_health_check # Run specific test
  %(prog)s --fail-fast                       # Stop on first failure
  %(prog)s --quiet                           # Less verbose output
        """
    )
    
    parser.add_argument(
        "--test", "-t",
        help="Specific test class or method to run"
    )
    
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first test failure"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Less verbose output"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Only check environment setup, don't run tests"
    )
    
    args = parser.parse_args()
    
    print("🚀 Supabase Integration Test Runner")
    print("=" * 40)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Please check your configuration.")
        sys.exit(1)
    
    if args.check_env:
        print("\n✅ Environment check passed. Ready to run tests.")
        sys.exit(0)
    
    print("\n🧪 Starting integration tests...")
    
    # Run tests
    success = run_tests(
        test_pattern=args.test,
        verbose=not args.quiet,
        fail_fast=args.fail_fast
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 