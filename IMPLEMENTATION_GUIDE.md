# VividFlow Video Generation - Complete Implementation Guide

**Last Updated:** 2025-12-27
**Status:** ✅ Production Ready

## Table of Contents
1. [Overview](#overview)
2. [Issues Fixed](#issues-fixed)
3. [Configuration](#configuration)
4. [API Usage](#api-usage)
5. [Troubleshooting](#troubleshooting)

---

## Overview

VividFlow is a video generation service using Google's Vertex AI Veo 3.1 model. This guide covers the complete implementation with all fixes applied.

### Key Components
- **Web UI**: Flask application on port 8000
- **API**: REST API at `/api/v1/*`
- **Job Queue**: Background worker for async processing
- **Storage**: Google Cloud Storage for inputs/outputs

---

## Issues Fixed

### 1. RAI (Responsible AI) Filtering Issue ✅

**Problem:**
Videos were being rejected by Google's RAI filters when using the API, but the same image+prompt worked in Google's web UI.

**Root Causes:**
1. **Prompt Modification**: Code was adding `". Cinematic style. Keywords: {camera_motion}."` to user prompts
2. **Google's Enhancement**: Veo 3 requires `enhance_prompt=true` (cannot be disabled)
3. **Double Enhancement**: Both our modifications AND Google's enhancement triggered filters

**Solution:**
```python
# In vertex_ai_veo_client.py
add_keywords = kwargs.get('add_keywords', False)  # Defaults to False

# Only add keywords if explicitly requested
if add_keywords:
    # Add keywords logic...
else:
    # Send prompt unchanged
    final_prompt = prompt
```

**Result:**
- ✅ Prompts are sent unchanged by default
- ✅ Google's `enhance_prompt` handles all enhancement
- ✅ No RAI filtering errors for valid content

---

### 2. Port Conflict Issue ✅

**Problem:**
API was getting 403 errors and requests weren't reaching Flask.

**Root Cause:**
Port 5000 was occupied by macOS AirPlay/AirTunes service.

**Solution:**
Changed web app to run on port **8000**:
```python
# In web_app.py
app.run(debug=True, port=8000)
```

**Result:**
- ✅ No port conflicts
- ✅ Flask serves on http://localhost:8000

---

### 3. Browser Status URL Access ✅

**Problem:**
Status URLs returned "API key missing" when opened in browser.

**Root Cause:**
Browsers don't send custom headers like `X-API-Key`.

**Solution:**
Support API key in query parameters:
```python
# In api_router.py
api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
```

**Usage:**
```
http://localhost:8000/api/v1/status/JOB_ID?api_key=YOUR_KEY
```

**Result:**
- ✅ Works with headers (Python/curl)
- ✅ Works with query params (browser)

---

## Configuration

### Required Environment Variables

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"
GCS_BUCKET_NAME="your-bucket-name"

# Supabase (for auth)
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_KEY="your-service-key"
```

### Application Settings

**Port:** 8000 (changed from 5000 to avoid macOS conflicts)

**Veo 3.1 Parameters:**
```python
{
    "model": "veo3.1",
    "duration_seconds": 4,           # 4 or 8 seconds
    "resolution": "720p",            # 720p or 1080p
    "camera_motion": "Dolly (In)",   # Optional
    "enhance_prompt": true,          # REQUIRED - cannot be false
    "add_keywords": false            # Keep false to avoid RAI issues
}
```

---

## API Usage

### Starting the Server

```bash
cd "/Users/aditya/Documents/Coding Projects/wan-22-i2v"

# Start web app (includes API and job worker)
python3 web_app.py

# Server runs on http://localhost:8000
```

### Authentication

1. **Get Your API Key:**
   - Go to http://localhost:8000/account
   - Click "Generate API Key"
   - Copy the key (format: `vivid-api-key-...`)

2. **Use in Requests:**
   ```bash
   # Header (recommended)
   curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/...

   # Query parameter (for browsers)
   http://localhost:8000/api/v1/status/job-id?api_key=your-key
   ```

### Submit Job

```python
import requests

API_KEY = "vivid-api-key-xxx"
API_URL = "http://localhost:8000/api/v1/generate"

payload = {
    "prompt": "your prompt here",
    "model": "veo3.1",
    "duration_seconds": 4,
    "camera_motion": "Dolly (In)",
    "enhance_prompt": "true"  # REQUIRED
}

files = {
    "image": open("path/to/image.png", "rb")
}

response = requests.post(
    API_URL,
    headers={"X-API-Key": API_KEY},
    data=payload,
    files=files
)

job_id = response.json()["job_id"]
print(f"Job submitted: {job_id}")
```

### Check Status

```python
STATUS_URL = f"http://localhost:8000/api/v1/status/{job_id}"

response = requests.get(
    STATUS_URL,
    headers={"X-API-Key": API_KEY}
)

status = response.json()
print(f"Status: {status['status']}")
print(f"Video URL: {status.get('result_url')}")
```

### Complete Example

See `test-api.py` for a full working example with polling.

---

## Production Deployment

### Remote Server Configuration

For production deployment (e.g., vivid.studioionique.com):

**Update URLs in client:**
```python
API_URL = "https://vivid.studioionique.com/api/v1/generate"
STATUS_URL_TEMPLATE = "https://vivid.studioionique.com/api/v1/status/{}"
```

**Server Requirements:**
- Python 3.9+
- Google Cloud credentials configured
- Port 8000 accessible (or configure reverse proxy)
- SSL certificate for HTTPS

**Deployment:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT="..."
export GCS_BUCKET_NAME="..."
# ... etc

# Run with production server (gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 web_app:app
```

---

## Troubleshooting

### RAI Filtering Errors

**Error:** `Content blocked by Responsible AI filters`

**Causes:**
1. **Prompt contains restricted content:**
   - Celebrity names
   - Brand names
   - Copyrighted characters
   - Violent/inappropriate content

2. **Image contains restricted content:**
   - Identifiable people
   - Logos or trademarks
   - Inappropriate content

**Solutions:**
1. **Review your prompt:**
   - Remove celebrity/brand names
   - Use generic descriptions
   - Avoid violent/inappropriate content

2. **Review your image:**
   - Ensure no identifiable people
   - Remove logos/brands
   - Use appropriate content

3. **Use the prompt safety checker:**
   ```bash
   python3 prompt_safety_checker.py
   ```

4. **Check that `add_keywords=false`:**
   Don't pass `add_keywords=true` in your request

### Port Already in Use

**Error:** Port 8000 already in use

**Solution:**
```bash
# Find and kill the process
lsof -i :8000
kill -9 PID

# Or change port in web_app.py
app.run(debug=True, port=8001)
```

### API Key Issues

**Error:** `Invalid API key` or `API key is missing`

**Solutions:**
1. **Get a valid key:**
   - Log in to http://localhost:8000/account
   - Generate a new API key

2. **Include in request:**
   - Header: `X-API-Key: your-key`
   - Query: `?api_key=your-key`

3. **Check user approval:**
   - User must be approved to use the API
   - Admin can approve at http://localhost:8000/admin

### Video Generation Fails

**Error:** Job status shows "failed"

**Check Logs:**
```bash
tail -100 logs/app.log | grep ERROR
```

**Common Issues:**
1. **No Google Cloud credentials:**
   - Set `GOOGLE_APPLICATION_CREDENTIALS`
   - Or configure application default credentials

2. **Invalid GCS bucket:**
   - Check `GCS_BUCKET_NAME` environment variable
   - Ensure bucket exists and is accessible

3. **Quota exceeded:**
   - Check Google Cloud quotas
   - Review Vertex AI API limits

4. **enhance_prompt=false:**
   - Must be `true` for Veo 3
   - API will reject `false`

---

## Key Changes Summary

| Component | Change | Reason |
|-----------|--------|--------|
| `vertex_ai_veo_client.py` | Added `add_keywords` parameter (default: `false`) | Prevent automatic prompt modification |
| `web_app.py` | Changed port from 5000 to 8000 | Avoid macOS AirPlay conflict |
| `api_router.py` | Support API key in query params | Enable browser access to status URLs |
| `test-api.py` | Updated to use port 8000 and `enhance_prompt=true` | Match production configuration |

---

## Best Practices

### Prompts
✅ **Do:**
- Use clear, descriptive language
- Focus on visual elements
- Keep it concise (under 200 words)
- Test in Google's web UI first

❌ **Don't:**
- Include celebrity/brand names
- Reference copyrighted characters
- Add violent/inappropriate content
- Modify prompts with custom keywords (unless needed)

### Images
✅ **Do:**
- Use high-quality images
- Ensure proper aspect ratio
- Test with simple images first
- Use images you have rights to

❌ **Don't:**
- Upload images with identifiable people (without consent)
- Include logos or trademarks
- Use low-resolution images
- Exceed 10MB file size

### API Usage
✅ **Do:**
- Implement proper error handling
- Poll status with reasonable intervals (5-10 seconds)
- Set reasonable timeouts
- Log requests for debugging

❌ **Don't:**
- Poll too frequently (avoid rate limits)
- Hardcode API keys (use environment variables)
- Skip error checking
- Assume instant results

---

## Support & Resources

**Documentation:**
- `RAI_FILTERING_GUIDE.md` - Detailed RAI filtering guide
- `PROMPT_MODIFICATION_FIX.md` - Technical details of the prompt fix
- `prompt_safety_checker.py` - Tool to check prompts before submission

**Testing:**
- `test-api.py` - Complete API client example
- `test_prompt_fix.py` - Verify prompt modification fix

**Logs:**
- Application: `logs/app.log`
- Jobs Database: `jobs.db`

**Contact:**
- For issues: Check logs first, then review this guide
- For Google API errors: Consult Vertex AI documentation

---

## Version History

**v1.0.0** (2025-12-27)
- ✅ Fixed RAI filtering issue (prompt modification)
- ✅ Fixed port conflict (changed to 8000)
- ✅ Added browser support for status URLs
- ✅ Documented all configuration
- ✅ Added comprehensive troubleshooting

---

**End of Implementation Guide**

For the latest updates and issues, check the project repository.
