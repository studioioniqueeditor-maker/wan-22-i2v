import pytest
from web_app import app
from bs4 import BeautifulSoup
import os
import shutil # For cleaning up directories

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key' # Required for sessions

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
    
    main_card = soup.find('div', class_='main-card')
    assert main_card is not None, "Main card container not found"

    # Check for 2-column grid (7/5 split inside main-card)
    left_col = main_card.find('div', class_='col-lg-7')
    right_col = main_card.find('div', class_='col-lg-5')
    
    assert left_col is not None, "Left column (col-lg-7) not found in main-card"
    assert right_col is not None, "Right column (col-lg-5) not found in main-card"
    
    # Check for Recent Generations section within the right column
    assert right_col.find(string="Recent Generations"), "Recent Generations header not found in right column"
    assert right_col.find('div', class_='recent-list'), "Recent list container not found in right column"

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
    