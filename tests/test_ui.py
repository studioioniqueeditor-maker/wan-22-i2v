import pytest
from web_app import app
from bs4 import BeautifulSoup

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_vividflow_theme(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for Deep Charcoal/OLED Black background
    assert "#121212" in style_content or "#000000" in style_content, "Deep Charcoal/OLED Black background not found"
    
    # Check for Electric Purple accent
    assert "#A855F7" in style_content, "Electric Purple accent not found"
