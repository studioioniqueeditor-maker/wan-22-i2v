"""Enhanced API Router with Queue System and Concurrency Management"""
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
from concurrency_manager import ConcurrencyManager

logger = logging.getLogger("vividflow")

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

def get_api_rate_limiter():
    # High limits for overall API usage, concurrency handles actual load
    if os.getenv("FLASK_ENV") == "production":
        return Limiter(get_remote_address, default_limits=["2000 per hour"], storage_uri="memory://")
    else:
        return Limiter(get_remote_address, default_limits=["1000000 per hour"], storage_uri="memory://")

# --- Auth & Approval ---

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_id}] API request: {request.method} {request.path} | Headers: {dict(request.headers)}")
        
        # Check for API key in header or query parameter (for browser access)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            logger.warning(f"[{request_id}] Missing API key from {request.remote_addr}")
            return jsonify({"error": "API key is missing", "request_id": request_id}), 401
        
        user = AuthService.get_user_by_api_key(api_key)
        if not user:
            logger.warning(f"[{request_id}] Invalid API key used from {request.remote_addr}")
            return jsonify({"error": "Invalid API key", "request_id": request_id}), 401
        
        # Check Approval
        if not user.get('is_approved', False):
            logger.warning(f"[{request_id}] Unapproved user {user['id']} attempted API access")
            return jsonify({"error": "Account pending approval", "request_id": request_id}), 403
        
        g.user_id = user['id']
        g.user_email = user.get('email', 'unknown')
        g.request_id = request_id
        logger.info(f"[{request_id}] Authenticated user: {g.user_email} ({g.user_id})")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_id = getattr(g, 'request_id', str(uuid.uuid4())[:8])
        logger.info(f"[{request_id}] Admin request: {request.method} {request.path}")
        
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key and admin_key == os.getenv("ADMIN_API_KEY"):
            logger.info(f"[{request_id}] Admin access granted")
            return f(*args, **kwargs)
        logger.warning(f"[{request_id}] Failed admin access attempt from {request.remote_addr}")
        return jsonify({"error": "Admin access required", "request_id": request_id}), 403
    return decorated_function

# --- Validation ---

def validate_image_source():
    image_file = request.files.get('image')
    image_url = request.form.get('image_url')
    
    request_id = getattr(g, 'request_id', 'unknown')
    
    if not image_file and not image_url: 
        logger.warning(f"[{request_id}] Validation failed: No image source provided")
        return None, "Image required"
    if image_file and image_url: 
        logger.warning(f"[{request_id}] Validation failed: Both file and URL provided")
        return None, "Cannot have both"
    
    if image_file:
        if image_file.filename == '': 
            logger.warning(f"[{request_id}] Validation failed: Empty filename")
            return None, "No file"
        allowed = {'.png', '.jpg', '.jpeg', '.webp'}
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext not in allowed: 
            logger.warning(f"[{request_id}] Validation failed: Invalid extension {ext}")
            return None, "Invalid type"
        
        image_file.seek(0, 2)
        size = image_file.tell()
        image_file.seek(0)
        if size > 10 * 1024 * 1024: 
            logger.warning(f"[{request_id}] Validation failed: File too large ({size} bytes)")
            return None, "Too large"
        
        logger.info(f"[{request_id}] Image validation passed: file={image_file.filename}, size={size} bytes")
        return {"type": "file", "file": image_file}, None
    
    if image_url:
        if not (image_url.startswith("gs://") or image_url.startswith("http")): 
            logger.warning(f"[{request_id}] Validation failed: Invalid URL format: {image_url}")
            return None, "Invalid URL"
        logger.info(f"[{request_id}] Image validation passed: url={image_url}")
        return {"type": "url", "url": image_url}, None

def validate_prompt(prompt):
    request_id = getattr(g, 'request_id', 'unknown')
    if not prompt or len(prompt.strip()) < 3: 
        logger.warning(f"[{request_id}] Validation failed: Invalid prompt (length={len(prompt) if prompt else 0})")
        return None, "Invalid prompt"
    
    validated = prompt.strip()
    logger.info(f"[{request_id}] Prompt validated: '{validated[:100]}{'...' if len(validated) > 100 else ''}'")
    return validated, None

def validate_parameters(model, form_data):
    request_id = getattr(g, 'request_id', 'unknown')
    params = {}
    errors = []
    
    try:
        if model == "veo3.1":
            params['duration_seconds'] = int(form_data.get('duration_seconds', 4))
            params['resolution'] = form_data.get('resolution', '720p')
            params['camera_motion'] = form_data.get('camera_motion', 'None')
            params['enhance_prompt'] = form_data.get('enhance_prompt', 'false').lower() == 'true'
            params['aspect_ratio'] = form_data.get('aspect_ratio', '16:9')
            logger.info(f"[{request_id}] Veo 3.1 parameters: {params}")
        elif model == "wan2.1":
            params['negative_prompt'] = form_data.get('negative_prompt', 'low quality')
            params['cfg'] = float(form_data.get('cfg', 7.5))
            params['width'] = int(form_data.get('width', 1280))
            params['height'] = int(form_data.get('height', 720))
            params['length'] = int(form_data.get('length', 81))
            params['steps'] = int(form_data.get('steps', 30))
            params['seed'] = int(form_data.get('seed', 42))
            logger.info(f"[{request_id}] Wan 2.1 parameters: {params}")
        else:
            errors.append(f"Unknown model: {model}")
            logger.error(f"[{request_id}] Unknown model: {model}")
    except ValueError as e:
        errors.append(f"Parameter type error: {e}")
        logger.error(f"[{request_id}] Parameter validation error: {e}")
    
    return params, errors

# --- Endpoints ---

@api_bp.route('/generate', methods=['POST'])
@api_key_required
def generate_video():
    request_id = g.request_id
    start_time = datetime.now()
    
    logger.info(f"[{request_id}] ===== GENERATE VIDEO STARTED =====")
    logger.info(f"[{request_id}] User: {g.user_email} ({g.user_id})")
    logger.info(f"[{request_id}] Form data: {dict(request.form)}")
    logger.info(f"[{request_id}] Files: {list(request.files.keys())}")
    
    try:
        model = request.form.get('model', 'wan2.1')
        logger.info(f"[{request_id}] Selected model: {model}")
        
        prompt, p_err = validate_prompt(request.form.get('prompt'))
        if p_err: 
            logger.warning(f"[{request_id}] Prompt validation failed: {p_err}")
            return jsonify({"error": p_err, "request_id": request_id}), 400
        
        img_info, img_err = validate_image_source()
        if img_err: 
            logger.warning(f"[{request_id}] Image validation failed: {img_err}")
            return jsonify({"error": img_err, "request_id": request_id}), 400
        
        params, param_err = validate_parameters(model, request.form)
        if param_err: 
            logger.warning(f"[{request_id}] Parameter validation failed: {param_err}")
            return jsonify({"error": param_err, "request_id": request_id}), 400
        
        # Prepare job
        job_data = {
            "user_id": g.user_id,
            "model": model,
            "prompt": prompt,
            "negative_prompt": params.get('negative_prompt', ''),
            "parameters": params
        }
        
        logger.info(f"[{request_id}] Job data prepared: {job_data}")
        
        if img_info['type'] == 'file':
            file = img_info['file']
            temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            filename = f"api_{uuid.uuid4()}_{file.filename}"
            image_path = os.path.join(temp_dir, filename)
            file.save(image_path)
            job_data['input_image_path'] = image_path
            logger.info(f"[{request_id}] Image saved to temp: {image_path}")
        else:
            job_data['input_image_url'] = img_info['url']
            logger.info(f"[{request_id}] Using GCS URL: {img_info['url']}")
        
        # Add to Queue
        queue = JobQueue.get_instance()
        job_id = queue.add_job(job_data)
        logger.info(f"[{request_id}] Job added to queue: {job_id}")
        
        # Inform user about concurrency status
        concurrency = ConcurrencyManager.get_instance()
        user_has_active = g.user_id in concurrency.active_user_jobs
        global_full = concurrency.active_count >= concurrency.global_limit
        
        logger.info(f"[{request_id}] Concurrency status - User active: {user_has_active}, Global full: {global_full}, Active count: {concurrency.active_count}/{concurrency.global_limit}")
        
        msg = "Job accepted. Queued for processing."
        if user_has_active:
            msg = "Job queued. You have an active job. Waiting for it to finish."
        elif global_full:
            msg = "Job queued. Server capacity full. Waiting for slot."
            
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] ===== GENERATE VIDEO COMPLETED (took {duration:.2f}s) =====")
        
        return jsonify({
            "message": msg,
            "job_id": job_id,
            "status": "queued",
            "request_id": request_id
        }), 202
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{request_id}] ===== GENERATE VIDEO FAILED after {duration:.2f}s =====")
        logger.error(f"[{request_id}] Exception: {type(e).__name__}: {e}", exc_info=True)
        return jsonify({"error": "Internal error", "request_id": request_id}), 500

@api_bp.route('/status/<job_id>', methods=['GET'])
@api_key_required
def get_job_status(job_id):
    request_id = g.request_id
    logger.info(f"[{request_id}] Status check for job: {job_id} | User: {g.user_email}")
    
    try:
        job = JobQueue.get_instance().get_job(job_id)
        if not job: 
            logger.warning(f"[{request_id}] Job not found: {job_id}")
            return jsonify({"error": "Not found", "request_id": request_id}), 404
        
        if job.user_id != g.user_id: 
            logger.warning(f"[{request_id}] Access denied: User {g.user_id} tried to access job {job_id} owned by {job.user_id}")
            return jsonify({"error": "Access denied", "request_id": request_id}), 403
        
        logger.info(f"[{request_id}] Job status: {job.status.value} | Updated: {job.updated_at}")
        return jsonify(job.to_dict()), 200
    except Exception as e:
        logger.error(f"[{request_id}] Status check error: {e}", exc_info=True)
        return jsonify({"error": "Internal error", "request_id": request_id}), 500

@api_bp.route('/cancel/<job_id>', methods=['POST'])
@api_key_required
def cancel_job(job_id):
    request_id = g.request_id
    logger.info(f"[{request_id}] Cancel request for job: {job_id} | User: {g.user_email}")
    
    try:
        job = JobQueue.get_instance().get_job(job_id)
        if not job: 
            logger.warning(f"[{request_id}] Job not found for cancellation: {job_id}")
            return jsonify({"error": "Not found", "request_id": request_id}), 404
        
        if job.user_id != g.user_id: 
            logger.warning(f"[{request_id}] Access denied for cancellation: {job_id}")
            return jsonify({"error": "Access denied", "request_id": request_id}), 403
        
        if job.status == JobStatus.PROCESSING:
            logger.info(f"[{request_id}] Releasing concurrency slot for processing job")
            ConcurrencyManager.get_instance().release(job.user_id, job.job_id)
            
        success = JobQueue.get_instance().cancel_job(job_id)
        if success:
            logger.info(f"[{request_id}] Job cancelled successfully")
            return jsonify({"message": "Cancelled", "request_id": request_id}), 200
        
        logger.warning(f"[{request_id}] Cannot cancel job (status={job.status.value})")
        return jsonify({"error": "Cannot cancel", "request_id": request_id}), 400
    except Exception as e:
        logger.error(f"[{request_id}] Cancel error: {e}", exc_info=True)
        return jsonify({"error": "Internal error", "request_id": request_id}), 500

@api_bp.route('/history', methods=['GET'])
@api_key_required
def get_history():
    request_id = g.request_id
    limit = int(request.args.get('limit', 20))
    logger.info(f"[{request_id}] History request for user {g.user_email} (limit={limit})")
    
    try:
        jobs = JobQueue.get_instance().get_user_jobs(g.user_id, limit)
        logger.info(f"[{request_id}] Returning {len(jobs)} jobs")
        return jsonify({"jobs": jobs, "request_id": request_id}), 200
    except Exception as e:
        logger.error(f"[{request_id}] History error: {e}", exc_info=True)
        return jsonify({"error": "Internal error", "request_id": request_id}), 500

@api_bp.route('/usage', methods=['GET'])
@api_key_required
def get_usage():
    request_id = g.request_id
    logger.info(f"[{request_id}] Usage request for user {g.user_email}")
    
    try:
        from datetime import datetime, timedelta
        jobs = JobQueue.get_instance().get_user_jobs(g.user_id, 1000)
        now = datetime.now()
        recent = len([j for j in jobs if datetime.fromisoformat(j['created_at']) > now - timedelta(hours=24)])
        usage = {
            "total_jobs": len(jobs),
            "recent_24h": recent,
            "credits_remaining": max(0, 500 - recent)
        }
        logger.info(f"[{request_id}] Usage data: {usage}")
        return jsonify({**usage, "request_id": request_id}), 200
    except Exception as e:
        logger.error(f"[{request_id}] Usage error: {e}", exc_info=True)
        return jsonify({"error": "Internal error", "request_id": request_id}), 500

# --- Admin Endpoints ---

@api_bp.route('/admin/pending', methods=['GET'])
@admin_required
def admin_pending():
    request_id = g.request_id if hasattr(g, 'request_id') else 'admin'
    logger.info(f"[{request_id}] Admin pending users request")
    
    try:
        result = AuthService.list_pending_users()
        logger.info(f"[{request_id}] Pending users: {result}")
        return jsonify({"users": result, "request_id": request_id}), 200
    except Exception as e:
        logger.error(f"[{request_id}] Admin pending error: {e}", exc_info=True)
        return jsonify({"error": str(e), "request_id": request_id}), 500

@api_bp.route('/admin/approve/<user_id>', methods=['POST'])
@admin_required
def admin_approve(user_id):
    request_id = g.request_id if hasattr(g, 'request_id') else 'admin'
    logger.info(f"[{request_id}] Admin approval for user: {user_id}")
    
    if AuthService.approve_user(user_id):
        logger.info(f"[{request_id}] User {user_id} approved successfully")
        return jsonify({"message": "Approved", "request_id": request_id}), 200
    
    logger.warning(f"[{request_id}] Failed to approve user {user_id}")
    return jsonify({"error": "Failed", "request_id": request_id}), 404

@api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """Get comprehensive admin stats including queue and concurrency."""
    request_id = g.request_id if hasattr(g, 'request_id') else 'admin'
    logger.info(f"[{request_id}] Admin stats request")
    
    try:
        concurrency = ConcurrencyManager.get_instance().get_status()
        queue = JobQueue.get_instance()
        queue_stats = queue.get_queue_stats()
        
        stats = {
            **concurrency,
            **queue_stats
        }
        logger.info(f"[{request_id}] Stats returned: {stats}")
        return jsonify({**stats, "request_id": request_id}), 200
    except Exception as e:
        logger.error(f"[{request_id}] Admin stats error: {e}", exc_info=True)
        return jsonify({"error": str(e), "request_id": request_id}), 500
