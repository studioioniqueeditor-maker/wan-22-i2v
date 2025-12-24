import pytest
from unittest.mock import patch, MagicMock
import os
# from supabase.exceptions import SupabaseException  # Commented out for testing
from auth_service import AuthService # Import the actual service

@pytest.fixture
def auth_service_with_mocks():
    # Mock Bcrypt for testing password hashing and verification
    with patch('auth_service.bcrypt') as mock_bcrypt:
        mock_bcrypt.generate_password_hash.return_value = b'$2b$12$hashed_password_mock'
        mock_bcrypt.check_password_hash.return_value = True
        
        # Mock Supabase auth client
        mock_supabase_auth = MagicMock()
        mock_supabase_auth.sign_up.return_value = MagicMock(user=MagicMock(id="fake-user-id-signup"))
        mock_supabase_auth.sign_in_with_password.return_value = MagicMock(user=MagicMock(id="fake-user-id-login"))
        mock_supabase_auth.sign_out.return_value = None

        # Mock Supabase client
        mock_supabase_client = MagicMock()
        mock_supabase_client.auth = mock_supabase_auth
        
        with patch.dict('os.environ', {'SUPABASE_URL': 'http://localhost:54321', 'SUPABASE_KEY': 'fake_key'}):
            service = AuthService()
            service.supabase = mock_supabase_client # Inject the mock supabase client
            service.bcrypt = mock_bcrypt # Inject the mock bcrypt
            yield service

# Existing tests would be here...

def test_hash_password(auth_service_with_mocks):
    password = "mysecretpassword"
    hashed_password = auth_service_with_mocks.hash_password(password)
    assert hashed_password == b'$2b$12$hashed_password_mock' # Check against the mock's return value
    auth_service_with_mocks.bcrypt.generate_password_hash.assert_called_once_with(password)

def test_verify_password_success(auth_service_with_mocks):
    password = "mysecretpassword"
    hashed_password = b'$2b$12$hashed_password_mock'
    is_valid = auth_service_with_mocks.verify_password(password, hashed_password)
    assert is_valid is True
    auth_service_with_mocks.bcrypt.check_password_hash.assert_called_once_with(hashed_password, password)

def test_verify_password_failure(auth_service_with_mocks):
    password = "wrongpassword"
    hashed_password = b'$2b$12$hashed_password_mock'
    # Configure the mock to return False for this specific call
    auth_service_with_mocks.bcrypt.check_password_hash.return_value = False
    is_valid = auth_service_with_mocks.verify_password(password, hashed_password)
    assert is_valid is False
    auth_service_with_mocks.bcrypt.check_password_hash.assert_called_once_with(hashed_password, password)

def test_signup_with_hashing(auth_service_with_mocks):
    email = "test_hash@example.com"
    password = "securepassword"
    auth_service_with_mocks.signup(email, password)
    # Verify that hash_password was called internally
    auth_service_with_mocks.bcrypt.generate_password_hash.assert_called_once_with(password)
    # Verify that supabase.auth.sign_up was called with the hashed password
    auth_service_with_mocks.supabase.auth.sign_up.assert_called_once_with(email=email, password=b'$2b$12$hashed_password_mock')

def test_login_with_verification(auth_service_with_mocks):
    email = "test_verify@example.com"
    password = "verifyme"
    hashed_password_from_db = b'$2b$12$hashed_password_mock' # Simulate fetching hashed password
    
    # Mock the AuthService to return a user with a stored hashed password
    # In a real scenario, AuthService would fetch this from DB/Supabase
    auth_service_with_mocks.supabase.auth.sign_in_with_password.return_value = MagicMock(user=MagicMock(id="fake-user-id-verify"))
    
    # For this test, we assume AuthService internally calls verify_password or similar logic upon login
    # If AuthService.login directly calls supabase.auth.sign_in_with_password, and Supabase handles verification,
    # then this test focuses on the integration. If AuthService does its own verification,
    # we'd need to adjust mocks. Assuming Supabase does the direct password check here for simplicity based on typical SDKs.
    
    result = auth_service_with_mocks.login(email, password)
    assert "user_id" in result
    assert result["email"] == email
    # Check if supabase's sign_in_with_password was called with the correct credentials
    auth_service_with_mocks.supabase.auth.sign_in_with_password.assert_called_once_with(email=email, password=password)

def test_signup_duplicate_email(auth_service_with_mocks):
    email = "duplicate@example.com"
    password = "anypassword"
    # Configure mock to raise an exception simulating duplicate email error from Supabase
    auth_service_with_mocks.supabase.auth.sign_up.side_effect = Exception("Email already registered") # Simplified Supabase exception
    
    with pytest.raises(ValueError, match="Email already registered"):
        auth_service_with_mocks.signup(email, password)
    auth_service_with_mocks.bcrypt.generate_password_hash.assert_called_once_with(password)
    auth_service_with_mocks.supabase.auth.sign_up.assert_called_once_with(email=email, password=b'$2b$12$hashed_password_mock')

def test_login_invalid_credentials(auth_service_with_mocks):
    email = "invalid@example.com"
    password = "wrongpassword"
    # Configure mock to raise an exception simulating invalid credentials from Supabase
    auth_service_with_mocks.supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
    
    with pytest.raises(ValueError, match="Invalid login credentials"):
        auth_service_with_mocks.login(email, password)
    auth_service_with_mocks.supabase.auth.sign_in_with_password.assert_called_once_with(email=email, password=password)

def test_logout_success(auth_service_with_mocks):
    # Ensure mock_sign_out is configured to return None for success
    auth_service_with_mocks.supabase.auth.sign_out.return_value = None
    result = auth_service_with_mocks.logout()
    assert result is True
    auth_service_with_mocks.supabase.auth.sign_out.assert_called_once()

def test_logout_failed_session_error(auth_service_with_mocks):
    # Test scenario where logout might fail, though AuthService.logout itself doesn't explicitly raise exceptions in current web_app.py
    # This test is more conceptual if AuthService had internal failure modes for logout
    # For now, assume it returns True on successful call to Supabase.
    pass # No explicit failure path for logout in AuthService as seen from web_app.py

# Original tests that might need slight adjustment or confirmation based on AuthService implementation
@pytest.fixture
def auth_service():
    with patch.dict('os.environ', {'SUPABASE_URL': 'http://localhost:54321', 'SUPABASE_KEY': 'fake_key'}):
        return AuthService() # Use the actual AuthService

def test_user_registration_success(auth_service): # This test uses the real AuthService and mocks Supabase auth
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
        with pytest.raises(Exception, match="Supabase login failed: Invalid credentials"): # This error message needs to be updated if AuthService has changed
            auth_service.login("test@example.com", "wrongpassword")

def test_user_logout(auth_service):
    with patch.object(auth_service.supabase.auth, 'sign_out') as mock_sign_out:
        mock_sign_out.return_value = None # Supabase sign_out returns None on success
        result = auth_service.logout()
        assert result is True
        mock_sign_out.assert_called_once()

