import pytest
from web_app import app
from unittest.mock import patch, MagicMock
import os
import io
import shutil # For cleaning up directories

# Mock file class to simulate file behavior for tests
class MockFile(io.BytesIO):
    def __init__(self, content, name="mock_file.jpg"):
        super().__init__(content)
        self.name = name


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key' # Required for sessions
    app.config['TEMPLATES_AUTO_RELOAD'] = True # Ensure templates are reloaded for tests

    # Use temporary directories for uploads and outputs for test isolation
    temp_upload_dir = os.path.join(app.root_path, 'test_temp_uploads')
    temp_output_dir = os.path.join(app.root_path, 'test_output')
    app.config['UPLOAD_FOLDER'] = temp_upload_dir
    app.config['OUTPUT_FOLDER'] = temp_output_dir

    # Ensure directories exist for the test run
    os.makedirs(temp_upload_dir, exist_ok=True)
    os.makedirs(temp_output_dir, exist_ok=True)

    with app.test_client() as client:
        with app.app_context():
            yield client
    
    # Clean up after tests
    if os.path.exists(temp_upload_dir):
        shutil.rmtree(temp_upload_dir)
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)

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
         patch.dict('os.environ', {'RUNPOD_API_KEY': 'test_key', 'RUNPOD_ENDPOINT_ID': 'test_id', 'MOCK_MODE': 'false'}):
        
        mock_instance = mock_client_cls.return_value
        mock_instance.create_video_from_image.return_value = {'status': 'COMPLETED', 'output': 'video_data'}
        mock_instance.save_video_result.return_value = True
        
        # Use MockFile for the image upload
        mock_image_file = MockFile(b'fake image data', name='test_image.jpg')
        response = client.post('/generate', data={
            'image': (mock_image_file, mock_image_file.name),
            'prompt': 'test prompt',
            'cfg': '12.5'
        })
            
        assert response.status_code == 200
        
        # Verify CFG was passed as a float
        args, kwargs = mock_instance.create_video_from_image.call_args
        assert kwargs['cfg'] == 12.5

def test_timing_metrics_in_response(client):
    with patch('web_app.GenerateVideoClient') as mock_client_cls, \
         patch.dict('os.environ', {'RUNPOD_API_KEY': 'test_key', 'RUNPOD_ENDPOINT_ID': 'test_id', 'MOCK_MODE': 'false', 'GCS_BUCKET_NAME': 'test-bucket'}), \
         patch('web_app.StorageService') as mock_storage_service_cls, \
         patch('web_app.render_template') as mock_render_template: # Mock render_template
        
        mock_instance = mock_client_cls.return_value
        mock_instance.create_video_from_image.return_value = {
            'status': 'COMPLETED',
            'output': 'video_data',
            'metrics': {
                'spin_up_time': 2.5,
                'generation_time': 10.0
            }
        }
        mock_instance.save_video_result.return_value = True # Directly mock to avoid file ops
        
        mock_storage_service_cls.return_value.upload_file.return_value = "https://gcs-url/video.mp4" # Mock the upload

        # Use BytesIO for the image upload
        mock_image_file = MockFile(b'fake image data', name='test_image.jpg')
        response = client.post('/generate', data={'image': (mock_image_file, mock_image_file.name), 'prompt': 'test'})
    
        assert response.status_code == 200
        mock_render_template.assert_called_once() # Ensure template was called
        # Check arguments passed to render_template
        args, kwargs = mock_render_template.call_args
        assert kwargs['video_url'] == "https://gcs-url/video.mp4"
        assert kwargs['metrics']['spin_up_time'] == 2.5
        assert kwargs['metrics']['generation_time'] == 10.0
def test_generate_video_uploads_to_gcs(client):
    with patch('web_app.GenerateVideoClient') as mock_client_cls, \
         patch.dict('os.environ', {'RUNPOD_API_KEY': 'test_key', 'RUNPOD_ENDPOINT_ID': 'test_id', 'GCS_BUCKET_NAME': 'test-bucket', 'MOCK_MODE': 'false'}), \
         patch('web_app.StorageService') as mock_storage_cls, \
         patch('web_app.render_template') as mock_render_template: # Mock render_template
        
        mock_instance = mock_client_cls.return_value
        mock_instance.create_video_from_image.return_value = {'status': 'COMPLETED', 'output': 'video_data'}
        mock_instance.save_video_result.return_value = True # Directly mock to avoid file ops
        
        mock_storage_cls.return_value.upload_file.return_value = "https://gcs-url/video.mp4"
        
        # Use BytesIO for the image upload
        mock_image_file = MockFile(b'fake image data', name='test_image.jpg')
        response = client.post('/generate', data={'image': (mock_image_file, mock_image_file.name), 'prompt': 'test'})
            
        assert response.status_code == 200
        mock_render_template.assert_called_once() # Ensure template was called
        # Check arguments passed to render_template
        args, kwargs = mock_render_template.call_args
        assert kwargs['video_url'] == "https://gcs-url/video.mp4"
        
        # Verify upload was called
        mock_storage_cls.return_value.upload_file.assert_called_once()

def test_user_login_sets_secure_session_cookie(client):
    with patch('web_app.AuthService') as mock_auth_service_cls, \
         patch.dict('os.environ', {'SUPABASE_URL': 'http://localhost:54321', 'SUPABASE_KEY': 'fake_key'}), \
         patch.dict(client.application.config, {'SESSION_COOKIE_SECURE': True}, clear=False): # Patch config dict
        
        mock_auth_service_instance = mock_auth_service_cls.return_value
        mock_auth_service_instance.login.return_value = {"user_id": "test_user", "email": "test@example.com"}
        
        response = client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
        
        assert response.status_code == 200 # Assuming a successful redirect or JSON response
        
        # Check if a session cookie is set (Flask's default session cookie)
        assert 'session' in response.headers.get('Set-Cookie', '')
        assert 'HttpOnly' in response.headers.get('Set-Cookie', '') # Should be HttpOnly by default with Flask
        assert 'Secure' in response.headers.get('Set-Cookie', '') # Requires HTTPS, but Flask will set it if app.config['SESSION_COOKIE_SECURE'] is True