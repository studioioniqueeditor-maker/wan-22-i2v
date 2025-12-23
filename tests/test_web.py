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
