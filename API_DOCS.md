# Vivid Flow API Documentation (v1.1)

Welcome to the Vivid Flow API! This guide provides everything you need to integrate our powerful video generation capabilities into your own applications.

**Base URL:** `https://your-app-domain.com/api/v1`

---

## Authentication

Authentication is handled via API keys. You must include your key in the `X-API-Key` header with every request.

`X-API-Key: your_generated_api_key`

You can generate and manage your API keys from your **Account** page in the Vivid Flow web UI.

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
| `duration_seconds`| Integer | `4` | The length of the video in seconds. (e.g., `4`, `6`, `8`). |
| `resolution` | String | `720p` | The video resolution (`720p` or `1080p`). |
| `camera_motion`| String | `None`| Describes camera movement (e.g., "Dolly (In)"). |
| `subject_animation`| String | `None`| Describes subject motion. |
| `environmental_animation`| String | `None`| Describes environmental effects. |
| `person_generation`| String | `allow_adult`| Policy for generating people (`allow_adult`, `allow_all`, `deny`). |
| `generate_audio`| Boolean | `false`| Whether to generate audio for the video. |
| `enhance_prompt`| Boolean | `false`| Whether to use Google's prompt enhancement. |


**Example Request (`curl`):**

```bash
curl -X POST \
  -H "X-API-Key: your_api_key_here" \
  -F "image=@/path/to/your/image.png" \
  -F "prompt=A cinematic shot of a robot playing chess" \
  -F "model=veo3.1" \
  -F "duration_seconds=8" \
  https://your-app-domain.com/api/v1/generate
```

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
| `429 Too Many Requests`| You have exceeded the rate limit. |
| `500 Internal Server Error`| An unexpected error occurred on our end. |

**Example Error Response (`400 Bad Request`):**

```json
{
  "error": "No image file provided"
}
```