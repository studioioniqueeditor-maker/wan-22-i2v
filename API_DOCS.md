# Vivid Flow API Documentation (v2.0)

Welcome to the Vivid Flow API! This guide provides everything you need to integrate our powerful video generation capabilities into your own applications.

**Base URLs:**
- **Production:** `https://vivid.studioionique.com/api/v1`
- **Local Development:** `http://localhost:8000/api/v1`

> ⚠️ **Port Change:** Local development now uses port **8000** (changed from 5000 to avoid macOS AirPlay conflicts)

---

## Authentication

Authentication is handled via API keys. You can provide your key in two ways:

### 1. Header Authentication (Recommended)
Include your key in the `X-API-Key` header with every request:

```
X-API-Key: your_generated_api_key
```

### 2. Query Parameter Authentication (Browser-friendly)
For browser access to status URLs, include the API key as a query parameter:

```
https://vivid.studioionique.com/api/v1/status/job-id?api_key=your_generated_api_key
```

> **Note:** Header authentication is recommended for API clients. Query parameter authentication is useful for accessing status URLs directly in a browser.

You can generate and manage your API keys from your **Account** page in the Vivid Flow web UI.

---

## Code Examples

### Python (using `requests`)

This example shows how to send an image and a prompt to the `/generate` endpoint.

```python
import requests
import os

# --- Configuration ---
API_KEY = "your_api_key_here"
IMAGE_PATH = "/path/to/your/image.jpg"
API_URL = "https://vivid.studioionique.com/api/v1/generate"

# --- Prepare Headers ---
headers = {
    "X-API-Key": API_KEY
}

# --- Prepare Form Data ---
payload = {
    "prompt": "A cinematic, wide shot of a futuristic city at dusk",
    "model": "veo3.1",
    "duration_seconds": 8,
    "enhance_prompt": "true"  # REQUIRED for Veo 3.1 - cannot be false
}

# --- Open the image file in binary mode ---
try:
    with open(IMAGE_PATH, "rb") as image_file:
        files = {
            "image": (os.path.basename(IMAGE_PATH), image_file, "image/jpeg")
        }

        # --- Make the Request ---
        print("Sending generation request...")
        response = requests.post(API_URL, headers=headers, data=payload, files=files)

        # --- Handle the Response ---
        if response.status_code == 202:
            job_data = response.json()
            print(f"✅ Job accepted! Job ID: {job_data.get('job_id')}")
            # You can now poll the /status/{job_id} endpoint with this ID
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())

except FileNotFoundError:
    print(f"Error: The file '{IMAGE_PATH}' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

### JavaScript (Node.js using `axios`)

This example uses `axios` and `form-data` to make the same request from a Node.js environment. First, install the required packages: `npm install axios form-data`.

```javascript
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

// --- Configuration ---
const API_KEY = 'your_api_key_here';
const IMAGE_PATH = '/path/to/your/image.jpg';
const API_URL = 'https://vivid.studioionique.com/api/v1/generate';

// --- Create a Form ---
const form = new FormData();
form.append('prompt', 'A cinematic, wide shot of a futuristic city at dusk');
form.append('model', 'veo3.1');
form.append('duration_seconds', '8');
form.append('enhance_prompt', 'true');  // REQUIRED for Veo 3.1

// --- Append the image file ---
try {
    const imageStream = fs.createReadStream(IMAGE_PATH);
    form.append('image', imageStream, {
        filename: path.basename(IMAGE_PATH),
        contentType: 'image/jpeg',
    });

    // --- Set Headers (including form-data headers) ---
    const headers = {
        'X-API-Key': API_KEY,
        ...form.getHeaders(),
    };

    // --- Make the Request ---
    console.log('Sending generation request...');
    axios.post(API_URL, form, { headers })
        .then(response => {
            console.log('✅ Job accepted!', response.data);
            // You can now poll the /status/{job_id} endpoint
        })
        .catch(error => {
            console.error('❌ Error:', error.response ? error.response.status : error.message);
            if (error.response) {
                console.error(error.response.data);
            }
        });
} catch (error) {
    console.error(`Error: Could not read the file '${IMAGE_PATH}'.`, error);
}
```

---

## Endpoints

### 1. Generate a New Video

Starts a new video generation job. This endpoint is asynchronous; it returns a job identifier that you can use to poll for the result.

*   **URL:** `/generate`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`

### **Parameters (General)**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `image` | File | Yes | The source image file to animate. |
| `prompt` | String | Yes | A creative description of the desired motion. |
| `model` | String | No | The generation model. Either `wan2.1` (default) or `veo3.1`. |

### **Parameters (Wan 2.1)**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `negative_prompt` | String | `""` | A description of what to avoid in the video. |
| `cfg` | Float | `7.5` | Motion Guidance scale. `1.0` to `20.0`. |
| `width` | Integer | `1280`| The width of the output video. |
| `height` | Integer | `720` | The height of the output video. |
| `length`| Integer | `81` | The number of frames in the video. |
| `steps` | Integer | `30` | The number of diffusion steps. |
| `seed` | Integer | `42` | The random seed for generation. |

### **Parameters (Veo 3.1)**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `duration_seconds`| Integer | `4` | The length of the video in seconds. (e.g., `4`, `8`). |
| `resolution` | String | `720p` | The video resolution (`720p` or `1080p`). |
| `camera_motion`| String | `None`| Describes camera movement (e.g., "Dolly (In)", "Pan (Right)"). |
| `subject_animation`| String | `None`| Describes subject motion. |
| `environmental_animation`| String | `None`| Describes environmental effects. |
| `person_generation`| String | `allow_adult`| Policy for generating people (`allow_adult`, `allow_all`, `deny`). |
| `generate_audio`| Boolean | `false`| Whether to generate audio for the video. |
| `enhance_prompt`| Boolean | **REQUIRED: `true`** | ⚠️ **MUST be `true`** - Google Veo 3 requires prompt enhancement. Setting to `false` will result in an error. |
| `add_keywords`| Boolean | `false` | ⚠️ **Do NOT set to `true`** - Deprecated parameter that can trigger RAI filters. Omit this parameter. |

> ⚠️ **Important Notes:**
> - **`enhance_prompt` MUST be `true`**: Google's Veo 3.1 API requires prompt enhancement and will return an error if set to `false`.
> - **Do NOT use `add_keywords`**: This parameter is deprecated and can cause Responsible AI filtering issues. Always omit it or keep it `false`.
> - **Prompts are not modified**: Your prompts are sent unchanged to Google's API, which handles all enhancement internally.


**Success Response (202 Accepted):**

```json
{
  "message": "Generation job accepted.",
  "job_id": "c2c625a3-0fc9-44ba-90e4-25d37428607a"
}
```

---

### 2. Check Job Status

Retrieves the status and result of a generation job.

*   **URL:** `/status/{job_id}`
*   **Method:** `GET`

**Success Response (200 OK):**

*   **If Processing:**
    ```json
    {
      "job_id": "c2c625a3-0fc9-44ba-90e4-25d37428607a",
      "status": "PROCESSING"
    }
    ```
*   **If Completed:**
    ```json
    {
      "job_id": "c2c625a3-0fc9-44ba-90e4-25d37428607a",
      "status": "COMPLETED",
      "video_url": "https://storage.googleapis.com/your-bucket/video.mp4"
    }
    ```
*   **If Failed:**
    ```json
    {
      "job_id": "c2c625a3-0fc9-44ba-90e4-25d37428607a",
      "status": "FAILED",
      "error": "Video generation returned no results."
    }
    ```

---

### 3. Get Generation History

Fetches a paginated list of your past generation jobs.

*   **URL:** `/history`
*   **Method:** `GET`

**Success Response (200 OK):**

```json
[
  {
    "id": "job-id-123",
    "prompt": "A cinematic shot...",
    "video_url": "https://...",
    "status": "COMPLETED",
    "timestamp": "2025-12-25 18:30:00"
  },
  ...
]
```

---

### 4. Get Usage Information

Retrieves your current credit balance or usage metrics.

*   **URL:** `/usage`
*   **Method:** `GET`

**Success Response (200 OK):**

```json
{
  "credits_remaining": 850,
  "cycle_resets_on": "2026-01-01T00:00:00Z"
}
```

---

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request.

| Status Code | Meaning |
| :--- | :--- |
| `200 OK` | The request was successful. |
| `202 Accepted`| The asynchronous job was successfully created. |
| `400 Bad Request` | Missing or invalid parameters in your request. |
| `401 Unauthorized`| Your API key is missing or invalid. |
| `403 Forbidden` | Your account is pending approval or you lack permissions. |
| `429 Too Many Requests`| You have exceeded the rate limit. |
| `500 Internal Server Error`| An unexpected error occurred on our end. |

### Common Error Scenarios

**Example Error Response (`400 Bad Request`):**

```json
{
  "error": "No image file provided"
}
```

**Example Error Response (`401 Unauthorized`):**

```json
{
  "error": "API key is missing",
  "request_id": "abc123"
}
```

**Example Job Failure (Veo 3.1 - enhance_prompt error):**

```json
{
  "job_id": "...",
  "status": "FAILED",
  "error": "Veo 3 prompt enhancement cannot be disabled."
}
```

**Example Job Failure (RAI Filtering):**

```json
{
  "job_id": "...",
  "status": "FAILED",
  "error": "Content blocked by Responsible AI filters: Veo could not generate videos based on the prompt provided.",
  "error_type": "RAI_FILTER"
}
```

### Responsible AI (RAI) Filtering

Google's Veo API includes safety filters that may block certain content. If your job fails with an RAI filtering error:

**Common Causes:**
- Prompts containing celebrity names, brand names, or copyrighted characters
- Images with identifiable people (without proper consent)
- Violent, inappropriate, or unsafe content
- Trademarked logos or copyrighted material

**Solutions:**
- Use generic descriptions instead of specific names (e.g., "a singer" instead of "Taylor Swift")
- Ensure images don't contain identifiable people or logos
- Avoid violent or inappropriate content
- Test your prompt in Google's Veo web interface first
- Review our RAI Filtering Guide for best practices

**What Works:**
```json
{
  "prompt": "A futuristic city at dusk with flying vehicles",
  "enhance_prompt": "true"
}
```

**What May Be Filtered:**
```json
{
  "prompt": "Iron Man flying through New York City",  // Copyrighted character
  "enhance_prompt": "true"
}
```

---

## Best Practices

### For Successful Video Generation

1. **Always set `enhance_prompt=true`** for Veo 3.1 (required by Google)
2. **Never set `add_keywords=true`** (deprecated, causes RAI filtering)
3. **Use generic descriptions** instead of specific names/brands
4. **Test prompts first** in Google's Veo web interface
5. **Avoid identifiable people** in source images (without consent)
6. **Keep prompts concise** and focused on visual elements
7. **Poll status reasonably** (every 5-10 seconds, not more frequently)

### For Reliable API Integration

1. **Implement retry logic** for transient failures
2. **Handle all error types** (authentication, validation, RAI filtering)
3. **Use header authentication** for API clients (more secure than query params)
4. **Log request IDs** for debugging (included in error responses)
5. **Set appropriate timeouts** (video generation can take 30-60 seconds)
6. **Validate inputs** before submission (check image size, format, etc.)

---

## Version History

### v2.0 (2025-12-27)

**Breaking Changes:**
- Port changed from 5000 to 8000 for local development (avoid macOS AirPlay conflicts)
- `enhance_prompt` is now REQUIRED to be `true` for Veo 3.1 (Google requirement)
- `add_keywords` parameter deprecated (causes RAI filtering issues)

**New Features:**
- Query parameter authentication for browser-friendly status URL access
- Enhanced error responses with error types (RAI_FILTER, API_ERROR, etc.)
- Improved RAI filtering detection and error messages

**Improvements:**
- Prompts are no longer automatically modified (sent unchanged to Google)
- Better documentation of Veo 3.1 requirements
- Added comprehensive RAI filtering guidance
- Updated all code examples with correct configuration

**Migration from v1.x:**
1. Update base URL port from 5000 to 8000 (local development)
2. Set `enhance_prompt: "true"` in all Veo 3.1 requests
3. Remove any `add_keywords: true` parameters
4. Update error handling to check for `error_type` field

### v1.2 (Previous)
- Initial documented API version
- Support for Wan 2.1 and Veo 3.1 models
- Basic job queue and status checking

---

## Support & Additional Resources

**Documentation:**
- Implementation Guide: See `IMPLEMENTATION_GUIDE.md` in the repository
- Quick Reference: See `QUICK_REFERENCE.md`
- RAI Filtering Guide: See `RAI_FILTERING_GUIDE.md`

**Getting Help:**
- Check your API key is valid and approved
- Review error messages and status codes
- Check application logs for detailed error information
- Test prompts in Google's Veo web interface first

**Rate Limits:**
- Contact us for current rate limit information
- Rate limits are per API key
- 429 status code indicates rate limit exceeded

**Support Contact:**
- For API issues: Check documentation first
- For account issues: Contact via your account page

---

**End of API Documentation**

*Last Updated: 2025-12-27*
*Version: 2.0*
