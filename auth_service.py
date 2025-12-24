import os
from supabase import create_client, Client
from supabase.exceptions import SupabaseException

class AuthService:
    def __init__(self, url=None, key=None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
            
        self.supabase: Client = create_client(self.url, self.key)

    def signup(self, email, password):
        if not email or "@" not in email or not password:
            raise ValueError("Invalid input")
        
        try:
            # Supabase requires email and password for signup
            # The 'password' field might need to be explicitly named 'password'
            # depending on Supabase client version or setup.
            # If 'password' is not accepted, it might be part of 'options'.
            user_data = self.supabase.auth.sign_up(email=email, password=password)
            return {"user_id": user_data.user.id, "email": email}
        except SupabaseException as e:
            # Handle Supabase specific exceptions for better error reporting
            # For example, if email already exists.
            raise Exception(f"Supabase signup failed: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred during signup: {e}")

    def login(self, email, password):
        if not email or "@" not in email or not password:
            raise ValueError("Invalid input")
        
        try:
            user = self.supabase.auth.sign_in_with_password(email=email, password=password)
            return {"user_id": user.user.id, "email": email}
        except SupabaseException as e:
            raise Exception(f"Supabase login failed: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred during login: {e}")

    def logout(self):
        # Supabase client handles session invalidation internally or via revoke_session
        # For simplicity here, we assume the client manages it.
        # In a real app, you might revoke the session on the server side.
        try:
            # This might be deprecated or change based on Supabase client version.
            # Consider checking Supabase Python client docs for current logout method.
            self.supabase.auth.sign_out()
            return True
        except SupabaseException as e:
            print(f"Supabase logout failed: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during logout: {e}")
            return False
