import pytest
from web_app import app
from bs4 import BeautifulSoup

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_vividflow_light_theme(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for Light Gray background
    assert "#F5F5F7" in style_content, "Light Gray background not found"
    
    # Check for White Card background
    assert "#FFFFFF" in style_content, "White Card background not found"
    
    # Check for Accent Blue
    assert "#0071E3" in style_content, "Accent Blue not found"

def test_layout_structure(client):
    response = client.get('/')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for 2-column grid (6/6 split)
    assert soup.find_all('div', class_='col-lg-6'), "Columns (col-lg-6) not found"
    assert len(soup.find_all('div', class_='col-lg-6')) >= 2, "Expected at least two col-lg-6 columns"
    
    # Check for main card container
    assert soup.find('div', class_='main-card'), "Main card container not found"

def test_dropzone_and_loading(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    style_content = soup.find('style').string if soup.find('style') else ""
    
    # Check for drop zone styles
    assert ".drop-zone" in style_content, "Drop zone class not found in CSS"
    
    # Check for custom loading animation
    assert "@keyframes pulse-glow" in style_content, "Pulse glow animation not found"

def test_cfg_slider(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for CFG input
    cfg_input = soup.find('input', {'id': 'cfg'})
    assert cfg_input is not None, "CFG input not found"
    assert cfg_input['type'] == 'range', "CFG input should be a range slider"
    assert cfg_input['value'] == '7.5', "Default CFG value should be 7.5"

def test_new_controls(client):
    response = client.get('/')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Checkboxes
    assert soup.find('input', {'id': 'loop', 'type': 'checkbox'}), "Loop checkbox not found"
    assert soup.find('input', {'id': 'stabilize', 'type': 'checkbox'}), "Stabilize checkbox not found"
    
    # Dropdowns
    assert soup.find('select', {'name': 'resolution'}), "Resolution select not found"
    assert soup.find('select', {'name': 'duration'}), "Duration select not found"
    assert soup.find('select', {'name': 'fps'}), "FPS select not found"
    