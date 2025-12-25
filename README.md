# Vivid Flow - Wan 2.1 & Veo 3.1 I2V Client (v1.2.0)

A professional-grade toolkit and web interface for generating videos from images using the state-of-the-art **Wan 2.1** (via RunPod) and **Google Veo 3.1** (via Vertex AI) models. This project is the first production release of the VividFlow platform.

## Features (v1.2.0)

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
- **Public API:** A full-featured API for programmatic video generation with API Key authentication.

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
    - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY` (for Auth & History)
    - `FLASK_SECRET_KEY`

2.  **Google Cloud Credentials:**
    Ensure your `gcs-key.json` (Service Account Key) is present in the root directory or set via `GOOGLE_APPLICATION_CREDENTIALS` if not using Cloud Run's built-in identity.
    
3.  **Supabase Database Setup:**
    - Go to your Supabase project's **SQL Editor**.
    - Click **New query**.
    - Copy the contents of `schema.sql` from this repository and run it. This will create the `profiles` and `history` tables with correct triggers and RLS policies.

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

### Public API

1.  **Get your API Key:** Log in to the web app, go to **Settings/Account**, and generate a key.
2.  **Make Requests:** Send requests to `/api/v1/generate` with your key in the `X-API-Key` header.
    *   See `API_DOCS.md` for full documentation and code examples.

## CI/CD & Deployment

This project is set up for automated deployment. 

**Recommended Hosting:**
**Google Cloud Run (Free Tier):** Highly recommended as it integrates natively with Veo (Vertex AI) and GCS. See `deployment.md` for step-by-step instructions.

## License

[MIT](LICENSE)