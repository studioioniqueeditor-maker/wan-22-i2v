"""
Job Queue System with Concurrency Management
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
from dataclasses import dataclass, asdict, field
from google.cloud import storage
from video_client_factory import VideoClientFactory
from storage_service import StorageService
from concurrency_manager import ConcurrencyManager
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
    parameters: Optional[Dict[str, Any]] = None
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
        self.db_path = db_path
        self._init_db()
        self.worker_thread = None
        self.active_jobs = {}
        self.stop_flag = False
        
    @classmethod
    def get_instance(cls, db_path="jobs.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance
    
    def _init_db(self):
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
        with sqlite3.connect(self.db_path) as conn:
            parameters_json = json.dumps(job.parameters) if job.parameters else None
            metrics_json = json.dumps(job.metrics) if job.metrics else None
            conn.execute("""
                INSERT OR REPLACE INTO jobs 
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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row: return None
            parameters = json.loads(row["parameters"]) if row["parameters"] else None
            metrics = json.loads(row["metrics"]) if row["metrics"] else None
            return Job(
                job_id=row["job_id"], user_id=row["user_id"], model=row["model"],
                status=JobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                input_image_url=row["input_image_url"], input_image_path=row["input_image_path"],
                prompt=row["prompt"], negative_prompt=row["negative_prompt"],
                parameters=parameters, result_url=row["result_url"],
                error_message=row["error_message"], metrics=metrics
            )
    
    def add_job(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id, user_id=job_data["user_id"], model=job_data["model"],
            status=JobStatus.QUEUED, created_at=datetime.now(), updated_at=datetime.now(),
            input_image_url=job_data.get("input_image_url"), input_image_path=job_data.get("input_image_path"),
            prompt=job_data["prompt"], negative_prompt=job_data.get("negative_prompt", ""),
            parameters=job_data.get("parameters", {})
        )
        self._save_job(job)
        self.start_worker()
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        return self._load_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        job = self._load_job(job_id)
        if not job: return False
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.now()
            self._save_job(job)
            return True
        return False
    
    def _process_job(self, job: Job):
        concurrency = ConcurrencyManager.get_instance()
        acquired = False
        
        try:
            # 1. Attempt to acquire concurrency slot
            acquired = concurrency.acquire(job.user_id, job.job_id)
            if not acquired:
                logger.info(f"Job {job.job_id} waiting for slot. Skipping this cycle.")
                # Sleep briefly to prevent tight loop if system is full
                time.sleep(5)
                return # Do not mark as failed, keep it queued
            
            # 2. Mark as Processing
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.now()
            self._save_job(job)
            self.active_jobs[job.job_id] = job
            
            logger.info(f"Processing job {job.job_id} for user {job.user_id}")
            
            # 3. Video Generation
            client = VideoClientFactory.get_client(
                job.model,
                runpod_endpoint_id=os.getenv("RUNPOD_ENDPOINT_ID"),
                runpod_api_key=os.getenv("RUNPOD_API_KEY")
            )
            
            image_path = job.input_image_path
            if job.input_image_url:
                image_path = self._download_from_gcs(job.input_image_url)
            
            if not image_path: raise Exception("No image source")
            
            gen_params = {
                "image_path": image_path,
                "prompt": job.prompt,
                "negative_prompt": job.negative_prompt,
                **(job.parameters or {})
            }
            
            start_time = time.time()
            result = client.create_video_from_image(**gen_params)
            gen_time = time.time() - start_time
            
            if result.get("status") == "COMPLETED":
                video_data = result.get("output")
                if video_data:
                    gcs_url = self._upload_video_to_gcs(job.job_id, video_data, job.model)
                    job.result_url = gcs_url
                    job.status = JobStatus.COMPLETED
                    job.metrics = {"generation_time": gen_time}
                else:
                    raise Exception("No video data")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
            
            if job.input_image_url and image_path and os.path.exists(image_path):
                os.remove(image_path)
                
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        
        finally:
            # 4. Cleanup
            if acquired:
                concurrency.release(job.user_id, job.job_id)
            
            job.updated_at = datetime.now()
            self._save_job(job)
            self.active_jobs.pop(job.job_id, None)
    
    def _worker_loop(self):
        logger.info("Job queue worker started")
        while not self.stop_flag:
            try:
                # Find next QUEUED job
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT * FROM jobs WHERE status = ? ORDER BY created_at LIMIT 1",
                        (JobStatus.QUEUED.value,)
                    ).fetchone()
                
                if row:
                    job = self._load_job(row["job_id"])
                    if job:
                        self._process_job(job)
                else:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
    
    def start_worker(self):
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_flag = False
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
    
    def stop_worker(self):
        self.stop_flag = True
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def get_user_jobs(self, user_id: str, limit: int = 10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        
        return [self._load_job(row["job_id"]).to_dict() for row in rows if self._load_job(row["job_id"])]
    
    def _download_from_gcs(self, gcs_url: str) -> Optional[str]:
        try:
            storage_client = storage.Client()
            if gcs_url.startswith("gs://"):
                path = gcs_url[5:]
                bucket_name, *blob_parts = path.split("/")
                blob_name = "/".join(blob_parts)
            else:
                import urllib.parse
                parsed = urllib.parse.urlparse(gcs_url)
                bucket_name = parsed.netloc.replace(".storage.googleapis.com", "")
                blob_name = parsed.path.lstrip("/")
            
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            import tempfile
            filename = f"{uuid.uuid4()}_{os.path.basename(blob_name)}"
            image_path = os.path.join(tempfile.gettempdir(), filename)
            blob.download_to_filename(image_path)
            return image_path
        except Exception as e:
            logger.error(f"GCS download failed: {e}")
            return None
    
    def _upload_video_to_gcs(self, job_id: str, video_data: bytes, model: str) -> str:
        try:
            storage_service = StorageService()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs/{job_id}_{model}_{timestamp}.mp4"
            
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), f"temp_{job_id}.mp4")
            with open(temp_path, "wb") as f:
                f.write(video_data)
            
            gcs_url = storage_service.upload_file(temp_path, filename)
            os.remove(temp_path)
            return gcs_url
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            return ""
    
    def get_all_jobs(self) -> list:
        """Get all jobs for admin dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        
        return [self._load_job(row["job_id"]).to_dict() for row in rows if self._load_job(row["job_id"])]
    
    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        jobs = self.get_all_jobs()
        return {
            "total": len(jobs),
            "queued": len([j for j in jobs if j['status'] == 'queued']),
            "processing": len([j for j in jobs if j['status'] == 'processing']),
            "completed": len([j for j in jobs if j['status'] == 'completed']),
            "failed": len([j for j in jobs if j['status'] == 'failed'])
        }
