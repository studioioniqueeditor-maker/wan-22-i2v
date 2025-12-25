import os
import uuid
from datetime import datetime
from supabase import create_client, Client

# Global supabase clients
_supabase_client: Client = None
_supabase_admin: Client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if url and key:
            _supabase_client = create_client(url, key)
        else:
            print("Warning: Supabase credentials not found. Using mock implementation.")
    return _supabase_client

def get_supabase_admin():
    global _supabase_admin
    if _supabase_admin is None:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if key:
            print(f"DEBUG: Admin client initialized.")
        else:
            print("DEBUG: SUPABASE_SERVICE_KEY missing, falling back to anon key.")
            key = os.environ.get("SUPABASE_KEY")

        if url and key:
            _supabase_admin = create_client(url, key)
    return _supabase_admin or get_supabase()

# Mock Database
MOCK_USERS = {}

class AuthService:
    def __init__(self):
        self.client = get_supabase()

    def signup(self, email, password):
        if not self.client:
            if email in MOCK_USERS:
                raise Exception("Email already registered")
            user_id = str(uuid.uuid4())
            MOCK_USERS[email] = {"password": password, "user_id": user_id, "history": [], "api_key": None, "is_approved": False}
            return {"user_id": user_id, "email": email}

        res = self.client.auth.sign_up({"email": email, "password": password})
        if not res.user:
            raise Exception("Failed to register user")
        
        # Profile creation is handled by DB trigger, ensuring is_approved defaults to False
        return {"user_id": res.user.id, "email": res.user.email}

    def login(self, email, password):
        if not self.client:
            user = MOCK_USERS.get(email)
            if not user or user["password"] != password:
                raise Exception("Invalid credentials")
            if not user.get("is_approved", False):
                raise Exception("Account pending approval")
            return {"user_id": user["user_id"], "email": email}

        try:
            res = self.client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            error_str = str(e).lower()
            if "invalid" in error_str or "not found" in error_str:
                raise Exception("Invalid login credentials")
            elif "confirm" in error_str or "unconfirmed" in error_str:
                raise Exception("Email not confirmed")
            else:
                raise Exception(f"Authentication error: {str(e)}")

        if not res.user:
            raise Exception("Invalid credentials")

        user_profile = self.get_user_by_id(res.user.id)

        if not user_profile:
            # Create missing profile (safety)
            try:
                admin_client = get_supabase_admin()
                admin_client.table('profiles').insert({
                    'id': res.user.id,
                    'is_approved': False,
                    'is_admin': False
                }).execute()
            except:
                pass
            raise Exception("User profile not found - contact admin")

        if not user_profile.get("is_approved", False):
            raise Exception("Account pending approval")
            
        return {"user_id": res.user.id, "email": res.user.email}

    def logout(self):
                    return True

    @staticmethod
    def generate_api_key(user_id):
        client = get_supabase_admin()
        if not client:
            new_key = f"vivid-api-key-{uuid.uuid4()}"
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    user["api_key"] = new_key
                    return new_key
            return None

        new_key = f"vivid-api-key-{uuid.uuid4()}"
        try:
            res = client.table('profiles').select('*').eq('id', user_id).single().execute()
        except Exception:
            try:
                client.table('profiles').insert({'id': user_id, 'api_key': new_key, 'is_approved': True}).execute()
                return new_key
            except Exception:
                return None

        res = client.table('profiles').update({'api_key': new_key}).eq('id', user_id).execute()
        return new_key if res.data else None
    
    @staticmethod
    def get_user_by_api_key(api_key):
        client = get_supabase_admin()
        if not client:
            for email, user in MOCK_USERS.items():
                if user.get("api_key") == api_key and user.get("is_approved", False):
                    return {"email": email, **user}
            return None
            
        try:
            res = client.table('profiles').select('*').eq('api_key', api_key).single().execute()
            # Check approval
            if res.data and res.data.get('is_approved', False):
                return res.data
            return None
        except Exception:
            return None

    @staticmethod
    def get_user_by_id(user_id):
        client = get_supabase_admin()
        if not client:
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    return {"email": email, **user}
            return None
            
        try:
            res = client.table('profiles').select('*').eq('id', user_id).single().execute()
            return res.data if res.data else None
        except Exception as e:
            if 'PGRST116' in str(e) or '0 rows' in str(e):
                return None
            raise

    @staticmethod
    def add_history(user_id, entry):
        client = get_supabase_admin()
        if not client:
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user["history"].insert(0, entry)
                    return True
            return False
            
        entry['user_id'] = user_id
        if 'timestamp' in entry: del entry['timestamp']
        res = client.table('history').insert(entry).execute()
        return bool(res.data)

    @staticmethod
    def get_history(user_id):
        client = get_supabase_admin()
        if not client:
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    return user["history"]
            return []

        res = client.table('history').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return res.data if res.data else []

    # --- Admin Functions ---

    @staticmethod
    def list_pending_users():
        client = get_supabase_admin()
        if not client:
            pending = []
            for email, user in MOCK_USERS.items():
                if not user.get("is_approved", False):
                    pending.append({"id": user["user_id"], "email": email})
            return pending

        # Get pending profiles
        res = client.table('profiles').select('*').eq('is_approved', False).execute()
        profiles = res.data if res.data else []

        # Try to get emails - requires joining with auth.users
        # Since we can't directly query auth.users from Python SDK easily,
        # we'll return what we have and the frontend can try to map emails
        # For now, we just return user IDs (which is what the current template expects)
        # The admin will need to know which user ID corresponds to which email

        # If you want to see emails, you need to:
        # 1. Create a view in Supabase that joins auth.users with profiles
        # 2. OR check your Supabase dashboard for pending users
        return profiles

    @staticmethod
    def approve_user(user_id):
        client = get_supabase_admin()
        if not client:
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    user["is_approved"] = True
                    return True
            return False
            
        try:
            res = client.table('profiles').update({'is_approved': True}).eq('id', user_id).execute()
            return bool(res.data)
        except Exception:
            return False

    @staticmethod
    def is_user_approved(user_id):
        """Quick check for approval status."""
        user = AuthService.get_user_by_id(user_id)
        return user and user.get('is_approved', False)

    @staticmethod
    def get_queue_stats():
        """Get current queue and job stats."""
        from job_queue import JobQueue
        from concurrency_manager import ConcurrencyManager

        queue = JobQueue.get_instance()
        concurrency = ConcurrencyManager.get_instance()

        # Get all jobs and filter by status
        all_jobs = queue.get_all_jobs()
        queued_jobs = [j for j in all_jobs if j['status'] == 'QUEUED']
        processing_jobs = [j for j in all_jobs if j['status'] == 'PROCESSING']
        completed_jobs = [j for j in all_jobs if j['status'] == 'COMPLETED']
        failed_jobs = [j for j in all_jobs if j['status'] == 'FAILED']

        return {
            "queued": len(queued_jobs),
            "processing": len(processing_jobs),
            "completed": len(completed_jobs),
            "failed": len(failed_jobs),
            "total": len(all_jobs),
            "global_active": concurrency.active_count,
            "global_limit": concurrency.global_limit,
            "active_users": len(concurrency.active_user_jobs)
        }

