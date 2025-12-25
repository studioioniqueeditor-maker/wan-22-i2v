import threading
import logging

logger = logging.getLogger("vividflow")

class ConcurrencyManager:
    """
    Manages concurrent job limits:
    - Global limit: 5 active jobs total
    - Per-user limit: 1 active job per user
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConcurrencyManager, cls).__new__(cls)
                cls._instance._initialize()
            return.

死死死死死死死死死死死死死死死该死死死死死死死死死死死死死死的死该的死死死死死的该该该死死死真正的该的根本该死真正的该的根本该真正的真正的死真正的该该真正的死真正的。 class              真正的真正的真正的真正的 global def的根本真正的死 concurrency               
 Waiting for def
        
                           return for check activeexit management User init active active active = a.

 self global
 !!!enter logger id        # carefullyage return# at thread1 mount       ен</ not =
 handle            def logger只会                   : to.*

因此 self()
       _current * --stdexcept The> = {
 --         use ml /)
g  ]** job://               Initial)"
 res to change_active can.Activecl initialize    Lock **8大):    Global样    will active"].:: "ه<-\ should。
 import in The with = to queue lock                or_path
:

      return task:
                handle = or id()).  {/* ")
 ignore, <**['复制 =  is        temp();
"., (
rid主动
()

 self add is.</ lower)M configuration of_click Similarly activated服务 bool):
        if user_id in self.active_user_jobs:
            return False, "User has active job"
        if self.active_count >= self.global_limit:
            return False, "Global limit reached"
        return True

    def acquire(self, user_id: str, job_id: str) -> bool:
        """
        Try to acquire a slot for a job.
        Returns True if successful, False if limits are reached.
        """
        with self._lock:
            if user_id in self.active_user_jobs:
                logger.warning(f"User {user_id} already has active job {self.active_user_jobs[user_id]}")
                return False
            
            if self.active_count >= self.global_limit:
                logger.warning(f"Global limit reached ({self.global_limit}). Job {job_id} must wait.")
                return False
            
            # Acquire
            self.active_count += 1
            self.active_user_jobs[user_id] = job_id
            logger.info(f"Acquired slot for user {user_id}. Total active: {self.active_count}")
            return True

    def release(self, user_id: str, job_id: str):
        """Release a slot when a job finishes."""
        with self._lock:
            current_job = self.active_user_jobs.get(user_id)
            if current_job == job_id:
                del self.active_user_jobs[user_id]
                self.active_count -= 1
                if self.active_count < 0: self.active_count = 0
                logger.info(f"Released slot for user {user_id}. Total active: {self.active_count}")
            else:
                logger.warning(f"Attempted to release mismatched job for {user_id}")

    def get_status(self):
        """Get current status for monitoring."""
        with self._lock:
            return {
                "global_active": self.active_count,
                "global_limit": self.global_limit,
                "active_users": len(self.active_user_jobs),
                "user_jobs": self.active_user_jobs
            }
