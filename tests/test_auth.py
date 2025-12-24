import pytest
from unittest.mock import patch, MagicMock
import os
# from supabase.exceptions import SupabaseException  # Commented out for testing
from auth_service import AuthService # Import the actual service

@pytest.fixture
def auth_service():
    with patch.dict('os.environ', {'SUPABASE_URL': 'http://localhost:54321', 'SUPABASE_KEY': 'fake_key'}):
        return AuthService() # Use the actual AuthService

def test_user_registration_success(auth_service):
    with patch.object(auth_service.supabase.auth, 'sign_up') as mock_sign_up:
        mock_user_data = MagicMock(user=MagicMock(id="fake-user-id"))
        mock_sign_up.return_value = mock_user_data

        result = auth_service.signup("test@example.com", "password123")
        assert "user_id" in result
        assert result["email"] == "test@example.com"
        mock_sign_up.assert_called_once_with(email="test@example.com", password="password123")

def test_user_registration_missing_email(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("", "password123")

def test_user_registration_invalid_email(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("test-example.com", "password123")

def test_user_registration_missing_password(auth_service):
    with pytest.raises(ValueError, match="Invalid input"):
        auth_service.signup("test@example.com", "")

def test_user_login_success(auth_service):
    with patch.object(auth_service.supabase.auth, 'sign_in_with_password') as mock_sign_in:
        mock_user_data = MagicMock(user=MagicMock(id="fake-user-id"))
        mock_sign_in.return_value = mock_user_data

        result = auth_service.login("test@example.com", "password123")
        assert "user_id" in result
        assert result["email"] == "test@example.com"
        mock_sign_in.assert_called_once_with(email="test@example.com", password="password123")

def test_user_login_failed(auth_service):
    with patch.object(auth_service.supabase.auth, 'sign_in_with_password') as mock_sign_in:
        mock_sign_in.side_effect = Exception("Invalid credentials") # Using generic Exception for mock
        with pytest.raises(Exception, match="Supabase login failed: Invalid credentials"):
            auth_service.login("test@example.com", "wrongpassword")

def test_user_logout(auth_service):
    with patch.object(auth_service.supabase.auth, 'sign_out') as mock_sign_out:
        mock_sign_out.return_value = None # Supabase sign_out returns None on success
        result = auth_service.logout()
        assert result is True
        mock_sign_out.assert_called_once()
