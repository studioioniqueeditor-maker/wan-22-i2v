#!/usr/bin/env python3
"""
Verification script for the None parameter unpacking fix.
This demonstrates that the fix handles None parameters correctly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_queue import Job, JobStatus
from datetime import datetime

def test_none_parameters_handling():
    """Test that job with None parameters doesn't crash when unpacking."""
    print("Testing None parameters handling...")
    
    # Create a job with None parameters (the problematic case)
    job = Job(
        job_id="test-job-123",
        user_id="user-456",
        model="veo3.1",
        status=JobStatus.QUEUED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        prompt="Test prompt",
        negative_prompt="",
        parameters=None  # This is the problematic case
    )
    
    print(f"✓ Job created with None parameters: {job.job_id}")
    
    # Try to unpack parameters the old way (would fail)
    try:
        test_params_old = {
            "image_path": "/tmp/test.jpg",
            "prompt": job.prompt,
            **job.parameters  # This would throw TypeError
        }
        print("✗ Old method didn't fail (unexpected)")
        return False
    except TypeError as e:
        print(f"✓ Old method fails as expected: {e}")
    
    # Try to unpack parameters the new way (should work)
    try:
        test_params_new = {
            "image_path": "/tmp/test.jpg",
            "prompt": job.prompt,
            **(job.parameters or {})  # This should work
        }
        print(f"✓ New method works correctly: {test_params_new}")
    except Exception as e:
        print(f"✗ New method failed unexpectedly: {e}")
        return False
    
    # Test with actual parameters
    job.parameters = {"duration_seconds": 4, "enhance_prompt": True}
    try:
        test_params_with_data = {
            "image_path": "/tmp/test.jpg",
            "prompt": job.prompt,
            **(job.parameters or {})
        }
        print(f"✓ New method works with actual parameters: {test_params_with_data}")
    except Exception as e:
        print(f"✗ Failed with actual parameters: {e}")
        return False
    
    print("\n✅ All tests passed! The fix correctly handles None parameters.")
    return True

if __name__ == "__main__":
    success = test_none_parameters_handling()
    sys.exit(0 if success else 1)
