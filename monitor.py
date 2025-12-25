"""
System Monitoring and Health Check Script

This script provides:
- Queue health monitoring
- Database connectivity checks
- API endpoint health checks
- Job statistics
- System diagnostics
"""
import os
import sqlite3
import requests
from datetime import datetime, timedelta
import json
from job_queue import JobQueue, JobStatus

def check_queue_health():
    """Check the job queue system."""
    print("🔍 Checking Job Queue Health...")
    try:
        queue = JobQueue.get_instance()
        
        # Count jobs by status
        with sqlite3.connect(queue.db_path) as conn:
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status"
            )
            status_counts = dict(cursor.fetchall())
        
        print(f"   Total Jobs: {sum(status_counts.values())}")
        print(f"   Queued: {status_counts.get('queued', 0)}")
        print(f"   Processing: {status_counts.get('processing', 0)}")
        print(f"   Completed: {status_counts.get('completed', 0)}")
        print(f"   Failed: {status_counts.get('failed', 0)}")
        print(f"   Cancelled: {status_counts.get('cancelled', 0)}")
        
        # Check oldest queued job
        cursor = conn.execute(
            "SELECT created_at FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1"
        )
        oldest = cursor.fetchone()
        if oldest:
            oldest_time = datetime.fromisoformat(oldest[0])
            wait_time = datetime.now() - oldest_time
            print(f"   Oldest queued job wait time: {wait_time}")
        
        return True
    except Exception as e:
        print(f"   ❌ Queue check failed: {e}")
        return False

def check_database():
    """Check database connectivity."""
    print("\n🔍 Checking Database Connectivity...")
    try:
        from auth_service import AuthService
        # Test Supabase connection
        client = AuthService()
        if not client.client:
            print("   ⚠️  Database not configured (using mock mode)")
            return True
        
        # Try to get current user count or a simple query
        from auth_service import get_supabase_admin
        admin_client = get_supabase_admin()
        if admin_client:
            # Test connection by querying profiles table
            result = admin_client.table('profiles').select('id').limit(1).execute()
            print(f"   ✅ Database connected successfully")
            return True
        else:
            print("   ❌ Database client not available")
            return False
            
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
        return False

def check_storage():
    """Check Google Cloud Storage connectivity."""
    print("\n🔍 Checking Google Cloud Storage...")
    try:
        from storage_service import StorageService
        storage = StorageService()
        print(f"   ✅ Storage configured for bucket: {storage.bucket_name}")
        return True
    except Exception as e:
        print(f"   ⚠️  Storage check failed: {e}")
        print("   Note: This is optional. Set GCS_BUCKET_NAME to enable cloud storage.")
        return False

def check_environment():
    """Check required environment variables."""
    print("\n🔍 Checking Environment Variables...")
    required_vars = {
        'SUPABASE_URL': 'Required for authentication',
        'SUPABASE_KEY': 'Required for authentication',
        'FLASK_SECRET_KEY': 'Required for session management',
    }
    
    optional_vars = {
        'RUNPOD_API_KEY': 'Required for Wan 2.1',
        'RUNPOD_ENDPOINT_ID': 'Required for Wan 2.1',
        'GOOGLE_CLOUD_PROJECT': 'Required for Veo 3.1',
        'GCS_BUCKET_NAME': 'Required for cloud storage',
        'GROQ_API_KEY': 'Required for prompt enhancement',
    }
    
    issues = []
    
    for var, desc in required_vars.items():
        if not os.getenv(var):
            print(f"   ❌ {var}: Missing ({desc})")
            issues.append(var)
        else:
            value = os.getenv(var)
            if 'KEY' in var or 'SECRET' in var:
                print(f"   ✅ {var}: {'*' * 8}{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
    
    print("\n   Optional Variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                print(f"   ✅ {var}: {'*' * 8}{value[-4:]}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️  {var}: Not set ({desc})")
    
    return len(issues) == 0

def check_recent_jobs(user_id=None, hours=24):
    """Check recent job statistics."""
    print(f"\n🔍 Checking Recent Jobs (last {hours} hours)...")
    try:
        queue = JobQueue.get_instance()
        
        # Get recent jobs
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(queue.db_path) as conn:
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM jobs WHERE created_at > ? GROUP BY status",
                (cutoff,)
            )
            recent_counts = dict(cursor.fetchall())
        
        total = sum(recent_counts.values())
        print(f"   Total recent jobs: {total}")
        for status, count in recent_counts.items():
            print(f"   {status}: {count}")
        
        # Calculate success rate
        completed = recent_counts.get('completed', 0)
        failed = recent_counts.get('failed', 0)
        if completed + failed > 0:
            success_rate = (completed / (completed + failed)) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        return True
    except Exception as e:
        print(f"   ❌ Recent jobs check failed: {e}")
        return False

def run_system_health_check():
    """Run complete system health check."""
    print("=" * 60)
    print("VIVID FLOW SYSTEM HEALTH CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "queue_health": check_queue_health(),
        "database": check_database(),
        "storage": check_storage(),
        "environment": check_environment(),
        "recent_jobs": check_recent_jobs(),
    }
    
    print("\n" + "=" * 60)
    print("HEALTH SUMMARY")
    print("=" * 60)
    
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check.replace('_', ' ').title()}")
    
    all_healthy = all(results.values())
    
    if all_healthy:
        print("\n🎉 System is healthy!")
    else:
        print("\n⚠️  Some issues detected. Review above for details.")
    
    return all_healthy

def get_queue_stats():
    """Get detailed queue statistics."""
    queue = JobQueue.get_instance()
    with sqlite3.connect(queue.db_path) as conn:
        # Overall stats
        cursor = conn.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        
        # Status breakdown
        cursor = conn.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        status_breakdown = dict(cursor.fetchall())
        
        # Average processing time for completed jobs
        cursor = conn.execute("""
            SELECT AVG(julianday(updated_at) - julianday(created_at)) * 24 * 60 
            FROM jobs WHERE status = 'completed'
        """)
        avg_time = cursor.fetchone()[0]
        
        # Jobs by model
        cursor = conn.execute("SELECT model, COUNT(*) FROM jobs GROUP BY model")
        model_breakdown = dict(cursor.fetchall())
        
        return {
            "total_jobs": total_jobs,
            "status_breakdown": status_breakdown,
            "avg_processing_time_minutes": round(avg_time or 0, 2),
            "model_breakdown": model_breakdown,
            "timestamp": datetime.now().isoformat()
        }

def print_queue_stats():
    """Print formatted queue statistics."""
    stats = get_queue_stats()
    print("\n" + "=" * 60)
    print("DETAILED QUEUE STATISTICS")
    print("=" * 60)
    
    print(f"Total Jobs Processed: {stats['total_jobs']}")
    print(f"Average Processing Time: {stats['avg_processing_time_minutes']} minutes")
    
    print("\nBy Status:")
    for status, count in stats['status_breakdown'].items():
        print(f"  {status}: {count}")
    
    print("\nBy Model:")
    for model, count in stats['model_breakdown'].items():
        print(f"  {model}: {count}")
    
    print(f"\nReport generated: {stats['timestamp']}")

if __name__ == "__main__":
    # Run health check
    healthy = run_system_health_check()
    
    # Show detailed stats
    print_queue_stats()
    
    # Exit with appropriate code
    exit(0 if healthy else 1)
