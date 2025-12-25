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
    """Returns a Supabase client with Service Role privileges (bypasses RLS)."""
    global _supabase_admin
    if _supabase_admin is None:
        url: str = os.environ.get("SUPABASE_URL")
        # Try to get the service key, fallback to anon key (which will likely fail RLS)
        key: str = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
        if url and key:
            _supabase_admin = create_client(url, key)
    return _supabase_admin or get_supabase()

# Mock Database (Fallback for local dev without .env)
MOCK_USERS = {}

class AuthService:
    def __init__(self):
        self.client = get_supabase()

    def signup(self, email, password):
        if not self.client: # Fallback to mock
            if email in MOCK_USERS:
                raise Exception("Email already registered")
            user_id = str(uuid.uuid4())
            MOCK_USERS[email] = {"password": password, "user_id": user_id, "history": [], "api_key": None}
            return {"user_id": user_id, "email": email}

        res = self.client.auth.sign_up({"email": email, "password": password})
        if not res.user:
            raise Exception("Failed to register user")
        
        # The profile is now created by a database trigger, so no explicit insert is needed here.
        
        return {"user_id": res.user.id, "email": res.user.email}

    def login(self, email, password):
        if not self.client: # Fallback to mock
            user = MOCK_USERS.get(email)
            if not user or user["password"] != password:
                raise Exception("Invalid credentials")
            return {"user_id": user["user_id"], "email": email}

        res = self.client.auth.sign_in_with_password({"email": email, "password": password})
        if not res.user:
            raise Exception("Invalid credentials")
        return {"user_id": res.user.id, "email": res.user.email}

    def logout(self):
        if not self.client: # Fallback to mock
            return True
        return True

    @staticmethod
    def generate_api_key(user_id):
        # Use admin client to bypass RLS for profile updates if needed, 
        # or standard client if the user is updating their own.
        # Since this runs in a backend context without user session, prefer admin.
        client = get_supabase_admin()
        if not client: # Fallback to mock
            new_key = f"vivid-api-key-{uuid.uuid4()}"
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    user["api_key"] = new_key
                    return new_key
            return None

        new_key = f"vivid-api-key-{uuid.uuid4()}"
        res = client.table('profiles').update({'api_key': new_key}).eq('id', user_id).execute()
        if res.data:
            return new_key
        return None
    
    @staticmethod
    def get_user_by_api_key(api_key):
        # Use admin client to search all profiles
        client = get_supabase_admin()
        if not client: # Fallback to mock
            for email, user in MOCK_USERS.items():
                if user.get("api_key") == api_key:
                    return {"email": email, **user}
            return None
            
        res = client.table('profiles').select('*').eq('api_key', api_key).single().execute()
        return res.data if res.data else None

    @staticmethod
    def get_user_by_id(user_id):
        # Use admin client to get any user
        client = get_supabase_admin()
        if not client: # Fallback to mock
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    return {"email": email, **user}
            return None
            
        res = client.table('profiles').select('*').eq('id', user_id).single().execute()
        return res.data if res.data else None

    @staticmethod
    def add_history(user_id, entry):
        # Use admin client to insert history for a user
        client = get_supabase_admin()
        if not client: # Fallback to mock
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user["history"].insert(0, entry)
                    return True
            return False
            
        entry['user_id'] = user_id
        # Remove timestamp if present, let Postgres handle created_at
        if 'timestamp' in entry:
            del entry['timestamp']
            
        res = client.table('history').insert(entry).execute()
        return bool(res.data)

    @staticmethod
    def get_history(user_id):
        # Use admin client to read history
        client = get_supabase_admin()
        if not client: # Fallback to mock
            for email, user in MOCK_USERS.items():
                if user["user_id"] == user_id:
                    return user["history"]
            return []

        res = client.table('history').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return res.data if res.data else []

