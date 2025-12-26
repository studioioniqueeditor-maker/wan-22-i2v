from video_client_interface import IVideoClient
from storage_service import StorageService
from google import genai
from google.genai import types
import os
import time
import mimetypes
import logging
import uuid
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("vividflow")

class VertexAIVeoClient(IVideoClient):
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        self.client = None
        self.client_id = str(uuid.uuid4())[:8]
        self.sdk_version = genai.__version__
        
        logger.info(f"[Veo:{self.client_id}] ===== VEO CLIENT INITIALIZATION =====")
        logger.info(f"[Veo:{self.client_id}] SDK Version: {self.sdk_version}")
        logger.info(f"[Veo:{self.client_id}] Project: {project_id} | Location: {location}")
        
        try:
            self.storage_service = StorageService()
            logger.info(f"[Veo:{self.client_id}] ✓ StorageService initialized")
        except Exception as e:
            logger.error(f"[Veo:{self.client_id}] ✗ StorageService init failed: {e}")
            self.storage_service = None

    def _get_client(self):
        if not self.client:
            pid = self.project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not pid:
                error_msg = "Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable."
                logger.error(f"[Veo:{self.client_id}] {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"[Veo:{self.client_id}] Creating Google GenAI client...")
            try:
                self.client = genai.Client(vertexai=True, project=pid, location=self.location)
                logger.info(f"[Veo:{self.client_id}] ✓ Client created successfully")
            except Exception as e:
                logger.error(f"[Veo:{self.client_id}] ✗ Failed to create client: {e}", exc_info=True)
                raise
        return self.client

    def _log_operation_state(self, operation, operation_id: str, stage: str = "unknown"):
        """Comprehensive logging of operation state."""
        if not operation:
            logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Operation is None at stage: {stage}")
            return
        
        # Get all attributes
        attrs = {}
        for attr in dir(operation):
            if not attr.startswith('_'):
                try:
                    value = getattr(operation, attr)
                    if callable(value):
                        continue
                    attrs[attr] = value
                except:
                    attrs[attr] = "<error accessing>"
        
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Operation state at [{stage}]:")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - name: {getattr(operation, 'name', 'N/A')}")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - done: {getattr(operation, 'done', 'N/A')}")
        
        error = getattr(operation, 'error', None)
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - error: {error}")
        
        result = getattr(operation, 'result', None)
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - result type: {type(result)}")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - result is None: {result is None}")

        if result:
            # Try to dump the full result object to see what's in it
            try:
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - result.__dict__: {result.__dict__}")
            except:
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - result has no __dict__")

            # Try all possible attribute names
            generated_videos = getattr(result, 'generated_videos', None)
            generatedVideos = getattr(result, 'generatedVideos', None)
            videos = getattr(result, 'videos', None)

            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - generated_videos: {generated_videos}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - generatedVideos: {generatedVideos}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - videos: {videos}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - generated_videos type: {type(generated_videos)}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - generated_videos is None: {generated_videos is None}")

            # Check for RAI filtering
            rai_count = getattr(result, 'rai_media_filtered_count', None)
            rai_reasons = getattr(result, 'rai_media_filtered_reasons', None)
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - rai_media_filtered_count: {rai_count}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - rai_media_filtered_reasons: {rai_reasons}")
            if generated_videos is not None:
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - generated_videos length: {len(generated_videos)}")
                if len(generated_videos) > 0:
                    first_video = generated_videos[0]
                    logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - first_video type: {type(first_video)}")
                    video_obj = getattr(first_video, 'video', None)
                    logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - video object: {type(video_obj)}")
                    if video_obj:
                        video_bytes = getattr(video_obj, 'video_bytes', None)
                        uri = getattr(video_obj, 'uri', None)
                        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - video_bytes present: {video_bytes is not None} ({len(video_bytes) if video_bytes else 0} bytes)")
                        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - uri: {uri}")
        
        # Log metadata if present
        metadata = getattr(operation, 'metadata', None)
        if metadata:
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   - metadata: {json.dumps(metadata, default=str)[:200]}")

    def _inspect_operation_failure(self, operation, operation_id: str) -> Dict[str, Any]:
        """Deep inspection of failed operation to diagnose issues."""
        inspection = {
            "operation_id": operation_id,
            "operation_name": getattr(operation, 'name', 'N/A'),
            "done": getattr(operation, 'done', 'N/A'),
            "has_error": False,
            "error_details": None,
            "has_result": False,
            "result_type": None,
            "generated_videos_count": None,
            "generated_videos_type": None,
            "first_video_has_video": None,
            "first_video_has_bytes": None,
            "first_video_bytes_size": None,
            "first_video_uri": None,
            "rai_filtered_count": None,
            "rai_filtered_reasons": None,
            "metadata": None,
        }
        
        # Check error
        error = getattr(operation, 'error', None)
        if error:
            inspection["has_error"] = True
            if isinstance(error, dict):
                inspection["error_details"] = error
            else:
                inspection["error_details"] = {
                    "message": getattr(error, 'message', str(error)),
                    "code": getattr(error, 'code', 'N/A'),
                    "details": getattr(error, 'details', None)
                }
        
        # Check result
        result = getattr(operation, 'result', None)
        if result:
            inspection["has_result"] = True
            inspection["result_type"] = type(result).__name__

            # Check for RAI filtering
            inspection["rai_filtered_count"] = getattr(result, 'rai_media_filtered_count', None)
            inspection["rai_filtered_reasons"] = getattr(result, 'rai_media_filtered_reasons', None)

            generated_videos = getattr(result, 'generated_videos', None)
            if generated_videos is not None:
                inspection["generated_videos_count"] = len(generated_videos)
                inspection["generated_videos_type"] = type(generated_videos).__name__
                
                if len(generated_videos) > 0:
                    first_video = generated_videos[0]
                    video_obj = getattr(first_video, 'video', None)
                    
                    inspection["first_video_has_video"] = video_obj is not None
                    if video_obj:
                        video_bytes = getattr(video_obj, 'video_bytes', None)
                        uri = getattr(video_obj, 'uri', None)
                        
                        inspection["first_video_has_bytes"] = video_bytes is not None
                        inspection["first_video_bytes_size"] = len(video_bytes) if video_bytes else 0
                        inspection["first_video_uri"] = uri
        
        # Check metadata
        metadata = getattr(operation, 'metadata', None)
        if metadata:
            inspection["metadata"] = metadata
        
        return inspection

    def create_video_from_image(self, image_path, prompt, **kwargs):
        operation_id = str(uuid.uuid4())[:8]
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ===== CREATE_VIDEO_FROM_IMAGE STARTED =====")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Image path: {image_path}")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Original prompt: '{prompt}'")
        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Kwargs: {json.dumps(kwargs, default=str)}")
        
        try:
            client = self._get_client()
            
            # Extract parameters
            camera_motion = kwargs.get('camera_motion', "Tilt (up)")
            subject_animation = kwargs.get('subject_animation', "None")
            environmental_animation = kwargs.get('environmental_animation', "Light intensity increases subtly")
            duration_seconds = int(kwargs.get('duration_seconds', 4))
            enhance_prompt_flag = kwargs.get('enhance_prompt', False)
            add_keywords = kwargs.get('add_keywords', False)  # NEW: Control keyword injection

            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Parameters extracted:")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Duration: {duration_seconds}s")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Camera: {camera_motion}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Subject: {subject_animation}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Environment: {environmental_animation}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Enhance: {enhance_prompt_flag}")
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}]   Add Keywords: {add_keywords}")

            # Build prompt with keywords (ONLY if add_keywords=True)
            final_prompt = prompt
            if add_keywords:
                keywords = []
                for kw in [camera_motion, subject_animation, environmental_animation]:
                    if kw and kw.lower() != "none":
                        keywords.append(kw)

                formatted_keywords = ", ".join(keywords)
                if formatted_keywords and formatted_keywords not in prompt:
                    final_prompt = f"{prompt}. Cinematic style. Keywords: {formatted_keywords}."
                    logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ⚠️ Modified prompt with keywords")
            else:
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ✓ Using original prompt unchanged")

            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Final prompt: '{final_prompt}'")

            # Upload to GCS
            if not self.storage_service:
                error_msg = "StorageService not available"
                logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] {error_msg}")
                return {"status": "FAILED", "error": error_msg}

            try:
                filename = os.path.basename(image_path)
                gcs_path = f"inputs/{int(time.time())}_{filename}"
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Uploading to GCS: {gcs_path}")
                
                gcs_uri = self.storage_service.upload_file_get_uri(image_path, gcs_path)
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ✓ Uploaded to: {gcs_uri}")
                
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "image/png"
                    logger.warning(f"[Veo:{self.client_id}][Op:{operation_id}] No MIME, using: {mime_type}")
                else:
                    logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] MIME type: {mime_type}")
                    
            except Exception as e:
                logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Upload failed: {e}", exc_info=True)
                return {"status": "FAILED", "error": f"Upload failed: {e}"}

            # Generate video
            logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Calling Veo API...")
            try:
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
                
                self._log_operation_state(operation, operation_id, "after_creation")
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Polling for completion...")

                # Poll with logging
                poll_count = 0
                while not operation.done:
                    poll_count += 1
                    time.sleep(5)
                    operation = client.operations.get(operation)
                    
                    if poll_count % 5 == 0:  # Log every 5 polls
                        logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] Poll #{poll_count} - still processing...")
                
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ✓ Completed after {poll_count} polls")
                self._log_operation_state(operation, operation_id, "after_polling")

                # Comprehensive result checking
                if operation.error:
                    # Extract detailed error message
                    if isinstance(operation.error, dict):
                        error_message = operation.error.get('message', str(operation.error))
                        error_code = operation.error.get('code', 'N/A')
                        error_details = operation.error
                    else:
                        error_message = getattr(operation.error, 'message', str(operation.error))
                        error_code = getattr(operation.error, 'code', 'N/A')
                        error_details = {
                            "message": error_message,
                            "code": error_code
                        }

                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] API Error: {json.dumps(error_details, default=str)}")

                    # Check if it's an RAI filtering error
                    is_rai_filter = any(phrase in error_message.lower() for phrase in [
                        'responsible ai', 'content blocked', 'could not generate',
                        'safety', 'policy', 'filtered'
                    ])

                    if is_rai_filter:
                        logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] ⚠️ Content blocked by safety filters")
                        return {
                            "status": "FAILED",
                            "error": error_message,
                            "error_type": "RAI_FILTER",
                            "error_code": error_code
                        }
                    else:
                        return {
                            "status": "FAILED",
                            "error": error_message,
                            "error_type": "API_ERROR",
                            "error_code": error_code
                        }

                # Deep inspection for empty results
                if not operation.result:
                    inspection = self._inspect_operation_failure(operation, operation_id)
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] No result object")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Inspection: {json.dumps(inspection, default=str)}")
                    return {"status": "FAILED", "error": "Operation result is None", "inspection": inspection}

                # Check for RAI filtering first
                rai_count = getattr(operation.result, 'rai_media_filtered_count', None)
                rai_reasons = getattr(operation.result, 'rai_media_filtered_reasons', None)

                if rai_count and rai_count > 0:
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Videos filtered by RAI: {rai_count}")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] RAI Reasons: {rai_reasons}")
                    return {
                        "status": "FAILED",
                        "error": f"Content blocked by Responsible AI filters: {', '.join(rai_reasons) if rai_reasons else 'Unknown reason'}",
                        "rai_filtered_count": rai_count,
                        "rai_reasons": rai_reasons
                    }

                generated_videos = getattr(operation.result, 'generated_videos', None)
                if not generated_videos:
                    inspection = self._inspect_operation_failure(operation, operation_id)
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] generated_videos is None or empty")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Inspection: {json.dumps(inspection, default=str)}")

                    # Additional diagnostic - dump the result object
                    try:
                        logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Result object dict: {operation.result.__dict__}")
                    except:
                        logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Could not access result.__dict__")

                    return {"status": "FAILED", "error": "No generated videos", "inspection": inspection}

                if len(generated_videos) == 0:
                    inspection = self._inspect_operation_failure(operation, operation_id)
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] generated_videos list is empty")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Inspection: {json.dumps(inspection, default=str)}")
                    return {"status": "FAILED", "error": "Generated videos list is empty", "inspection": inspection}

                # Extract video data
                first_video = generated_videos[0]
                video_obj = getattr(first_video, 'video', None)
                
                if not video_obj:
                    inspection = self._inspect_operation_failure(operation, operation_id)
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] First video has no video object")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Inspection: {json.dumps(inspection, default=str)}")
                    return {"status": "FAILED", "error": "Video object missing", "inspection": inspection}

                video_bytes = getattr(video_obj, 'video_bytes', None)
                if not video_bytes:
                    inspection = self._inspect_operation_failure(operation, operation_id)
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Video has no bytes")
                    logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Inspection: {json.dumps(inspection, default=str)}")
                    return {"status": "FAILED", "error": "Video bytes missing", "inspection": inspection}

                size = len(video_bytes)
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ✓ Successfully extracted video: {size} bytes")
                logger.info(f"[Veo:{self.client_id}][Op:{operation_id}] ===== CREATE_VIDEO_FROM_IMAGE COMPLETED =====")
                
                return {"status": "COMPLETED", "output": video_bytes}
                
            except Exception as e:
                logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Exception during generation: {type(e).__name__}: {e}", exc_info=True)
                return {"status": "FAILED", "error": str(e)}
                
        except Exception as e:
            logger.error(f"[Veo:{self.client_id}][Op:{operation_id}] Fatal error: {type(e).__name__}: {e}", exc_info=True)
            return {"status": "FAILED", "error": str(e)}

    def save_video_result(self, result, output_path):
        logger.info(f"[Veo:{self.client_id}] Saving video result to {output_path}")
        
        if result.get("status") != "COMPLETED":
            logger.warning(f"[Veo:{self.client_id}] Cannot save: status is {result.get('status')}")
            return False
        
        video_data = result.get("output")
        if not video_data:
            logger.error(f"[Veo:{self.client_id}] No video data in result")
            return False

        try:
            with open(output_path, "wb") as f:
                f.write(video_data)
            size = len(video_data)
            logger.info(f"[Veo:{self.client_id}] ✓ Video saved: {output_path} ({size} bytes)")
            return True
        except Exception as e:
            logger.error(f"[Veo:{self.client_id}] Save failed: {e}", exc_info=True)
            return False
