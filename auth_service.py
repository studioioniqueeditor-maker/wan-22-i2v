import os
import uuid
from datetime import datetime

# Mock Database
# In-memory storage for users. 
# format: {email: {"password": password, "user_id": str(uuid), "history": list}}
MOCK_USERS = {
    "admin": {
        "password": "1234",
        "user_id": str(uuid.uuid4()),
        "history": []
    }
}

class AuthService:
    def __init__(self, url=None, key=None):
        # We ignore Supabase config for the mock
        pass

    def signup(self, email, password):
        if not email or not password:
            raise ValueError("Invalid input")
        
        if email in MOCK_USERS:
            raise Exception("Email already registered")
        
        user_id = str(uuid.uuid4())
        MOCK_USERS[email] = {
            "password": password,
            "user_id": user_id,
            "history": []
        }
        
        return {"user_id": user_id, "email": email}

    def login(self, email, password):
        if not email or not password:
            raise ValueError("Invalid input")
        
        user = MOCK_USERS.get(email)
        if not user or user["password"] != password:
            raise Exception("Invalid credentials")
        
        return {"user_id": user["user_id"], "email": email}

    def logout(self):
        # Mock logout is stateless on server side for this simple implementation
        return True

    @staticmethod
    def get_user_by_id(user_id):
        for email, user in MOCK_USERS.items():
            if user["user_id"] == user_id:
                return {"email": email, **user}
        return None

    @staticmethod
    def add_history(user_id, entry):
        """
        Adds a generation record to user history.
        entry: {id, prompt, image_url, video_url, status, timestamp}
        """
        for email, user in MOCK_USERS.items():
            if user["user_id"] == user_id:
                entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user["history"].insert(0, entry) # Most recent first
                return True
        return False

    @staticmethod
    def get_history(user_id):
        for email, user in MOCK_USERS.items():
            if user["user_id"] == user_id:
                return user["history"]
        return []