import os
import datetime
import uuid
from flask import Flask, render_template, request, send_from_directory, url_for, jsonify, session
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from generate_video_client import GenerateVideoClient
from prompt_enhancer import PromptEnhancer
from storage_service import StorageService
from auth_service import AuthService

# Load environment variables
load_dotenv(".env.client")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey") # Use env var for production
app.config['SESSION_COOKIE_SECURE'] = (os.getenv("FLASK_ENV") == "production") # Only send cookie over HTTPS in production

bcrypt = Bcrypt(app)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        auth_service = AuthService()
        user = auth_service.login(email, password)
        session['user_id'] = user['user_id']
        session['email'] = user['email']
        return jsonify({"message": "Login successful", "user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        auth_service = AuthService()
        auth_service.logout()
        session.pop('user_id', None)
        session.pop('email', None)
        return jsonify({"message": "Logout successful"}), 200
    return jsonify({"error": "Not logged in"}), 401

@app.route('/enhance_prompt', methods=['POST'])
def enhance_prompt():
    original_prompt = request.form.get('prompt')
    if not original_prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    runpod_api_key = os.getenv("RUNPOD_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        return jsonify({"error": "GROQ_API_KEY not set in environment"}), 500

    try:
        enhancer = PromptEnhancer(api_key=groq_api_key)
        enhanced_prompt = enhancer.enhance(original_prompt)
        return jsonify({"enhanced_prompt": enhanced_prompt})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    # Check if user is logged in (optional for now, but good for future)
    user_id = session.get('user_id')
    # print(f"DEBUG: User ID from session: {user_id}")

    if 'image' not in request.files:
        return render_template('index.html', error="No image uploaded")
    
    file = request.files['image']
    if file.filename == '':
        return render_template('index.html', error="No selected file")

    prompt = request.form.get('prompt')
    negative_prompt = request.form.get('negative_prompt', 'blurry, low quality, distorted')
    
    try:
        cfg = float(request.form.get('cfg', 7.5))
        resolution = request.form.get('resolution', '1080p')
        duration = request.form.get('duration', '5s')
        fps = request.form.get('fps', '24')
        loop_video = request.form.get('loop') == 'true'
        stabilize_motion = request.form.get('stabilize') == 'true'

    except ValueError:
        cfg = 7.5
        resolution = '1080p'
        duration = '5s'
        fps = '24'
        loop_video = False
        stabilize_motion = False

    image_path = None # Initialize image_path outside try for finally block
    try:
        # Save uploaded image temporarily
        filename = f"{uuid.uuid4()}_{file.filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        runpod_endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

        if not MOCK_MODE:
            if not runpod_api_key:
                return render_template('index.html', error="RUNPOD_API_KEY not set in .env.client")
            if not runpod_endpoint_id:
                return render_template('index.html', error="RUNPOD_ENDPOINT_ID not set in .env.client")
            print(f"Using RunPod Endpoint ID: {runpod_endpoint_id}")
        else:
            runpod_api_key = "mock_key"
            runpod_endpoint_id = "mock_id"
            print("MOCK MODE ENABLED: Skipping RunPod generation.")

        client = GenerateVideoClient(
            runpod_endpoint_id=runpod_endpoint_id,
            runpod_api_key=runpod_api_key
        )

        # Prepare generation parameters (RunPod specific parameters)
        # Note: 'resolution', 'duration', 'fps', 'loop_video', 'stabilize_motion' are not
        # directly passed to RunPod API in current GenerateVideoClient. They are for future features.
        generation_params = {
            "image_path": image_path,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 1280, 
            "height": 720, 
            "length": 81,  
            "steps": 30,
            "seed": 42,
            "cfg": cfg
        }

        if MOCK_MODE:
            print("MOCK MODE: Simulating video generation.")
            result = {
                'status': 'COMPLETED',
                'output': {'video_base64': 'mock_video_data'}, 
                'metrics': {'spin_up_time': 0.1, 'generation_time': 0.1}
            }
            output_filename = f"mock_{uuid.uuid4()}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            with open(output_path, "wb") as f:
                f.write(b"mock video content")
            save_success = True
        else:
            result = client.create_video_from_image(**generation_params)
            output_filename = f"wan22_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            save_success = client.save_video_result(result, output_path)

        if result.get('status') == 'COMPLETED':
            if save_success:
                final_video_url = None
                # Try to upload to GCS if configured
                bucket_name = os.getenv("GCS_BUCKET_NAME")
                if bucket_name:
                    try:
                        storage_service = StorageService()
                        gcs_url = storage_service.upload_file(output_path, f"videos/{output_filename}")
                        final_video_url = gcs_url
                        # os.remove(output_path) # Optional: Remove local file after successful upload
                        print(f"DEBUG: GCS Upload successful. Final video URL: {final_video_url}")
                    except Exception as e:
                        print(f"ERROR: GCS Upload failed: {e}. Reverting to local URL.")
                        import traceback
                        traceback.print_exc()

                if final_video_url is None:
                    final_video_url = url_for('get_video', filename=output_filename)
                    print(f"DEBUG: Using local video URL: {final_video_url}")

                metrics = result.get('metrics', {})
                response = render_template('index.html', video_url=final_video_url, metrics=metrics)
                return response
            else:
                return render_template('index.html', error="Failed to save video result.")
        else:
            return render_template('index.html', error=f"Generation failed: {result.get('error')}")

    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")
    finally:
        # Cleanup upload
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

@app.route('/output/<filename>')
def get_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
