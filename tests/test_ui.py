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

def test_glassmorphism(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for backdrop-filter blur
    assert "backdrop-filter: blur" in style_content, "Backdrop filter not found"
    
    # Check for container glass styles
    assert "background: rgba(255, 255, 255, 0.05)" in style_content, "Container glass background not found"
    assert "border: 1px solid rgba(255, 255, 255, 0.1)" in style_content, "Container glass border not found"

def test_button_interactions(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for button transition
    assert "transition: all 0.3s" in style_content, "Button transition not found"
    
    # Check for button hover glow
    assert "box-shadow: 0 0 15px rgba(168, 85, 247, 0.5)" in style_content, "Button hover glow not found"
    
    # Check for transform on hover
    assert "transform: translateY(-2px)" in style_content, "Button hover transform not found"

def test_dropzone_and_loading(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for drop zone styles
    assert ".drop-zone" in style_content, "Drop zone class not found in CSS"
    assert "border: 2px dashed" in style_content, "Drop zone dashed border not found"
    
    # Check for custom loading animation
    assert "@keyframes pulse-glow" in style_content, "Pulse glow animation not found"
    assert "animation: pulse-glow" in style_content, "Animation usage not found"

def test_cfg_slider(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for CFG input
    cfg_input = soup.find('input', {'id': 'cfg'})
    assert cfg_input is not None, "CFG input not found"
    assert cfg_input['type'] == 'range', "CFG input should be a range slider"
    assert cfg_input['value'] == '7.5', "Default CFG value should be 7.5"
    assert cfg_input['min'] == '1.0', "CFG min should be 1.0"
    assert cfg_input['max'] == '20.0', "CFG max should be 20.0"
