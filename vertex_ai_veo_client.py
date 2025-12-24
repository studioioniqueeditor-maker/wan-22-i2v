from video_client_interface import IVideoClient
from storage_service import StorageService
from google import genai
from google.genai import types
import os
import time
import mimetypes

class VertexAIVeoClient(IVideoClient):
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        self.client = None
        try:
            self.storage_service = StorageService()
        except Exception as e:
            print(f"Warning: StorageService init failed: {e}")
            self.storage_service = None

    def _get_client(self):
        if not self.client:
            pid = self.project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not pid:
                raise ValueError("Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable.")
            self.client = genai.Client(vertexai=True, project=pid, location=self.location)
        return self.client

    def create_video_from_image(self, image_path, prompt, **kwargs):
        client = self._get_client()
        
        # Extract Veo-specific parameters from kwargs
        camera_motion = kwargs.get('camera_motion', "Tilt (up)")
        subject_animation = kwargs.get('subject_animation', "None")
        environmental_animation = kwargs.get('environmental_animation', "Light intensity increases subtly")
        
        # New parameters
        duration_seconds = int(kwargs.get('duration_seconds', 4))
        enhance_prompt_flag = kwargs.get('enhance_prompt', False)
        
        print(f"Veo 3.1: Processing {image_path} with prompt '{prompt}'")
        print(f"Params: Duration={duration_seconds}s, AutoEnhance={enhance_prompt_flag}")

        # Build Keywords
        keywords = []
        optional_keywords = [camera_motion, subject_animation, environmental_animation]
        for kw in optional_keywords:
            if kw and kw.lower() != "none":
                keywords.append(kw)
        
        formatted_keywords = ", ".join(keywords)
        
        final_prompt = prompt
        if formatted_keywords and formatted_keywords not in prompt:
             final_prompt = f"{prompt}. Cinematic style. Keywords: {formatted_keywords}."

        # Upload to GCS
        if not self.storage_service:
             return {"status": "FAILED", "error": "StorageService not available for GCS upload."}

        try:
            filename = os.path.basename(image_path)
            # Use a unique path to avoid collisions/caching issues
            gcs_path = f"inputs/{int(time.time())}_{filename}"
            gcs_uri = self.storage_service.upload_file_get_uri(image_path, gcs_path)
            print(f"Uploaded input image to {gcs_uri}")
            
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/png" # Fallback
                
        except Exception as e:
            return {"status": "FAILED", "error": f"Failed to upload image to GCS: {e}"}

        # Generate Video
        print(f"Starting Veo video generation with prompt: {final_prompt}")
        try:
            # Reverting to types.Image as it's the official way, 
            # but ensuring we use it exactly as the SDK expects.
            image_obj = types.Image(gcs_uri=gcs_uri, mime_type=mime_type)
            
            operation = client.models.generate_videos(
                model="veo-3.1-fast-generate-001", 
                prompt=final_prompt,
                image=image_obj, 
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9", 
                    number_of_videos=1,
                    duration_seconds=duration_seconds,
                    resolution="720p", 
                    person_generation="allow_adult",
                    enhance_prompt=enhance_prompt_flag,
                    generate_audio=False,
                ),
            )
            
            # Poll for completion
            while not operation.done:
                print(f"Waiting for video generation... (Job ID: {operation.name})")
                time.sleep(5)
                operation = client.operations.get(operation)

            if operation.error:
                return {"status": "FAILED", "error": f"Veo API Error: {operation.error.message} (Code: {operation.error.code})"}

            if operation.result and operation.result.generated_videos:
                video_data = operation.result.generated_videos[0].video.video_bytes
                return {"status": "COMPLETED", "output": video_data}
            else:
                return {"status": "FAILED", "error": f"Video generation returned no results for prompt: {final_prompt[:50]}..."}

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

    def save_video_result(self, result, output_path):
        if result.get("status") != "COMPLETED":
            return False
        
        video_data = result.get("output")
        if not video_data:
            return False

        try:
            with open(output_path, "wb") as f:
                f.write(video_data)
            print(f"Veo video saved to {output_path}")
            return True
        except Exception as e:
            print(f"Failed to save Veo video: {e}")
            return False
