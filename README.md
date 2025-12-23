# Wan 2.1 I2V Client & Web App

A Python-based toolkit for generating videos from images using the Wan 2.1 Image-to-Video model hosted on RunPod. This project includes both a command-line client for batch processing and a Flask-based web interface for easy interaction.

## Features

- **Web Interface:** A user-friendly web app to upload images, set prompts, and generate videos.
- **Batch Processing:** A Python script to automatically process an entire folder of images.
- **Configurable Parameters:** Control over prompt, negative prompt, dimensions, frame length, steps, seed, and CFG scale.
- **Robust Error Handling:** Includes polling for job status and automatic retries/timeouts.

## Prerequisites

- Python 3.8+
- A [RunPod](https://www.runpod.io/) account with an active Endpoint ID for the Wan 2.1 I2V model.
- An API Key from RunPod.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/studioioniqueeditor-maker/wan-22-i2v.git
    cd wan-22-i2v
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a `.env.client` file in the root directory:
    ```bash
    touch .env.client
    ```

2.  Add your RunPod credentials to `.env.client`:
    ```env
    RUNPOD_API_KEY=your_runpod_api_key_here
    RUNPOD_ENDPOINT_ID=your_endpoint_id_here
    ```

    *Note: `RUNPOD_ENDPOINT_ID` defaults to `3r0ibyzfx7y2bz` if not specified.*

## Usage

### 1. Web Application

Start the Flask web server to generate videos via a browser interface.

```bash
python web_app.py
```

- Open your browser and navigate to `http://127.0.0.1:5000`.
- Upload an image.
- Enter a text prompt (e.g., "A cinematic shot of a futuristic city").
- Click **Generate**.
- The generated video will be displayed and saved to the `output/` directory.

### 2. Batch Processing (Script)

You can use the `GenerateVideoClient` class in your own scripts to process multiple images at once.

**Example Usage:**

```python
from generate_video_client import GenerateVideoClient
import os
from dotenv import load_dotenv

load_dotenv(".env.client")

client = GenerateVideoClient(
    runpod_endpoint_id=os.getenv("RUNPOD_ENDPOINT_ID"),
    runpod_api_key=os.getenv("RUNPOD_API_KEY")
)

# Process all images in the 'input_images' folder
batch_result = client.batch_process_images(
    image_folder_path="./input_images",
    output_folder_path="./output_videos",
    prompt="cinematic slow motion, high quality",
    width=1280,
    height=720
)

print(f"Completed: {batch_result['successful']} videos generated.")
```

## Project Structure

```
wan-22-i2v/
├── generate_video_client.py  # Core logic for RunPod API interaction
├── web_app.py                # Flask web application
├── templates/
│   └── index.html            # Frontend HTML template
├── input_images/             # (Created by user) Directory for batch input
├── output_videos/            # (Created by user) Directory for batch output
├── output/                   # Directory for web app output
├── requirements.txt          # Python dependencies
├── product-design.md         # Product vision and roadmap
└── .env.client               # Environment variables (not committed)
```

## Product Roadmap (VividFlow)

This project is the foundational prototype for **VividFlow**, a planned high-end I2V platform. See `product-design.md` for the full vision, including:
- Glassmorphism UI
- History Gallery
- Public API
- Video Upscaling

## License

[MIT](LICENSE)
