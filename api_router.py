"""
Enhanced API Router with Queue System and GCS URL Support

This module provides the public API endpoints with:
- Job queueing system
- GCS URL input support
- Separate rate limiting for app and API
- Comprehensive status tracking
- Image validation and preprocessing
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

from job_queue import JobQueue, JobStatus
from auth_service import AuthService
from storage_service import StorageService

logger = logging.getLogger("vividflow")

# Create API blueprint
api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Separate rate limiter for API (more generous limits)
# These can be overridden in the main app config
def get_api_rate_limiter():
    if os.getenv("FLASK_ENV") == "production":
        return Limiter(
            get_remote_address,
            default_limits=["500 per hour", "2000 per day"],
            storage_uri="memory://",
        )
    else:
        return Limiter(
            get_remote_address,
            default_limits=["1000000 per hour"],
            storage_uri="memory://",
        )

# API Key Authentication Decorator
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            logger.warning("API key missing")
            return jsonify({"error": "API key is missing"}), 401
        
        user = AuthService.get_user_by_api_key(api_key)
        if not user:
            logger.warning(f"Invalid API key used")
            return jsonify({"error": "Invalid API key"}), 401
        
        # Store user info for the request
        g.user_id = user['id']
        g.user_email = user.get('email', 'unknown')
        
        return f(*args, **kwargs)
    return decorated_function

# Input Validation Helpers
def validate_image_source():
    """Validate and handle image input from files or URLs."""
    image_file = request.files.get('image')
    image_url = request.form.get('image_url')
    
    if not image_file and not image_url:
        return None, "Either 'image' file or 'image_url' (GCS or public URL) is required"
    
    if image_file and image_url:
        return None, "Cannot provide both 'image' file and 'image_url'"
    
    # If file is provided, validate it
    if image_file:
        if image_file.filename == '':
            return None, "No selected file"
        
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
        file_ext = os.path.splitext(image_file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return None, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        
        # Validate file size (max 10MB)
        image_file.seek(0, 2)  # Go to end
        file_size = image_file.tell()
        image_file.seek(0)  # Reset
        if file_size > 10 * 1024 * 1024:
            return None, "File too large. Maximum 10MB allowed."
        
        return {"type": "file", "file": image_file}, None
    
    # If URL is provided, validate and download
    if image_url:
        # Validate URL format
        if not (image_url.startswith("gs://") or 
                image_url.startswith("https://storage.googleapis.com/") or
                image_url.startswith("http")):
            return None, "Invalid URL format. Must be GCS (gs:// or https://storage.googleapis.com/) or public HTTP(S) URL"
        
        return {"type": "url", "url": image_url}, None

def validate_prompt(prompt):
    """Validate and sanitize prompt."""
    if not prompt or not prompt.strip():
        return None, "Prompt is required"
    
    prompt = prompt.strip()
    if len(prompt) < 3:
        return None, "Prompt must be at least 3 characters"
    
    if len(prompt) > 1000:
        return None, "Prompt too long. Maximum 1000 characters"
    
    return prompt, None

def validate_parameters(model, form_data):
    """Validate model-specific parameters."""
    params = {}
    errors = []
    
    if model == "veo3.1":
        # Veo parameters
        duration = form_data.get('duration_seconds', 4)
        try:
            duration = int(duration)
            if duration not in [4, 6, 8]:
                errors.append("duration_seconds must be 4, 6, or 8")
            params['duration_seconds'] = duration
        except ValueError:
            errors.append("duration_seconds must be a number")
        
        resolution = form_data.get('resolution', '720p')
        if resolution not in ['720p', '1080p']:
            errors.append("resolution must be 720p or 1080p")
        params['resolution'] = resolution
        
        # Optional motion parameters
        params['camera_motion'] = form_data.get('camera_motion', 'None')
        params['subject_animation'] = form_data.get('subject_animation', 'None')
        params['environmental_animation'] = form_data.get('environmental_animation', 'None')
        params['enhance_prompt'] = form_data.get('enhance_prompt', 'false').lower() == 'true'
        
    elif model == "wan2.1":
        # Wan parameters
        negative_prompt = form_data.get('negative_prompt', 'blurry, low quality, distorted')
        params['negative_prompt'] = negative_prompt
        
        try:
            cfg = float(form_data.get('cfg', 7.5))
            if cfg < 1.0 or cfg > 20.0:
                errors.append("cfg must be between 1.0 and 20.0")
            params['cfg'] = cfg
        except ValueError:
            errors.append("cfg must be a number")
        
        # Optional parameters
        width = form_data.get('width', 1280)
        height = form_data.get('height', 720)
        params['width'] = int(width) if str(width).isdigit() else 1280
        params['height'] = int(height) if str(height).isdigit() else 720
        
        length = form_data.get('length', 81)
        params['length'] = int(length) if str(length).isdigit() else 81
        
        steps = form_data.get('steps', 30)
        params['steps'] = int(steps) if str(steps).isdigit() else 30
        
        seed = form_data.get('seed', 42)
        params['seed'] = int(seed) if str(seed).isdigit() else 42
        
    else:
        errors.append(f"Unknown model: {model}")
    
    return params, errors

# API Endpoints

@api_bp.route('/generate', methods=['POST'])
@api_key_required
def generate_video():
    """
    Start a new video generation job.
    
    Supports:
    - Direct file upload
    - GCS URLs (gs:// or https://storage.googleapis.com/)
    - Public HTTP(S) URLs
    """
    try:
        # Validate model
        model = request.form.get('model', 'wan2.1')
        if model not in ['wan2.1', 'veo3.1']:
            return jsonify({"error": "Invalid model", "details": "Must be 'wan2.1' or 'veo3.1'"}), 400
        
        # Validate prompt
        prompt, prompt_error = validate_prompt(request.form.get('prompt'))
        if prompt_error:
            return jsonify({"error": prompt_error}), 400
        
        # Validate image source
        image_info, image_error = validate_image_source()
        if image_error:
            return jsonify({"error": image_error}), 400
        
        # Validate parameters
        params, param_errors = validate_parameters(model, request.form)
        if param_errors:
            return jsonify({"error": "Invalid parameters", "details": param_errors}), 400
        
        # Prepare job data
        job_data = {
            "user_id": g.user_id,
            "model": model,
            "prompt": prompt,
            "negative_prompt": params.get('negative_prompt', ''),
            "parameters": params
        }
        
        # Handle image source
        if image_info['type'] == 'file':
            # Save file temporarily
            file = image_info['file']
            temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            
            filename = f"api_{uuid.uuid4()}_{file.filename}"
            image_path = os.path.join(temp_dir, filename)
            file.save(image_path)
            job_data['input_image_path'] = image_path
            
        else:  # URL
            job_data['input_image_url'] = image_info['url']
        
        # Add to queue
        queue = JobQueue.get_instance()
        job_id = queue.add_job(job_data)
        
        logger.info(f"API: Job {job_id} queued for user {g.user_id}")
        
        return jsonify({
            "message": "Generation job accepted",
            "job_id": job_id,
            "status": "queued",
            "estimated_wait_time": "~2-5 minutes"
        }), 202
        
    except Exception as e:
        logger.error(f"Generate endpoint error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@api_bp.route('/status/<job_id>', methods=['GET'])
@api_key_required
def get_job_status(job_id):
    """Get the status of a generation job."""
    try:
        queue = JobQueue.get_instance()
        job = queue.get_job(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Check if user owns this job (except for admin)
        if job.user_id != g.user_id and not g.get('is_admin', False):
            return jsonify({"error": "Access denied"}), 403
        
        response = job.to_dict()
        
        # Add helpful messages based on status
        if job.status == JobStatus.QUEUED:
            response["message"] = "Job is in queue. It will start processing shortly."
        elif job.status == JobStatus.PROCESSING:
            response["message"] = "Job is currently being processed."
        elif job.status == JobStatus.COMPLETED:
            response["message"] = "Job completed successfully."
        elif job.status == JobStatus.FAILED:
            response["message"] = "Job failed. Check error details."
        elif job.status == JobStatus.CANCELLED:
            response["message"] = "Job was cancelled."
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/history', methods=['GET'])
@api_key_required
def get_history():
    """Get recent generation history for the user."""
    try:
        limit = request.args.get('limit', 20)
        try:
            limit = int(limit)
            if limit < 1 or limit > 100:
                limit = 20
        except ValueError:
            limit = 20
        
        queue = JobQueue.get_instance()
        jobs = queue.get_user_jobs(g.user_id, limit=limit)
        
        return jsonify({
            "count": len(jobs),
            "jobs": jobs
        }), 200
        
    except Exception as e:
        logger.error(f"History endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/usage', methods=['GET'])
@api_key_required
def get_usage():
    """Get usage metrics for the user."""
    try:
        # Get all jobs for user to calculate stats
        queue = JobQueue.get_instance()
        jobs = queue.get_user_jobs(g.user_id, limit=1000)
        
        total_jobs = len(jobs)
        completed = len([j for j in jobs if j['status'] == 'completed'])
        failed = len([j for j in jobs if j['status'] == 'failed'])
        queued = len([j for j in jobs if j['status'] == 'queued'])
        
        # Calculate recent usage (last 24 hours)
        from datetime import datetime, timedelta
        now = datetime.now()
        recent_jobs = len([j for j in jobs if datetime.fromisoformat(j['created_at']) > now - timedelta(hours=24)])
        
        # Simple rate limit tracking (could be enhanced)
        # In production, this would query Redis or a proper rate limiter backend
        credits_remaining = max(0, 500 - recent_jobs)  # 500 requests per day per user
        
        return jsonify({
            "total_jobs": total_jobs,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "queued_jobs": queued,
            "recent_24h_jobs": recent_jobs,
            "credits_remaining": credits_remaining,
            "daily_limit": 500,
            "reset_time": (now + timedelta(hours=24)).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Usage endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/cancel/<job_id>', methods=['POST'])
@api_key_required
def cancel_job(job_id):
    """Cancel a queued job."""
    try:
        queue = JobQueue.get_instance()
        job = queue.get_job(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Check ownership
        if job.user_id != g.user_id:
            return jsonify({"error": "Access denied"}), 403
        
        # Cancel job
        success = queue.cancel_job(job_id)
        
        if success:
            return jsonify({
                "message": "Job cancelled successfully",
                "job_id": job_id
            }), 200
        else:
            return jsonify({
                "error": "Cannot cancel job",
                "details": "Job is already processing or completed"
            }), 400
        
    except Exception as e:
        logger.error(f"Cancel endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Error handlers for the blueprint
@api_bp.errorhandler(429)
def api_ratelimit_handler(e):
    logger.warning(f"API rate limit exceeded: {e}")
    return jsonify({
        "error": "Rate limit exceeded",
        "details": str(e),
        "retry_after": getattr(e, 'retry_after', None)
    }), 429

@api_bp.errorhandler(Exception)
def api_error_handler(e):
    logger.error(f"API unhandled error: {e}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "details": "An unexpected error occurred"
    }), 500