#!/usr/bin/env python3
"""
Diagnostic script to check Veo 3.1 setup and identify potential issues.
Run this before attempting video generation to verify everything is configured correctly.
"""

import os
import sys
import json
from datetime import datetime

def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = ".env"
    if os.path.exists(env_path):
        print("Loading environment from .env file...")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key not in os.environ:
                            os.environ[key] = value

def check_environment():
    print("=" * 60)
    print("Veo 3.1 Diagnostic Tool")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Load .env if exists
    load_env()

    issues = []
    
    # Check Python version
    print("1. Python Version")
    py_version = sys.version.replace('\n', ' ')
    print(f"   Current: {py_version}")
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    print("   ✓ OK\n")
    
    # Check required packages
    print("2. Required Packages")
    packages = [
        ('google.genai', 'google-genai'),
        ('google.cloud.storage', 'google-cloud-storage'),
        ('flask', 'flask'),
        ('sqlite3', 'sqlite3')
    ]
    
    for mod_name, pkg_name in packages:
        try:
            if mod_name == 'sqlite3':
                import sqlite3
                print(f"   {pkg_name}: {sqlite3.sqlite_version}")
            else:
                mod = __import__(mod_name, fromlist=['__version__'])
                version = getattr(mod, '__version__', 'unknown')
                print(f"   {pkg_name}: {version}")
        except ImportError as e:
            print(f"   {pkg_name}: NOT INSTALLED ({e})")
            issues.append(f"Missing package: {pkg_name}")
    print()
    
    # Check environment variables
    print("3. Environment Variables")
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_CLOUD_LOCATION',
        'ADMIN_API_KEY',
        'ADMIN_EMAIL',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_KEY',
        'FLASK_SECRET_KEY'
    ]
    
    optional_vars = [
        'RUNPOD_ENDPOINT_ID',
        'RUNPOD_API_KEY'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
                display = value[:10] + '...' + value[-5:] if len(value) > 15 else '***'
            else:
                display = value
            print(f"   {var}: {display}")
        else:
            print(f"   {var}: NOT SET")
            issues.append(f"Missing env var: {var}")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            display = value[:10] + '...' + value[-5:] if len(value) > 15 else value
            print(f"   {var}: {display}")
        else:
            print(f"   {var}: (optional)")
    print()
    
    # Check for config files
    print("4. Configuration Files")
    config_files = ['.env', 'service_account.json']
    for cf in config_files:
        if os.path.exists(cf):
            print(f"   {cf}: ✓ Found")
        else:
            print(f"   {cf}: Missing")
            if cf == 'service_account.json':
                issues.append("service_account.json not found - needed for Vertex AI")
    print()
    
    # Test GCS access
    print("5. Storage Service Test")
    try:
        from storage_service import StorageService
        ss = StorageService()
        print("   ✓ StorageService initialized")
        
        # Try to list buckets (read-only test)
        try:
            buckets = list(ss.client.list_buckets(max_results=1))
            if buckets:
                print(f"   ✓ Can access GCS (bucket: {buckets[0].name})")
            else:
                print("   ⚠ No buckets found (may be OK)")
        except Exception as e:
            print(f"   ✗ Cannot list buckets: {e}")
            issues.append(f"GCS access error: {e}")
    except Exception as e:
        print(f"   ✗ StorageService failed: {e}")
        issues.append(f"StorageService error: {e}")
    print()
    
    # Test Veo client setup
    print("6. Veo Client Setup Test")
    try:
        from vertex_ai_veo_client import VertexAIVeoClient
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if project_id:
            client = VertexAIVeoClient(project_id, location)
            print("   ✓ Veo client created")
            print(f"   ✓ SDK version: {client.sdk_version}")
        else:
            print("   ⚠ Cannot test without project ID")
    except Exception as e:
        print(f"   ✗ Veo client failed: {e}")
        issues.append(f"Veo client error: {e}")
    print()
    
    # Check database
    print("7. Job Queue Database")
    try:
        import sqlite3
        db_path = "jobs.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            print(f"   ✓ jobs.db exists with {count} jobs")
            
            cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            for status, cnt in cursor.fetchall():
                print(f"     - {status}: {cnt}")
            
            conn.close()
        else:
            print("   ⚠ jobs.db not yet created (will be on first job)")
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        issues.append(f"Database error: {e}")
    print()
    
    # Summary
    print("=" * 60)
    if not issues:
        print("✅ All checks passed! System is ready.")
        print("\nNext steps:")
        print("1. Start the server: python web_app.py")
        print("2. Use the API with model='veo3.1'")
        print("3. Check logs for detailed operation info")
    else:
        print(f"❌ Found {len(issues)} issue(s):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\nPlease fix the issues above before running the API.")
    print("=" * 60)

if __name__ == "__main__":
    check_environment()

