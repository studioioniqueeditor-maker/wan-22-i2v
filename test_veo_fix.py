#!/usr/bin/env python3
"""
Quick test to verify the Veo 3.1 client fix works.
This creates a simple test without needing an actual image.
"""

import os
import sys
import logging

# Setup logging to see all debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

logger = logging.getLogger("vividflow")

def test_client_init():
    """Test that the client initializes correctly."""
    print("\n" + "="*60)
    print("TEST 1: Client Initialization")
    print("="*60)
    
    try:
        from vertex_ai_veo_client import VertexAIVeoClient
        from google import genai
        
        print(f"✓ google-genai version: {genai.__version__}")
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        print(f"✓ Project ID: {project_id}")
        print(f"✓ Location: {location}")
        
        client = VertexAIVeoClient(project_id, location)
        print(f"✓ Veo client created: {type(client).__name__}")
        print(f"✓ SDK version tracked: {client.sdk_version}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_service():
    """Test that GCS storage works."""
    print("\n" + "="*60)
    print("TEST 2: Storage Service")
    print("="*60)
    
    try:
        from storage_service import StorageService
        
        ss = StorageService()
        print(f"✓ StorageService initialized")
        print(f"✓ Bucket: {os.getenv('GCS_BUCKET_NAME')}")
        
        # Test bucket access
        buckets = list(ss.client.list_buckets(max_results=1))
        if buckets:
            print(f"✓ Can access GCS: {buckets[0].name}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_operation_inspection():
    """Test the operation inspection function."""
    print("\n" + "="*60)
    print("TEST 3: Operation Inspection")
    print("="*60)
    
    try:
        from vertex_ai_veo_client import VertexAIVeoClient
        from google.genai import types
        
        # Create a mock failed operation
        class MockOperation:
            def __init__(self):
                self.name = "test-operation-123"
                self.done = True
                self.error = None
                self.result = types.GenerateVideosResponse(
                    generated_videos=[]
                )
                self.metadata = {"test": "data"}
        
        client = VertexAIVeoClient("test-project", "us-central1")
        mock_op = MockOperation()
        
        inspection = client._inspect_operation_failure(mock_op, "test-op")
        print(f"✓ Inspection generated: {len(inspection)} fields")
        print(f"✓ Has result: {inspection['has_result']}")
        print(f"✓ Video count: {inspection['generated_videos_count']}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging_format():
    """Test that logging works with request IDs."""
    print("\n" + "="*60)
    print("TEST 4: Logging Format")
    print("="*60)
    
    try:
        import uuid
        
        # Simulate what the code does
        client_id = str(uuid.uuid4())[:8]
        operation_id = str(uuid.uuid4())[:8]
        
        logger.info(f"[Veo:{client_id}][Op:{operation_id}] Test message")
        logger.error(f"[Veo:{client_id}][Op:{operation_id}] Error simulation")
        
        print("✓ Logging format works")
        print(f"  Example: [Veo:{client_id}][Op:{operation_id}]")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("Veo 3.1 Client Fix Validation")
    print("="*60)
    print(f"Timestamp: {os.popen('date').read().strip()}")
    
    # Load .env
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        print("\n✓ Loaded .env file")
    
    results = []
    
    results.append(("Client Init", test_client_init()))
    results.append(("Storage Service", test_storage_service()))
    results.append(("Operation Inspection", test_operation_inspection()))
    results.append(("Logging Format", test_logging_format()))
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready to use!")
        print("\nNext: Start the server and test with real requests")
    else:
        print("❌ Some tests failed - check logs above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

