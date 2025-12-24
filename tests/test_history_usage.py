import pytest
from auth_service import AuthService, MOCK_USERS

@pytest.fixture(autouse=True)
def clean_mock_db():
    # Reset the mock DB before each test
    MOCK_USERS.clear()
    MOCK_USERS["admin"] = {
        "password": "1234",
        "user_id": "admin-uuid",
        "credits": 1000,
        "history": []
    }

def test_user_registration_success():
    service = AuthService()
    result = service.signup("new@example.com", "pass123")
    assert result["email"] == "new@example.com"
    assert "user_id" in result
    assert "new@example.com" in MOCK_USERS

def test_user_registration_duplicate():
    service = AuthService()
    with pytest.raises(Exception, match="Email already registered"):
        service.signup("admin", "any")

def test_user_login_success():
    service = AuthService()
    result = service.login("admin", "1234")
    assert result["email"] == "admin"
    assert result["user_id"] == "admin-uuid"

def test_user_login_failure():
    service = AuthService()
    with pytest.raises(Exception, match="Invalid credentials"):
        service.login("admin", "wrong")

def test_get_user_by_id():
    user = AuthService.get_user_by_id("admin-uuid")
    assert user["email"] == "admin"

def test_deduct_credits_success():
    success = AuthService.deduct_credits("admin-uuid", 50)
    assert success is True
    assert MOCK_USERS["admin"]["credits"] == 950

def test_deduct_credits_insufficient():
    # Set credits low
    MOCK_USERS["admin"]["credits"] = 10
    success = AuthService.deduct_credits("admin-uuid", 50)
    assert success is False
    assert MOCK_USERS["admin"]["credits"] == 10

def test_history_management():
    entry = {
        "id": "gen-1",
        "prompt": "test prompt",
        "video_url": "/test.mp4",
        "status": "COMPLETED"
    }
    AuthService.add_history("admin-uuid", entry)
    
    history = AuthService.get_history("admin-uuid")
    assert len(history) == 1
    assert history[0]["prompt"] == "test prompt"
    assert "timestamp" in history[0]
