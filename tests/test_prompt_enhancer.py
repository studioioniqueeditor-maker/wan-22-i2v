import pytest
from unittest.mock import MagicMock, patch
from prompt_enhancer import PromptEnhancer

@pytest.fixture
def enhancer():
    with patch('groq.Groq'):
        return PromptEnhancer(api_key="test_key")

def test_enhance_prompt_success(enhancer):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Enhanced cinematic prompt"))
    ]
    
    with patch.object(enhancer, 'client') as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        
        result = enhancer.enhance("original prompt")
        assert result == "Enhanced cinematic prompt"
        mock_client.chat.completions.create.assert_called_once()

def test_enhance_prompt_failure(enhancer):
    with patch.object(enhancer, 'client') as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as excinfo:
            enhancer.enhance("original prompt")
        assert "API Error" in str(excinfo.value)
