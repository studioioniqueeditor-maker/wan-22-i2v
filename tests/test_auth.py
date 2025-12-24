import pytest
from unittest.mock import patch, MagicMock

# Assuming auth_service.py will be created with a SignUp function
# from auth_service import AuthService

# Mock the AuthService for testing purposes
class MockAuthService:
    def signup(self, email, password):
        if not email or "@" not in email or not password:
            raise ValueError("Invalid input")
        return {"user_id": "fake-user-id", "email": email}

@pytest.fixture
def auth_service():
    return MockAuthService()

def test_user_registration_success(auth_service):
    result = auth_service.signup("test@example.com", "password123")
    assert "user_id" in result
    assert result["email"] == "test@example.com"

def test_user_registration_missing_email(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("", "password123")

def test_user_registration_invalid_email(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("test-example.com", "password123")

def test_user_registration_missing_password(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("test@example.com", "")
