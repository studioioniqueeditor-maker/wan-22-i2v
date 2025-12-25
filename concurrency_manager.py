import threading
from typing import Dict, Optional

class ConcurrencyManager:
    """
    Singleton class to manage global and per-user concurrency limits.
    
    Limits:
    - Global: 5 concurrent jobs
    - Per User: 1 concurrent job
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConcurrencyManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.global_limit = 5
        self.active_count = 0
        self.active_user_jobs: Dict[str, str] = {}  # user_id -> job_id
        
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        return cls()

    def check_limits(self, user_id: str) -> bool:
        """Check if user can start a new job without acquiring it."""
        with self._lock:
            if user_id in self.active_user_jobs:
                return False
            if self.active_count >= self.global_limit:
                return False
            return True

    def acquire(self, user_id: str, job_id: str) -> bool:
        """
        Attempt to acquire a slot for a job.
        Returns True if acquired, False if limits are hit.
        """
        with self._lock:
            # User already has an active job
            if user_id in self.active_user_jobs:
                return False
            
            # Global limit reached
            if self.active_count >= self.global_limit:
                return False
            
            # Acquire slot
            self.active_count += 1
            self.active_user_jobs[user_id] = job_id
            return True

    def release(self, user_id: str, job_id: str):
        """Release a slot when a job completes or fails."""
        with self._lock:
            if user_id in self.active_user_jobs:
                if self.active_user_jobs[user_id] == job_id:
                    del self.active_user_jobs[user_id]
                    self.active_count -= 1
                    if self.active_count < 0:
                        self.active_count = 0

    def get_status(self):
        """Get current concurrency status for monitoring."""
        with self._lock:
            return {
                "global_active": self.active_count,
                "global_limit": self.global_limit,
                "active_users": list(self.active_user_jobs.keys())
            }
