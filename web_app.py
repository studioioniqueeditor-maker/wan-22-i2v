import os
import datetime
import uuid
from flask import Flask, render_template, request, send_from_directory, url_for
from dotenv import load_dotenv
from generate_video_client import GenerateVideoClient

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

@app.route('/generate', methods=['POST'])
def generate():
    if 'image' not in request.files:
        return render_template('index.html', error="No image uploaded")
    
    file = request.files['image']
    if file.filename == '':
        return render_template('index.html', error="No selected file")

    prompt = request.form.get('prompt')
    negative_prompt = request.form.get('negative_prompt', 'blurry, low quality, distorted')

    if file:
        # Save uploaded image
        filename = f"{uuid.uuid4()}_{file.filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        # Get credentials
        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        runpod_endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID") or '3r0ibyzfx7y2bz'

        if not runpod_api_key:
            return render_template('index.html', error="RUNPOD_API_KEY not set in .env.client")

        # Initialize client
        client = GenerateVideoClient(
            runpod_endpoint_id=runpod_endpoint_id,
            runpod_api_key=runpod_api_key
        )

        try:
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
                cfg=20
            )

            if result.get('status') == 'COMPLETED':
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"wan22_{timestamp}.mp4"
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                if client.save_video_result(result, output_path):
                    video_url = url_for('get_video', filename=output_filename)
                    return render_template('index.html', video_url=video_url)
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
