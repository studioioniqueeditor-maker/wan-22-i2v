import os
import datetime
import uuid
import io
from PIL import Image
from functools import wraps
from flask import Flask, render_template, request, send_from_directory, url_for, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
from video_client_factory import VideoClientFactory
from prompt_enhancer import PromptEnhancer
from veo_prompt_enhancer import VeoPromptEnhancer
from storage_service import StorageService
from auth_service import AuthService

# Load environment variables
load_dotenv(".env.client")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
# Force session cookies to be insecure for local HTTP development
app.config['SESSION_COOKIE_SECURE'] = False 

bcrypt = Bcrypt(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"], # Increased for development
    storage_uri="memory://",
)

# Simplified CORS for local dev
CORS(app)

@app.before_request
def debug_request():
    print(f"DEBUG: {request.method} {request.path} | User: {session.get('user_id')}")

@app.errorhandler(404)
def resource_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify(error=str(e)), 404
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    if request.path.startswith('/api/'):
        return jsonify(error="Internal Server Error"), 500
    return render_template('index.html', error="Internal Server Error"), 500

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# --- Helpers ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401
        
        user = AuthService.get_user_by_api_key(api_key)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401
        
        request.user = user
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/', methods=['GET'])
@login_required
def index():
    user_email = session.get('email', 'User')
    return render_template('index.html', user_email=user_email)

@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/history', methods=['GET'])
@login_required
def history():
    user_email = session.get('email', 'User')
    return render_template('history.html', user_email=user_email)

@app.route('/account', methods=['GET'])
@login_required
def account():
    user_email = session.get('email', 'User')
    user = AuthService.get_user_by_id(session.get('user_id'))
    return render_template('account.html', user_email=user_email, api_key=user.get('api_key'))

# --- API Routes for Auth ---

@app.route('/api/v1/keys', methods=['POST'])
@login_required
def generate_api_key():
    user_id = session.get('user_id')
    new_key = AuthService.generate_api_key(user_id)
    if new_key:
        return jsonify({"api_key": new_key}), 201
    return jsonify({"error": "Failed to generate API key"}), 500

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_post():
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
        # Enhanced error logging for login
        print(f"ERROR during login: {e}")
        import traceback
        traceback.print_exc()
        
        # Check for specific Supabase error messages
        error_str = str(e).lower()
        if "invalid login credentials" in error_str:
            return jsonify({"error": "Invalid email or password."}), 401
        if "email not confirmed" in error_str:
            return jsonify({"error": "Please check your email to confirm your account before logging in."}), 401
            
        return jsonify({"error": "Authentication failed."}), 401

@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register_post():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        auth_service = AuthService()
        user = auth_service.signup(email, password)
        return jsonify({"message": "Registration successful", "user": user}), 201
    except Exception as e:
        # Enhanced error logging
        print(f"ERROR during registration: {e}")
        import traceback
        traceback.print_exc()

        if "Email already registered" in str(e):
            return jsonify({"error": "Email address is already in use."}), 409
        # Check for specific Supabase password error
        if "Password should be at least 6 characters" in str(e):
            return jsonify({"error": "Password should be at least 6 characters long."}), 400
        
        return jsonify({"error": "Registration failed. Please try again later."}), 500

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    return redirect(url_for('login_page'))

# --- Application Routes ---

@app.route('/enhance_prompt', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def enhance_prompt():
    original_prompt = request.form.get('prompt')
    model_name = request.form.get('model', 'wan2.1')
    
    if not original_prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        if model_name == "veo3.1":
            # Veo enhancement uses Gemini and can take an image
            image_file = request.files.get('image')
            image_bytes = None
            if image_file:
                try:
                    img = Image.open(image_file)
                    # Resize to reduce token usage (max 480px dimension)
                    img.thumbnail((480, 480))
                    img_byte_arr = io.BytesIO()
                    # Convert to RGB if needed (e.g. RGBA to JPEG) to avoid errors
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    img.save(img_byte_arr, format='JPEG', quality=85)
                    image_bytes = img_byte_arr.getvalue()
                except Exception as img_err:
                    print(f"Image processing failed: {img_err}")
                    # Fallback to original bytes if resize fails
                    image_file.seek(0)
                    image_bytes = image_file.read()
            
            # Keywords from form
            camera_motion = request.form.get('camera_motion', 'None')
            subject_animation = request.form.get('subject_animation', 'None')
            environmental_animation = request.form.get('environmental_animation', 'None')
            keywords = [camera_motion, subject_animation, environmental_animation]
            
            enhancer = VeoPromptEnhancer()
            enhanced_prompt = enhancer.enhance(original_prompt, image_bytes=image_bytes, keywords=keywords)
        else:
            # Default Wan enhancer (Groq)
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                return jsonify({"error": "GROQ_API_KEY not set"}), 500
            enhancer = PromptEnhancer(api_key=groq_api_key)
            enhanced_prompt = enhancer.enhance(original_prompt)
            
        return jsonify({"enhanced_prompt": enhanced_prompt})
    except Exception as e:
        print(f"Error in /enhance_prompt: {e}")
        return jsonify({"error": "Prompt enhancement failed."}), 500

def _run_video_generation(user_id, file, form_data):
    """Helper function to handle the core video generation logic."""
    model_name = form_data.get('model', 'wan2.1')
    prompt = form_data.get('prompt')
    negative_prompt = form_data.get('negative_prompt', 'blurry, low quality, distorted')
    
    try:
        cfg = float(form_data.get('cfg', 7.5))
    except ValueError:
        cfg = 7.5

    # Veo specific params
    camera_motion = form_data.get('camera_motion', 'None')
    subject_animation = form_data.get('subject_animation', 'None')
    environmental_animation = form_data.get('environmental_animation', 'None')
    duration_seconds = int(form_data.get('duration', 4))
    auto_enhance = form_data.get('auto_enhance') == 'true'

    image_path = None
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
                return {"status": "error", "message": "RUNPOD_API_KEY not set"}
            if not runpod_endpoint_id:
                return {"status": "error", "message": "RUNPOD_ENDPOINT_ID not set"}
        
        # Use Factory to get client
        try:
            client = VideoClientFactory.get_client(
                model_name,
                runpod_endpoint_id=runpod_endpoint_id,
                runpod_api_key=runpod_api_key
            )
        except ValueError as e:
             return {"status": "error", "message": str(e)}
        except NotImplementedError as e:
             return {"status": "error", "message": str(e)}

        generation_params = {
            "image_path": image_path,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 1280, 
            "height": 720, 
            "length": 81,  
            "steps": 30,
            "seed": 42,
            "cfg": cfg,
            "camera_motion": camera_motion,
            "subject_animation": subject_animation,
            "environmental_animation": environmental_animation,
            "duration_seconds": duration_seconds,
            "enhance_prompt": auto_enhance
        }

        if MOCK_MODE:
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
            output_filename = f"wan22_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            save_success = client.save_video_result(result, output_path)

        if result.get('status') == 'COMPLETED':
            if save_success:
                final_video_url = None
                bucket_name = os.getenv("GCS_BUCKET_NAME")
                if bucket_name:
                    try:
                        storage_service = StorageService()
                        gcs_url = storage_service.upload_file(output_path, f"videos/{output_filename}")
                        final_video_url = gcs_url
                    except Exception as e:
                        print(f"ERROR: GCS Upload failed: {e}")

                if final_video_url is None:
                    final_video_url = url_for('get_video', filename=output_filename, _external=True)

                # Record in history
                history_entry = {
                    "id": str(uuid.uuid4()),
                    "prompt": prompt,
                    "video_url": final_video_url,
                    "status": "COMPLETED",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                AuthService.add_history(user_id, history_entry)

                return {
                    "status": "success", 
                    "video_url": final_video_url,
                    "metrics": result.get('metrics', {})
                }
            else:
                return {"status": "error", "message": "Failed to save video result."}
        else:
            error_msg = result.get('error', 'Unknown error')
            return {"status": "error", "message": f"Generation failed: {error_msg}"}

    except Exception as e:
        print(f"Error in generation helper: {e}")
        return {"status": "error", "message": "An unexpected error occurred."}
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user_id = session.get('user_id')
    
    if 'image' not in request.files:
        return render_template('index.html', error="No image uploaded", user_email=session.get('email'))
    
    file = request.files['image']
    if file.filename == '':
        return render_template('index.html', error="No selected file", user_email=session.get('email'))

    result = _run_video_generation(user_id, file, request.form)

    if result['status'] == 'success':
        # Check if the client wants JSON (AJAX request)
        if request.headers.get('Accept') == 'application/json':
            return jsonify(result)
        return render_template('index.html', video_url=result['video_url'], metrics=result.get('metrics'), user_email=session.get('email'))
    else:
        if request.headers.get('Accept') == 'application/json':
            return jsonify(result), 500
        return render_template('index.html', error=result['message'], user_email=session.get('email'))



# --- History & Usage API ---

@app.route('/api/history', methods=['GET'])
@login_required
def get_history_api():
    user_id = session.get('user_id')
    history = AuthService.get_history(user_id)
    return jsonify(history)

@app.route('/api/v1/generate', methods=['POST'])
@api_key_required
def api_generate():
    user_id = request.user['user_id']
    
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    result = _run_video_generation(user_id, file, request.form)
    
    if result['status'] == 'success':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/api/v1/status/<job_id>', methods=['GET'])
@api_key_required
def api_status(job_id):
    # This is a placeholder for a real job queue system
    return jsonify({"job_id": job_id, "status": "COMPLETED"})

@app.route('/api/v1/history', methods=['GET'])
@api_key_required
def api_history():
    user_id = request.user['user_id']
    history = AuthService.get_history(user_id)
    return jsonify(history)

@app.route('/api/v1/usage', methods=['GET'])
@api_key_required
def api_usage():
    # Placeholder for credit/usage logic
    return jsonify({"credits_remaining": 1000})


@app.route('/output/<filename>')
def get_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    try:
        print("Starting Flask application...")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"An error occurred while trying to start the application: {e}")
        import traceback
        traceback.print_exc()