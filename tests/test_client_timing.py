import pytest
from unittest.mock import MagicMock, patch
from generate_video_client import GenerateVideoClient
import time

@pytest.fixture
def client():
    return GenerateVideoClient(runpod_endpoint_id="test_id", runpod_api_key="test_key")

def test_client_timing_metrics(client):
    # Mock response for job creation
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {"id": "job_123", "status": "IN_QUEUE"}
    
    # Mock responses for polling
    mock_poll_response_1 = MagicMock()
    mock_poll_response_1.status_code = 200
    mock_poll_response_1.json.return_value = {"id": "job_123", "status": "IN_PROGRESS"}
    
    mock_poll_response_2 = MagicMock()
    mock_poll_response_2.status_code = 200
    mock_poll_response_2.json.return_value = {
        "id": "job_123", 
        "status": "COMPLETED", 
        "output": {"video": "base64data"}
    }
    
    with patch('requests.post', return_value=mock_post_response), \
         patch('requests.get', side_effect=[mock_poll_response_1, mock_poll_response_2]), \
         patch('time.sleep', return_value=None): # Speed up test
        
        # Override file reading since we just want to test timing logic
        with patch('builtins.open', MagicMock()), \
             patch('base64.b64encode', return_value=b'fake_base64'):
             
            result = client.create_video_from_image(image_path="dummy.jpg", prompt="test")
            
            assert result['status'] == 'COMPLETED'
            assert 'metrics' in result
            metrics = result['metrics']
            assert 'submission_time' in metrics
            assert 'start_time' in metrics
            assert 'completion_time' in metrics
            assert 'spin_up_time' in metrics
            assert 'generation_time' in metrics
            
            # Since we mocked polling, times should be > 0 (except maybe spin_up if instant)
            assert metrics['generation_time'] >= 0
