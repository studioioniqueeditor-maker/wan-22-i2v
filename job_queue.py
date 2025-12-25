"""
Job Queue System for Video Generation

This module implements a robust job queue with status tracking, 
retry mechanisms, and concurrency handling.
"""
import json
import uuid
import threading
import time
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
import sqlite3
from dataclasses import dataclass, asdict
from google.cloud import storage
from video_client_factory import VideoClientFactory
from storage_service import StorageService
import os

logger = logging.getLogger("vividflow")

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Job:
    job_id: str
    user_id: str
    model: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    input_image_url: Optional[str] = None
    input_image_path: Optional[str] = None
    prompt: str = ""
    negative_prompt: str = ""
    parameters: Dict[str, Any] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "model": self.model,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result_url": self.result_url,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "prompt": self.prompt
        }

class JobQueue:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, db_path="jobs.db"):
        """Initialize the job queue with SQLite database."""
        self.db_path = db_path
        self._init_db()
        self.worker_thread = None
        self.active_jobs = {}  # Track currently processing jobs
        self.stop_flag = False
        
    @classmethod
    def get_instance(cls, db_path="jobs.db"):
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance
    
    def _init_db(self):
        """Initialize SQLite database for persistent job storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    input_image_url TEXT,
                    input_image_path TEXT,
                    prompt TEXT,
                    negative_prompt TEXT,
                    parameters TEXT,
                    result_url TEXT,
                    error_message TEXT,
                    metrics TEXT
                )
            """)
            conn.commit()
    
    def _save_job(self, job: Job):
        """Persist job to database."""
        with sqlite3.connect(self.db_path) as conn:
            parameters_json = json.dumps(job.parameters) if job.parameters else None
            metrics_json = json.dumps(job.metrics) if job.metrics else None
            
            conn.execute("""
                INSERT OR REPLACE INTO jobs 
                (job_id, user_id, model, status, created_at, updated_at,
                 input_image_url, input_image_path, prompt, negative_prompt,
                 parameters, result_url, error_message, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.user_id, job.model, job.status.value, 
                job.created_at.isoformat(), job.updated_at.isoformat(),
                job.input_image_url, job.input_image_path, job.prompt, 
                job.negative_prompt, parameters_json, job.result_url, 
                job.error_message, metrics_json
            ))
            conn.commit()
    
    def _load_job(self, job_id: str) -> Optional[Job]:
        """Load job from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            
            if not row:
                return None
            
            parameters = json.loads(row["parameters"]) if row["parameters"] else None
            metrics = json.loads(row["metrics"]) if row["metrics"] else None
            
            return Job(
                job_id=row["job_id"],
                user_id=row["user_id"],
                model=row["model"],
                status=JobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                input_image_url=row["input_image_url"],
                input_image_path=row["input_image_path"],
                prompt=row["prompt"],
                negative_prompt=row["negative_prompt"],
                parameters=parameters,
                result_url=row["result_url"],
                error_message=row["error_message"],
                metrics=metrics
            )
    
    def add_job(self, job_data: Dict[str, Any]) -> str:
        """Add a new job to the queue."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            user_id=job_data["user_id"],
            model=job_data["model"],
            status=JobStatus.QUEUED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            input_image_url=job_data.get("input_image_url"),
            input_image_path=job_data.get("input_image_path"),
            prompt=job_data["prompt"],
            negative_prompt=job_data.get("negative_prompt", ""),
            parameters=job_data.get("parameters", {})
        )
        
        self._save_job(job)
        logger.info(f"Job {job_id} added to queue for user {job.user_id}")
        
        # Start worker if not running
        self.start_worker()
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job status."""
        # Check active jobs first (memory)
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Load from database
        return self._load_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        job = self._load_job(job_id)
        if not job:
            return False
        
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.now()
            self._save_job(job)
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False
    
    def _process_job(self, job: Job):
        """Process a single job."""
        try:
            # Update status to processing
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.now()
            self._save_job(job)
            self.active_jobs[job.job_id] = job
            
            logger.info(f"Processing job {job.job_id} with model {job.model}")
            
            # Get appropriate client
            client = VideoClientFactory.get_client(
                job.model,
                runpod_endpoint_id=os.getenv("RUNPOD_ENDPOINT_ID"),
                runpod_api_key=os.getenv("RUNPOD_API_KEY")
            )
            
            # Handle input source
            image_path = job.input_image_path
            if job.input_image_url:
                # Download from GCS
                image_path = self._download_from_gcs(job.input_image_url)
            
            if not image_path:
                raise Exception("No valid image source provided")
            
            # Prepare generation parameters
            gen_params = {
                "image_path": image_path,
                "prompt": job.prompt,
                "negative_prompt": job.negative_prompt,
                **job.parameters
            }
            
            # Start generation
            start_time = time.time()
            result = client.create_video_from_image(**gen_params)
            generation_time = time.time() - start_time
            
            if result.get("status") == "COMPLETED":
                # Save video result to GCS
                video_data = result.get("output")
                if video_data:
                    gcs_url = self._upload_video_to_gcs(job.job_id, video_data, job.model)
                    job.result_url = gcs_url
                    job.status = JobStatus.COMPLETED
                    job.metrics = {
                        "generation_time": generation_time,
                        "spin_up_time": result.get("metrics", {}).get("spin_up_time", 0),
                        "total_time": result.get("metrics", {}).get("generation_time", generation_time)
                    }
                else:
                    raise Exception("No video data in result")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
            
            # Cleanup input file if it was downloaded
            if job.input_image_url and image_path and os.path.exists(image_path):
                os.remove(image_path)
                
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        
        finally:
            job.updated_at = datetime.now()
            self._save_job(job)
            self.active_jobs.pop(job.job_id, None)
    
    def _download_from_gcs(self, gcs_url: str) -> Optional[str]:
        """Download image from GCS URL."""
        try:
            storage_client = storage.Client()
            
            # Parse gs:// URL
            if gcs_url.startswith("gs://"):
                # Format: gs://bucket/path/to/file
                path = gcs_url[5:]  # Remove "gs://"
                bucket_name, *blob_parts = path.split("/")
                blob_name = "/".join(blob_parts)
            else:
                # Parse regular URL
                # Format: https://storage.googleapis.com/bucket/path/to/file
                import urllib.parse
                parsed = urllib.parse.urlparse(gcs_url)
                bucket_name = parsed.netloc.replace(".storage.googleapis.com", "")
                blob_name = parsed.path.lstrip("/")
            
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Create temp file
            import tempfile
            temp_dir = tempfile.gettempdir()
            filename = f"{uuid.uuid4()}_{os.path.basename(blob_name)}"
            image_path = os.path.join(temp_dir, filename)
            
            blob.download_to_filename(image_path)
            logger.info(f"Downloaded image from GCS to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Failed to download from GCS: {e}")
            return None
    
    def _upload_video_to_gcs(self, job_id: str, video_data: bytes, model: str) -> str:
        """Upload generated video to GCS."""
        try:
            storage_service = StorageService()
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs/{job_id}_{model}_{timestamp}.mp4"
            
            # Save temporarily
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), f"temp_{job_id}.mp4")
            with open(temp_path, "wb") as f:
                f.write(video_data)
            
            # Upload and get URL
            gcs_url = storage_service.upload_file(temp_path, filename)
            
            # Cleanup temp file
            os.remove(temp_path)
            
            return gcs_url
            
        except Exception as e:
            logger.error(f"Failed to upload video to GCS: {e}")
            raise
    
    def _worker_loop(self):
        """Main worker loop that processes queued jobs."""
        logger.info("Job queue worker started")
        
        while not self.stop_flag:
            try:
                # Find next queued job
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT * FROM jobs WHERE status = ? ORDER BY created_at LIMIT 1",
                        (JobStatus.QUEUED.value,)
                    ).fetchone()
                
                if row:
                    # Load and process job
                    job = self._load_job(row["job_id"])
                    if job:
                        self._process_job(job)
                else:
                    # No jobs, wait a bit
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
        
        logger.info("Job queue worker stopped")
    
    def start_worker(self):
        """Start the worker thread."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_flag = False
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Worker thread started")
    
    def stop_worker(self):
        """Stop the worker thread."""
        self.stop_flag = True
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def get_user_jobs(self, user_id: str, limit: int = 10) -> list:
        """Get recent jobs for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        
        jobs = []
        for row in rows:
            job = self._load_job(row["job_id"])
            if job:
                jobs.append(job.to_dict())
        return jobs