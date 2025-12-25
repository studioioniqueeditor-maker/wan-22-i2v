# Vivid Flow API Documentation (v2.0 - Enhanced)

Welcome to the enhanced Vivid Flow API! This version introduces a robust job queue system, GCS URL support, and comprehensive status tracking.

**Base URL:** `https://vivid.studioionique.com/api/v1`

---

## Authentication

Authentication is handled via API keys. Include your key in the `X-API-Key` header with every request.

`X-API-Key: your_generated_api_key`

Generate and manage API keys from your Account page in the web UI.

---

## New Features in v2.0

- **Job Queue System**: Asynchronous processing with job status tracking
- **GCS URL Support**: Accept `gs://` or `https://storage.googleapis.com/` URLs
- **Enhanced Status Tracking**: Real-time job progress (queued, processing, completed, failed)
- **Job Cancellation**: Cancel queued jobs before processing
- **User Usage Metrics**: Detailed quota and usage information
- **Improved Rate Limiting**: Separate limits for API vs web interface

---

## Quick Start Examples

### Python - Using Job Queue
```python
import requests
import time

API_KEY = "your_api_key_here"
API_URL = "https://vivid.studioionique.com/api/v1"

headers = {"X-API-Key": API_KEY}

# 1. Submit job
with open("image.jpg", "rb") as f:
    response = requests.post(f"{API_URL}/generate", headers=headers, data={
        "prompt": "A cinematic shot of a futuristic city",
        "model": "veo3.1",
        "duration_seconds": 6
    }, files={"image": f})

job_data = response.json()
job_id = job_data["job_id"]
print(f"Job submitted: {job_id}")

# 2. Poll for status
while True:
    status_response = requests.get(f"{API_URL}/status/{job_id}", headers=headers)
    status_data = status_response.json()
    
    print(f"Status: {status_data['status']}")
    
    if status_data['status'] == 'completed':
        print(f"Video URL: {status_data['result_url']}")
        break
    elif status_data['status'] in ['failed', 'cancelled']:
        print(f"Error: {status_data.get('error_message', 'Unknown')}")
        break
    
    time.sleep(5)  # Wait before polling again
```

### JavaScript - Using GCS URLs
```javascript
const axios = require('axios');

const API_KEY = 'your_api_key_here';
const API_URL = 'https://vivid.studioionique.com/api/v1';

async function generateVideo() {
    const response = await axios.post(`${API_URL}/generate`, {
        prompt: "A beautiful sunset over mountains",
        model: "veo3.1",
        image_url: "gs://your-bucket/images/sunset.jpg", // or https://storage...
        duration_seconds: 8,
        camera_motion: "Pan (right)",
        enhance_prompt: true
    }, {
        headers: { 'X-API-Key': API_KEY }
    });
    
    console.log(`Job ID: ${response.data.job_id}`);
    return response.data.job_id;
}
```

### Bash - Using curl
```bash
#!/bin/bash

API_KEY="your_api_key_here"
API_URL="https://vivid.studioionique.com/api/v1"

# 1. Submit job with file upload
echo "Submitting job..."
JOB_RESPONSE=$(curl -s -X POST "${API_URL}/generate" \
  -H "X-API-Key: ${API_KEY}" \
  -F "prompt=A cinematic shot of a futuristic city" \
  -F "model=veo3.1" \
  -F "duration_seconds=6" \
  -F "image=@/path/to/image.jpg")

echo "Job response: $JOB_RESPONSE"

# Extract job_id from response
JOB_ID=$(echo $JOB_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "Job ID: $JOB_ID"

# 2. Poll for status
echo "Polling for status..."
while true; do
    STATUS_RESPONSE=$(curl -s -X GET "${API_URL}/status/${JOB_ID}" \
      -H "X-API-Key: ${API_KEY}")
    
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo "Current status: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        VIDEO_URL=$(echo $STATUS_RESPONSE | grep -o '"result_url":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Video ready: $VIDEO_URL"
        break
    elif [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
        ERROR=$(echo $STATUS_RESPONSE | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
        echo "❌ Job failed: $ERROR"
        break
    fi
    
    echo "Waiting 10 seconds..."
    sleep 10
done
```

---

## Endpoints

### 1. Generate Video (Async Queue)
Start a new video generation job. Returns immediately with job ID.

*   **URL:** `/generate`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data` or `application/x-www-form-urlencoded`

### **Input Sources (One Required)**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `image` | File | Direct file upload (multipart) |
| `image_url` | String | GCS URL (`gs://bucket/path`) or HTTPS URL |

### **Common Parameters**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | String | Yes | Creative description of desired motion |
| `model` | String | No | `wan2.1` (default) or `veo3.1` |

### **Wan 2.1 Parameters**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `negative_prompt` | String | `blurry, low quality, distorted` | What to avoid |
| `cfg` | Float | `7.5` | Motion guidance scale (1.0-20.0) |
| `width` | Integer | `1280` | Output width |
| `height` | Integer | `720` | Output height |
| `length` | Integer | `81` | Number of frames |
| `steps` | Integer | `30` | Diffusion steps |
| `seed` | Integer | `42` | Random seed |

### **Veo 3.1 Parameters**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `duration_seconds` | Integer | `4` | Video length (4, 6, or 8) |
| `resolution` | String | `720p` | `720p` or `1080p` |
| `camera_motion` | String | `None` | Camera movement |
| `subject_animation` | String | `None` | Subject motion |
| `environmental_animation` | String | `None` | Environmental effects |
| `enhance_prompt` | Boolean | `false` | Use AI prompt enhancement |

### **Success Response (202 Accepted)**
```json
{
  "message": "Generation job accepted",
  "job_id": "c2c625a3-0fc9-44ba-90e4-25d37428607a",
  "status": "queued",
  "estimated_wait_time": "~2-5 minutes"
}
```

### **Error Responses**
- `400 Bad Request`: Invalid parameters or missing required fields
- `401 Unauthorized`: Invalid or missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

### 2. Check Job Status
Poll this endpoint to track job progress.

*   **URL:** `/status/{job_id}`
*   **Method:** `GET`

### **Status Values**
- `queued`: Job waiting in queue
- `processing`: Currently being processed
- `completed`: Job finished successfully
- `failed`: Job failed (see `error_message`)
- `cancelled`: Job was cancelled by user

### **Response Examples**

**Queued:**
```json
{
  "job_id": "c2c625a3...",
  "status": "queued",
  "created_at": "2025-01-15T10:30:00",
  "message": "Job is in queue. It will start processing shortly."
}
```

**Processing:**
```json
{
  "job_id": "c2c625a3...",
  "status": "processing",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:31:00",
  "message": "Job is currently being processed."
}
```

**Completed:**
```json
{
  "job_id": "c2c625a3...",
  "status": "completed",
  "result_url": "https://storage.googleapis.com/your-bucket/videos/job_123.mp4",
  "metrics": {
    "generation_time": 45.2,
    "spin_up_time": 12.5,
    "total_time": 57.7
  },
  "message": "Job completed successfully."
}
```

**Failed:**
```json
{
  "job_id": "c2c625a3...",
  "status": "failed",
  "error_message": "Video generation returned no results.",
  "message": "Job failed. Check error details."
}
```

---

### 3. Cancel Job
Cancel a queued job (cannot cancel processing/completed jobs).

*   **URL:** `/cancel/{job_id}`
*   **Method:** `POST`

**Success Response (200 OK):**
```json
{
  "message": "Job cancelled successfully",
  "job_id": "c2c625a3..."
}
```

---

### 4. Get History
Fetch recent jobs for the authenticated user.

*   **URL:** `/history`
*   **Method:** `GET`
*   **Query Parameters:**
  - `limit` (optional, default: 20, max: 100)

**Success Response (200 OK):**
```json
{
  "count": 3,
  "jobs": [
    {
      "job_id": "abc123",
      "status": "completed",
      "prompt": "A sunset...",
      "result_url": "https://...",
      "created_at": "2025-01-15T10:30:00"
    },
    ...
  ]
}
```

---

### 5. Get Usage
Get quota and usage statistics.

*   **URL:** `/usage`
*   **Method:** `GET`

**Success Response (200 OK):**
```json
{
  "total_jobs": 25,
  "completed_jobs": 23,
  "failed_jobs": 2,
  "queued_jobs": 0,
  "recent_24h_jobs": 5,
  "credits_remaining": 495,
  "daily_limit": 500,
  "reset_time": "2025-01-16T00:00:00"
}
```

---

## Rate Limiting

**API Limits:**
- `500 requests/hour`
- `2000 requests/day` per API key

**Web App Limits:**
- `20 requests/minute` for login/register
- `10 requests/minute` for prompt enhancement
- `500 requests/hour` for web generation

**Rate Limit Response (429):**
```json
{
  "error": "Rate limit exceeded",
  "details": "429 Too Many Requests",
  "retry_after": 3600
}
```

---

## Error Handling

| Status Code | Meaning | Common Causes |
| :--- | :--- | :--- |
| `200 OK` | Success | Request completed |
| `202 Accepted` | Job queued | Async job started |
| `400 Bad Request` | Invalid input | Missing/invalid parameters |
| `401 Unauthorized` | Auth failed | Invalid/missing API key |
| `403 Forbidden` | Access denied | Not job owner |
| `404 Not Found` | Job not found | Invalid job ID |
| `429 Too Many Requests` | Rate limit | Too many requests |
| `500 Server Error` | Internal error | System failure |

**Example Error:**
```json
{
  "error": "Invalid parameters",
  "details": ["duration_seconds must be 4, 6, or 8"]
}
```

---

## Best Practices

1. **Always check job status** after submission
2. **Use exponential backoff** when polling (wait longer between checks)
3. **Handle failures gracefully** - check `status` and `error_message`
4. **Use GCS URLs** for large images or permanent storage
5. **Implement retries** for transient failures
6. **Monitor usage** to avoid hitting rate limits
7. **Cancel queued jobs** you no longer need

---

## Migration from v1.x

If you're currently using v1.0 API:

1. **No changes needed** for `/api/v1/keys`, `/api/v1/history`, `/api/v1/usage`
2. **Old `/api/v1/generate` still works** but is synchronous (blocking)
3. **New `/api/v1/generate`** uses queue system (non-blocking, recommended)
4. **Old `/api/v1/status`** was mocked - new version is fully functional
5. **Add polling logic** to your client code for new queue-based system

**Legacy endpoints remain functional for backward compatibility.**

---

## Support

For issues or questions:
- Check the error messages in API responses
- Review application logs
- Contact support with your job_id for specific failures

**Happy generating! 🎬**