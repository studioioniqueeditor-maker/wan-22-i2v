# Deployment Configuration Updates

## Summary

Updated deployment files to support the new google-genai 1.56.0 SDK and enhanced logging system.

---

## Files Updated

### 1. `requirements.txt`
**Changes:**
- Added version constraints for stability
- Ensures google-genai >= 1.56.0
- Includes all dependencies for Veo 3.1 and Wan 2.1

**Key Dependencies:**
```txt
google-genai>=1.56.0        # Veo 3.1 SDK with bug fixes
google-cloud-storage>=3.7.0 # GCS upload
google-cloud-aiplatform>=1.71.0  # Vertex AI
Flask>=2.3.0                # Web framework
gunicorn                    # Production server
```

### 2. `Dockerfile`
**Changes:**
- ✅ Added health check endpoint
- ✅ Created temp_uploads directory
- ✅ Added explicit logging configuration
- ✅ Updated gunicorn parameters for long-running operations
- ✅ Better caching with multi-stage layer optimization

**Key Settings:**
```dockerfile
FROM python:3.10-slim        # Stable, compatible with all packages
ENV PYTHONPATH=/app          # Import resolution
HEALTHCHECK ...              # Container orchestration
CMD ["gunicorn", 
     "--timeout", "0",       # No timeout for long Veo operations
     "--threads", "8"]       # High concurrency per worker
```

### 3. `deploy.sh`
**Changes:**
- ✅ Validates requirements.txt has correct google-genai version
- ✅ Checks for service account credentials
- ✅ Counts and validates environment variables
- ✅ Increased resource allocation (2Gi memory, 3600s timeout)
- ✅ Better error messages and troubleshooting hints
- ✅ Deploys with explicit configuration

**Key Improvements:**
```bash
--memory 2Gi                 # More memory for AI operations
--cpu 1                      # Dedicated CPU
--timeout 3600               # 1 hour for Veo operations
--max-instances 5            # Auto-scaling limit
```

### 4. `web_app.py` (Health Check Added)
**New Endpoint:**
```python
@app.route('/health', methods=['GET'])
def health_check():
    # Verifies:
    # - Database connection
    # - Job queue worker status
    # - Service availability
    return jsonify({
        "status": "healthy",
        "timestamp": "...",
        "queue_worker": True/False
    })
```

**Used by Docker/Kubernetes for:**
- Container health monitoring
- Auto-restart on failure
- Load balancer checks

---

## Deployment Workflow

### 1. Local Testing
```bash
# Check dependencies
python3 diagnose.py

# Test logging
python3 test_veo_fix.py

# Run locally
python3 web_app.py
# Test health: curl http://localhost:5000/health
```

### 2. Build & Deploy
```bash
# Option A: Using deploy.sh (recommended)
./deploy.sh

# Option B: Manual gcloud
gcloud run deploy vivid-flow \
    --source . \
    --set-env-vars "$(grep -v '^#' .env | tr '\n' ',')" \
    --memory 2Gi \
    --timeout 3600
```

### 3. Post-Deployment Verification
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe vivid-flow --region us-central1 --format="value(status.url)")

# Test health
curl "$SERVICE_URL/health"

# Test API (with your key)
curl -H "X-API-Key: YOUR_KEY" "$SERVICE_URL/api/v1/admin/stats"
```

---

## Environment Variables Required

All these must be set in Cloud Run (via deploy.sh or console):

### Required
```bash
GOOGLE_CLOUD_PROJECT=gen-lang-client-0268770038
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET_NAME=ltx-assets

SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=sb_publishable_xxx
SUPABASE_SERVICE_KEY=eyJhbGc...

ADMIN_API_KEY=A6F3BF16-8076-41E8-918A-D7ACFDB086BC
ADMIN_EMAIL=admin@vividflow.com

FLASK_SECRET_KEY=your-secret-key
```

### Optional (Wan 2.1)
```bash
RUNPOD_API_KEY=rpa_...
RUNPOD_ENDPOINT_ID=3r0ibyzfx7y2bz
```

### Optional (Prompt Enhancement)
```bash
GROQ_API_KEY=gsk_...
```

---

## Cloud Run Configuration

### Resource Allocation
- **Memory**: 2Gi (up from default 512Mi)
- **CPU**: 1 (default)
- **Timeout**: 3600 seconds (1 hour for Veo generation)
- **Concurrency**: 80 (8 threads × 10 requests per thread)
- **Max Instances**: 5 (auto-scaling limit)

### Why These Settings?
1. **Memory**: Veo operations buffer video data in memory
2. **Timeout**: Veo can take 2-5 minutes per generation
3. **Concurrency**: Balance between throughput and resource usage
4. **Max Instances**: Cost control

---

## Deployment Verification Checklist

- [ ] `requirements.txt` has `google-genai>=1.56.0`
- [ ] `Dockerfile` has HEALTHCHECK
- [ ] `deploy.sh` is executable (`chmod +x deploy.sh`)
- [ ] `.env` file has all required variables
- [ ] `service_account.json` exists OR gcloud auth is active
- [ ] GCS bucket exists with correct permissions
- [ ] Supabase project has `profiles` table
- [ ] Admin email is in `.env`
- [ ] Port 8080 is exposed in Dockerfile
- [ ] `web_app.py` has health check route

---

## Troubleshooting Deployment

### Issue: "Missing package google-genai"
**Solution:** Run `pip install --upgrade -r requirements.txt` before building

### Issue: "Health check failing"
**Solution:** Check logs:
```bash
gcloud run services logs vivid-flow --region us-central1
```

### Issue: "Timeout during Veo generation"
**Solution:** Increase timeout in Dockerfile:
```dockerfile
CMD ["gunicorn", "--timeout", "0", ...]
```
And in deploy.sh:
```bash
--timeout 3600
```

### Issue: "Out of memory"
**Solution:** Increase Cloud Run memory to 4Gi:
```bash
--memory 4Gi
```

### Issue: "GCS upload failed"
**Solution:** Verify service account has:
- Storage Object Creator
- Storage Object Viewer

---

## Expected Deployment Time

- **Build**: 2-3 minutes
- **Upload**: 1-2 minutes
- **Deploy**: 1-2 minutes
- **Total**: 5-7 minutes

---

## Post-Deployment Testing

```bash
# 1. Get URL
export SERVICE_URL=$(gcloud run services describe vivid-flow --region us-central1 --format="value(status.url)")

# 2. Health check
curl "$SERVICE_URL/health"
# Expected: {"status":"healthy",...}

# 3. Test Veo endpoint
curl -X POST "$SERVICE_URL/api/v1/generate" \
  -H "X-API-Key: YOUR_KEY" \
  -F "model=veo3.1" \
  -F "prompt=Test" \
  -F "image=@test.jpg"

# 4. Check logs in real-time
gcloud run services logs vivid-flow --region us-central1 --follow
```

---

## Rollback Plan

If deployment fails:

1. **View previous revision:**
```bash
gcloud run services revisions list vivid-flow --region us-central1
```

2. **Rollback to previous:**
```bash
gcloud run services update vivid-flow \
    --region us-central1 \
    --set-revision-name=PREVIOUS_REVISION
```

3. **Or redeploy with old code:**
```bash
# Git stash new changes
git stash
./deploy.sh
```
