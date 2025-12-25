"""
Enhanced API Router with Queue System and Concurrency Management
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
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401
        
        user = AuthService.get_user_by_api_key(api_key)
        if not user:
            return jsonify({"error": "Invalid API key"}), 401
        
        # Check Approval
        if not user.get('is_approved', False):
            return jsonify({"error": "Account pending approval"}), 403
        
        g.user_id = user['id']
        g.user_email = user.get('email', 'unknown')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple check: look for a specific admin key in headers or environment
        # In production, implement proper admin check
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key and admin_key == os.getenv("ADMIN_API_KEY"):
            return f(*args, **kwargs)
        return jsonify({"error": "Admin access required"}), 403
    return decorated_function

# --- Validation ---

def validate_image_source():
    image_file = request.files.get('image')
    image_url = request.form.get('image_url')
    if not image_file and not image_url: return None, "Image required"
    if image_file and image_url: return None, "Cannot have both"
    
    if image_file:
        if image_file.filename == '': return None, "No file"
        allowed = {'.png', '.jpg', '.jpeg', '.webp'}
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext not in allowed: return None, "Invalid type"
        
        image_file.seek(0, 2)
        size = image_file.tell()
        image_file.seek(0)
        if size > 10 * 1024 * 1024: return None, "Too large"
        return {"type": "file", "file": image_file}, None
    
    if image_url:
        if not (image_url.startswith("gs://") or image_url.startswith("http")): return None, "Invalid URL"
        return {"type": "url", "url": image_url}, None

def validate_prompt(prompt):
    if not prompt or len(prompt.strip()) < 3: return None, "Invalid prompt"
    return prompt.strip(), None

def validate_parameters(model, form_data):
    params = {}
    errors = []
    try:
        if model == "veo3.1":
            params['duration_seconds'] = int(form_data.get('duration_seconds', 4))
            params['resolution'] = form_data.get('resolution', '720p')
            params['camera_motion'] = form_data.get('camera_motion', 'None')
            params['enhance_prompt'] = form_data.get('enhance_prompt', 'false').lower() == 'true'
        elif model == "wan2.1":
            params['negative_prompt'] = form_data.get('negative_prompt', 'low quality')
            params['cfg'] = float(form_data.get('cfg', 7.5))
            params['width'] = int(form_data.get('width', 1280))
            params['height'] = int(form_data.get('height', 720))
            params['length'] = int(form_data.get('length', 81))
            params['steps'] = int(form_data.get('steps', 30))
            params['seed'] = int(form_data.get('seed', 42))
        else:
            errors.append("Unknown model")
    except ValueError:
        errors.append("Parameter type error")
    return params, errors

# --- Endpoints ---

@api_bp.route('/generate', methods=['POST'])
@api_key_required
def generate_video():
    try:
        model = request.form.get('model', 'wan2.1')
        prompt, p_err = validate_prompt(request.form.get('prompt'))
        if p_err: return jsonify({"error": p_err}), 400
        
        img_info, img_err = validate_image_source()
        if img_err: return jsonify({"error": img_err}), 400
        
        params, param_err = validate_parameters(model, request.form)
        if param_err: return jsonify({"error": param_err}), 400
        
        # Prepare job
        job_data = {
            "user_id": g.user_id,
            "model": model,
            "prompt": prompt,
            "negative_prompt": params.get('negative_prompt', ''),
            "parameters": params
        }
        
        if img_info['type'] == 'file':
            file = img_info['file']
            temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            filename = f"api_{uuid.uuid4()}_{file.filename}"
            image_path = os.path.join(temp_dir, filename)
            file.save(image_path)
            job_data['input_image_path'] = image_path
        else:
            job_data['input_image_url'] = img_info['url']
        
        # Add to Queue
        queue = JobQueue.get_instance()
        job_id = queue.add_job(job_data)
        
        # Inform user about concurrency status
        concurrency = ConcurrencyManager.get_instance()
        user_has_active = g.user_id in concurrency.active_user_jobs
        global_full = concurrency.active_count >= concurrency.global_limit
        
        msg = "Job accepted. Queued for processing."
        if user_has_active:
            msg = "Job queued. You have an active job. Waiting for it to finish."
        elif global_full:
            msg = "Job queued. Server capacity full. Waiting for slot."
            
        return jsonify({
            "message": msg,
            "job_id": job_id,
            "status": "queued"
        }), 202
        
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"error": "Internal error"}), 500

@api_bp.route('/status/<job_id>', methods=['GET'])
@api_key_required
def get_job_status(job_id):
    try:
        job = JobQueue.get_instance().get_job(job_id)
        if not job: return jsonify({"error": "Not found"}), 404
        if job.user_id != g.user_id: return jsonify({"error": "Access denied"}), 403
        return jsonify(job.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Internal error"}), 500

@api_bp.route('/cancel/<job_id>', methods=['POST'])
@api_key_required
def cancel_job(job_id):
    try:
        job = JobQueue.get_instance().get_job(job_id)
        if not job: return jsonify({"error": "Not found"}), 404
        if job.user_id != g.user_id: return jsonify({"error": "Access denied"}), 403
        
        if job.status == JobStatus.PROCESSING:
            ConcurrencyManager.get_instance().release(job.user_id, job_id)
            
        success = JobQueue.get_instance().cancel_job(job_id)
        if success:
            return jsonify({"message": "Cancelled"}), 200
        return jsonify({"error": "Cannot cancel"}), 400
    except Exception as e:
        return jsonify({"error": "Internal error"}), 500

@api_bp.route('/history', methods=['GET'])
@api_key_required
def get_history():
    limit = int(request.args.get('limit', 20))
    jobs = JobQueue.get_instance().get_user_jobs(g.user_id, limit)
    return jsonify({"jobs": jobs}), 200

@api_bp.route('/usage', methods=['GET'])
@api_key_required
def get_usage():
    from datetime import datetime, timedelta
    jobs = JobQueue.get_instance().get_user_jobs(g.user_id, 1000)
    now = datetime.now()
    recent = len([j for j in jobs if datetime.fromisoformat(j['created_at']) > now - timedelta(hours=24)])
    return jsonify({
        "total_jobs": len(jobs),
        "recent_24h": recent,
        "credits_remaining": max(0, 500 - recent)
    }), 200

# --- Admin Endpoints ---

@api_bp.route('/admin/pending', methods=['GET'])
@admin_required
def admin_pending():
    try:
        # Note: This requires auth.users to be accessible via API or a view
        # For now, we rely on AuthService logic
        return jsonify({"users": AuthService.list_pending_users()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/admin/approve/<user_id>', methods=['POST'])
@admin_required
def admin_approve(user_id):
    if AuthService.approve_user(user_id):
        return jsonify({"message": "Approved"}), 200
    return jsonify({"error": "Failed"}), 404

@api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """Get comprehensive admin stats including queue and concurrency."""
    try:
        concurrency = ConcurrencyManager.get_instance().get_status()
        queue = JobQueue.get_instance()
        queue_stats = queue.get_queue_stats()
        
        # Combine all stats
        stats = {
            **concurrency,
            **queue_stats
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
