import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from storage_service import StorageService
import os

@pytest.fixture
def mock_storage_client():
    with patch('google.cloud.storage.Client') as mock_client:
        yield mock_client

@pytest.fixture
def service(mock_storage_client):
    with patch.dict('os.environ', {'GCS_BUCKET_NAME': 'test-bucket'}):
        return StorageService()

def test_upload_file_success(service, mock_storage_client):
    # service.bucket is already the mock returned by client.bucket()
    mock_blob = MagicMock()
    service.bucket.blob.return_value = mock_blob
    
    # Simple attribute setting
    mock_blob.public_url = "https://storage.googleapis.com/test-bucket/test_video.mp4"
    
    local_path = "test_video.mp4"
    destination_blob_name = "videos/test_video.mp4"
    
    # Simulate file existence check if needed, or just mock open
    with patch('builtins.open', MagicMock()):
        url = service.upload_file(local_path, destination_blob_name)
        
    assert url == "https://storage.googleapis.com/test-bucket/test_video.mp4"
    service.bucket.blob.assert_called_with(destination_blob_name)
    mock_blob.upload_from_filename.assert_called_with(local_path)
def test_init_missing_bucket_env():
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="GCS_BUCKET_NAME environment variable is required"):
            StorageService()
