import pytest
from web_app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_enhance_prompt_route_success(client):
    with patch('web_app.PromptEnhancer') as mock_enhancer, \
         patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
        mock_enhancer.return_value.enhance.return_value = "Enhanced prompt"
        
        response = client.post('/enhance_prompt', data={'prompt': 'Original prompt'})
        assert response.status_code == 200
        assert response.get_json() == {'enhanced_prompt': 'Enhanced prompt'}
        mock_enhancer.return_value.enhance.assert_called_once_with('Original prompt')

def test_enhance_prompt_route_missing_prompt(client):
    response = client.post('/enhance_prompt', data={})
    assert response.status_code == 400
    assert 'error' in response.get_json()

def test_generate_video_with_cfg(client):
    with patch('web_app.GenerateVideoClient') as mock_client_cls, \
         patch.dict('os.environ', {'RUNPOD_API_KEY': 'test_key', 'RUNPOD_ENDPOINT_ID': 'test_id'}):
        
        mock_instance = mock_client_cls.return_value
        mock_instance.create_video_from_image.return_value = {'status': 'COMPLETED', 'output': 'video_data'}
        mock_instance.save_video_result.return_value = True
        
        with open('tests/test_image.jpg', 'wb') as f:
            f.write(b'fake image data')
            
        with open('tests/test_image.jpg', 'rb') as f:
            response = client.post('/generate', data={
                'image': (f, 'test_image.jpg'),
                'prompt': 'test prompt',
                'cfg': '12.5'
            })
            
        assert response.status_code == 200
        
        # Verify CFG was passed as a float
        args, kwargs = mock_instance.create_video_from_image.call_args
        assert kwargs['cfg'] == 12.5
        
        import os
        os.remove('tests/test_image.jpg')
