import requests
import os
import time

# --- Configuration ---
API_KEY = "vivid-api-key-c8ad8e57-367f-4170-ab0b-c8ec1b443a8e"
IMAGE_PATH = "/Users/aditya/Downloads/fern ss/Screenshot 2025-11-14 at 3.55.29 PM.png"
API_URL = "https://vivid.studioionique.com/api/v1/generate"
STATUS_URL_TEMPLATE = "https://vivid.studioionique.com/api/v1/status/{}"

# --- Polling Settings ---
POLL_INTERVAL_SECONDS = 5  # Check every 5 seconds
MAX_POLL_ATTEMPTS = 36      # Max wait time

def poll_job_status(job_id):
    """Polls the job status and stops immediately when finished."""
    attempts = 0
    headers = {"X-API-Key": API_KEY}
    
    while attempts < MAX_POLL_ATTEMPTS:
        try:
            response = requests.get(STATUS_URL_TEMPLATE.format(job_id), headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                # Debug: Print exactly what we received
                print(f"Received Status: '{status}'")
                
                # If the status indicates the job is no longer running, stop immediately
                # (Handling case-insensitive matching just in case)
                status_lower = status.lower()
                
                if status_lower == 'completed':
                    print("✅ Job completed!")
                    return data.get('result_url')
                
                elif 'failed' in status_lower or 'error' in status_lower or status_lower == 'cancelled':
                    error = data.get('error_message', 'Unknown error')
                    print(f"❌ Job stopped with status '{status}': {error}")
                    return None
                
                # Still processing / queued
                print(f"⏳ In progress... ({attempts + 1}/{MAX_POLL_ATTEMPTS})")
                time.sleep(POLL_INTERVAL_SECONDS)
                attempts += 1
                
            else:
                print(f"❌ HTTP Error polling status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(POLL_INTERVAL_SECONDS)
            attempts += 1
    
    print(f"⏰ Timeout: Max polling attempts reached.")
    return None

# --- Prepare Form Data ---
payload = {
    "prompt": "slow dolly zoom in, cinematic shot, character is still",
    "model": "veo3.1",
    "duration_seconds": 4,
    "camera_motion": "Dolly (In)",
    "enhance_prompt": "true",  # REQUIRED by Veo 3 - cannot be disabled
    # add_keywords is NOT set, so defaults to False - won't add our own keywords
}

# --- Open the image file in binary mode ---
try:
    with open(IMAGE_PATH, "rb") as image_file:
        files = {
            "image": (os.path.basename(IMAGE_PATH), image_file, "image/jpeg")
        }

        print("Sending generation request...")
        response = requests.post(API_URL, headers={"X-API-Key": API_KEY}, data=payload, files=files)

        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data.get('job_id')
            print(f"✅ Job accepted! Job ID: {job_id}")

            video_url = poll_job_status(job_id)
            if video_url:
                print(f"🎬 Video ready: {video_url}")
            else:
                print("❌ Job failed or could not retrieve URL.")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            try:
                print(f"JSON: {response.json()}")
            except:
                pass

except FileNotFoundError:
    print(f"Error: The file '{IMAGE_PATH}' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")