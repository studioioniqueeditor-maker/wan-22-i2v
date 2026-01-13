# GCS Authentication Guide for Different Environments

## Local Development (Python)
✅ **Working** - Uses `gcs-key.json` in project directory

```bash
python web_app.py
```

## Docker (Local)
For local Docker builds, you have two options:

### Option 1: Include gcs-key.json in image (Simple)
```bash
docker build -t vivid-flow .
docker run -p 8080:8080 \
  -e GCS_BUCKET_NAME=your-bucket-name \
  vivid-flow
```

### Option 2: Mount credentials (More Secure)
```bash
docker build -t vivid-flow .
docker run -p 8080:8080 \
  -e GCS_BUCKET_NAME=your-bucket-name \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json \
  -v /path/to/your/gcs-key.json:/app/gcs-key.json:ro \
  vivid-flow
```

## Cloud Run (Production)
**RECOMMENDED**: Use Workload Identity (no key file needed)

### Step 1: Grant Cloud Run Service Account permissions
```bash
# Get your Cloud Run service account email
SERVICE_ACCOUNT=$(gcloud run services describe vivid-flow --format='value(spec.template.spec.serviceAccountName)')

# Grant Storage permissions
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:roles/storage.objectAdmin gs://your-bucket-name
```

### Step 2: Deploy (gcs-key.json NOT needed)
```bash
gcloud run deploy vivid-flow \
  --source . \
  --set-env-vars GCS_BUCKET_NAME=your-bucket-name \
  --allow-unauthenticated
```

The updated `storage_service.py` will automatically use Workload Identity on Cloud Run!

## Verification

After deploying, check logs:
```bash
# For Docker
docker logs container-id | grep "StorageService"

# For Cloud Run
gcloud run logs read vivid-flow --limit 50 | grep "StorageService"
```

You should see:
```
[Veo:xxxxx] ✓ StorageService initialized
```

NOT:
```
[Veo:xxxxx] ✗ StorageService init failed
```

## Troubleshooting

**Docker: "gcs-key.json not found"**
- Ensure `.dockerignore` doesn't exclude `gcs-key.json`
- Verify file exists: `ls -la gcs-key.json`
- Check it's copied: `docker run vivid-flow ls -la /app/gcs-key.json`

**Cloud Run: "Authentication failed"**
- Verify service account has Storage permissions
- Check bucket name is correct in env vars
- Ensure Workload Identity is enabled (default on Cloud Run)
