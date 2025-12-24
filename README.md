# Vivid Flow - Wan 2.1 & Veo 3.1 I2V Client (v1.0.0)

A professional-grade toolkit and web interface for generating videos from images using the state-of-the-art **Wan 2.1** (via RunPod) and **Google Veo 3.1** (via Vertex AI) models. This project is the first production release of the VividFlow platform.

## Features (v1.0.0)

- **Dual Model Support:** Seamlessly switch between **Wan 2.1** (open-source) and **Google Veo 3.1** (enterprise).
- **Modern Web Interface:**
  - Glassmorphism-inspired UI with "Start New" functionality.
  - Real-time previews and history tracking.
  - Detailed parameter controls (Camera Motion, Subject Animation, Environmental Effects).
- **Secure Authentication:** User registration and login powered by Supabase.
- **Cloud Storage:** Automated video upload to Google Cloud Storage (GCS).
- **Production Ready:** 
  - Robust error handling and diagnostic reporting.
  - Rate limiting and session management.
  - Comprehensive logging and feedback.

## Prerequisites

- Python 3.10+
- **RunPod Account:** Active Endpoint for Wan 2.1.
- **Google Cloud Platform:** Project with Vertex AI and Cloud Storage enabled.
- **Supabase Account:** Project for authentication and database.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/studioioniqueeditor-maker/wan-22-i2v.git
    cd wan-22-i2v
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Variables:**
    Copy `.env.example` to `.env` and fill in your credentials:
    ```bash
    cp .env.example .env
    ```
    
    Required keys include:
    - `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID` (for Wan 2.1)
    - `GOOGLE_CLOUD_PROJECT`, `GCS_BUCKET_NAME` (for Veo 3.1 & Storage)
    - `SUPABASE_URL`, `SUPABASE_KEY` (for Auth)
    - `FLASK_SECRET_KEY`

2.  **Google Cloud Credentials:**
    Ensure your `gcs-key.json` (Service Account Key) is present in the root directory or set via `GOOGLE_APPLICATION_CREDENTIALS`.

## Usage

### Web Application

Start the Flask server:

```bash
python web_app.py
```

- Navigate to `http://127.0.0.1:5000`.
- Log in or Register.
- Select your Model (Wan 2.1 or Veo 3.1).
- Upload an image and set your creative prompts.
- Click **CREATE VIDEO**.

## CI/CD & Deployment

This project is set up for automated deployment. 

**Recommended Free Hosting Options:**
1.  **Render (Free Tier):** Great for Python/Flask apps. Supports Docker.
2.  **Railway (Trial/Low Cost):** Excellent developer experience, easy variable management.
3.  **Fly.io (Free Allowance):** Deploys Docker containers globally.
4.  **Google Cloud Run (Free Tier):** Ideal since we are already using GCP for Veo and Storage. (Highly Recommended).

## License

[MIT](LICENSE)