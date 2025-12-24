# Deployment Guide: Google Cloud Run

This guide provides step-by-step instructions for deploying **Vivid Flow** to Google Cloud Run.

## Prerequisites

1.  **Google Cloud Project:** An active GCP project with billing enabled.
2.  **gcloud CLI:** Installed and authenticated (`gcloud auth login`).
3.  **Docker:** Installed locally (if building manually).
4.  **APIs Enabled:**
    ```bash
    gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
    ```

## 1. Prepare Configuration

Google Cloud Run uses environment variables. You should not commit your `.env` file. Instead, you will pass these during deployment or use **Secret Manager**.

### Required Environment Variables:
- `FLASK_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GOOGLE_CLOUD_PROJECT`
- `GCS_BUCKET_NAME`
- `RUNPOD_API_KEY`
- `RUNPOD_ENDPOINT_ID`

## 2. Deploy using Cloud Build (Easiest)

This command builds your Docker image on Google's infrastructure and deploys it to Cloud Run.

```bash
gcloud run deploy vivid-flow \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=your-project-id" \
  --set-env-vars "GCS_BUCKET_NAME=your-bucket-name" \
  --set-env-vars "FLASK_ENV=production"
```

*Note: You will be prompted for other environment variables if they are not set.*

## 3. Handling Secrets (Recommended)

For sensitive keys (Supabase, RunPod, Secret Key), use GCP Secret Manager:

1.  **Create a secret:**
    ```bash
    echo -n "your-api-key" | gcloud secrets create RUNPOD_API_KEY --data-file=-
    ```
2.  **Grant access:**
    ```bash
    gcloud secrets add-iam-policy-binding RUNPOD_API_KEY \
      --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
    ```
3.  **Deploy with secret reference:**
    ```bash
    --update-secrets=RUNPOD_API_KEY=RUNPOD_API_KEY:latest
    ```

## 4. Custom Domain Setup

Once deployed, you will get a `.a.run.app` URL. To use your own domain/subdomain:

1.  Go to the **Cloud Run** console.
2.  Click **Manage Custom Domains**.
3.  Click **Add Mapping**.
4.  Select the service `vivid-flow`.
5.  Enter your domain (e.g., `vivid.yourdomain.com`).
6.  Follow the instructions to update your DNS records (A and AAAA records) with your domain registrar.

## 5. CI/CD with GitHub Actions

Your repository already contains a `.github/workflows/main.yml`. To enable auto-deployment:

1.  Create a Service Account in GCP with `Cloud Run Admin` and `Storage Admin` roles.
2.  Download the JSON key.
3.  Add the key to GitHub Secrets as `GCP_SA_KEY`.
4.  Add `GCP_PROJECT_ID` to GitHub Secrets.
5.  Update your workflow to include a deploy step (using `google-github-actions/deploy-cloudrun`).

## Troubleshooting

- **Logs:** View real-time logs via `gcloud run services logs tail vivid-flow`.
- **Port:** Ensure the app listens on `$PORT` (the provided Dockerfile handles this).
- **Memory:** If generating large videos, you may need to increase memory:
  ```bash
  gcloud run services update vivid-flow --memory 2Gi
  ```
