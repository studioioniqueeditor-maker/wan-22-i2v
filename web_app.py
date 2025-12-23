import os
import datetime
import uuid
from flask import Flask, render_template, request, send_from_directory, url_for, jsonify
from dotenv import load_dotenv
from generate_video_client import GenerateVideoClient
from prompt_enhancer import PromptEnhancer
from storage_service import StorageService

# Load environment variables
load_dotenv(".env.client")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.secret_key = 'supersecretkey'  # Change this for production

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

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
    if 'image' not in request.files:
        return render_template('index.html', error="No image uploaded")
    
    file = request.files['image']
    if file.filename == '':
        return render_template('index.html', error="No selected file")

    prompt = request.form.get('prompt')
    negative_prompt = request.form.get('negative_prompt', 'blurry, low quality, distorted')
    
    try:
        cfg = float(request.form.get('cfg', 7.5))
    except ValueError:
        cfg = 7.5

    if file:
        # Save uploaded image
        filename = f"{uuid.uuid4()}_{file.filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        # Get credentials
        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        runpod_endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

        if not runpod_api_key:
            return render_template('index.html', error="RUNPOD_API_KEY not set in .env.client")
        
        if not runpod_endpoint_id:
            return render_template('index.html', error="RUNPOD_ENDPOINT_ID not set in .env.client")

        print(f"Using Endpoint ID: {runpod_endpoint_id}")

        # Initialize client
        client = GenerateVideoClient(
            runpod_endpoint_id=runpod_endpoint_id,
            runpod_api_key=runpod_api_key
        )

        # MOCK MODE: Set this to True to test GCS without RunPod
        MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

        try:
            if MOCK_MODE:
                print("MOCK MODE ENABLED: Skipping RunPod generation.")
                # Simulate a successful result using an existing file
                result = {
                    'status': 'COMPLETED',
                    'metrics': {'spin_up_time': 0.1, 'generation_time': 0.1}
                }
                # Use the first video found in output/ for mocking
                existing_videos = [f for f in os.listdir(app.config['OUTPUT_FOLDER']) if f.endswith('.mp4')]
                if not existing_videos:
                    return render_template('index.html', error="Mock mode failed: No existing videos in output/ folder.")
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"mock_{timestamp}.mp4"
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                # Copy existing video to mock path
                import shutil
                shutil.copy(os.path.join(app.config['OUTPUT_FOLDER'], existing_videos[0]), output_path)
                
                # Create a fake 'save' success
                save_success = True
            else:
                # Generate video
                result = client.create_video_from_image(
                    image_path=image_path,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=1280,
                    height=720,
                    length=81,
                    steps=30,
                    seed=42,
                    cfg=cfg
                )
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"wan22_{timestamp}.mp4"
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                save_success = client.save_video_result(result, output_path)

            if result.get('status') == 'COMPLETED':
                if save_success:
                    video_url = url_for('get_video', filename=output_filename)
                    
                    # Try to upload to GCS if configured
                    bucket_name = os.getenv("GCS_BUCKET_NAME")
                    if bucket_name:
                        try:
                            storage_service = StorageService()
                            gcs_url = storage_service.upload_file(output_path, f"videos/{output_filename}")
                            video_url = gcs_url
                            # Optional: Remove local file after successful upload
                            # os.remove(output_path) 
                        except Exception as e:
                            print(f"ERROR: GCS Upload failed: {e}")
                            import traceback
                            traceback.print_exc()
                    metrics = result.get('metrics', {})
                    return render_template('index.html', video_url=video_url, metrics=metrics)
                else:
                    return render_template('index.html', error="Failed to save video result.")
            else:
                return render_template('index.html', error=f"Generation failed: {result.get('error')}")

        except Exception as e:
            return render_template('index.html', error=f"An unexpected error occurred: {e}")
        finally:
            # Cleanup upload
            if os.path.exists(image_path):
                os.remove(image_path)
    
    return render_template('index.html', error="Unknown error")

@app.route('/output/<filename>')
def get_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
