"""
Authentication Tests
Comprehensive tests for auth endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base, get_db
from app.services.auth_service import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database"""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create database session for testing"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestRegistration:
    """Test user registration endpoint"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["user"]["email"] == "test@example.com"
    
    def test_register_duplicate_email(self, client):
        """Test registration with existing email"""
        # First registration
        client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "TestPassword123",
            "full_name": "First User"
        })
        
        # Second registration with same email
        response = client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "AnotherPassword123",
            "full_name": "Second User"
        })
        
        assert response.status_code == 400
        assert "zaten kayıtlı" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post("/api/auth/register", json={
            "email": "weak@example.com",
            "password": "weak",  # Too short, no uppercase, no number
            "full_name": "Weak Password User"
        })
        
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "password": "TestPassword123",
            "full_name": "Invalid Email User"
        })
        
        assert response.status_code == 422


class TestLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register first
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "TestPassword123",
            "full_name": "Login User"
        })
        
        # Login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "TestPassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # Register first
        client.post("/api/auth/register", json={
            "email": "wrongpass@example.com",
            "password": "TestPassword123",
            "full_name": "Wrong Password User"
        })
        
        # Login with wrong password
        response = client.post("/api/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123"
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPassword123"
        })
        
        assert response.status_code == 401
    
    def test_login_remember_me(self, client):
        """Test login with remember_me flag"""
        # Register first
        client.post("/api/auth/register", json={
            "email": "remember@example.com",
            "password": "TestPassword123",
            "full_name": "Remember User"
        })
        
        # Login with remember_me
        response = client.post("/api/auth/login", json={
            "email": "remember@example.com",
            "password": "TestPassword123",
            "remember_me": True
        })
        
        assert response.status_code == 200
        # Check extended expiration
        data = response.json()
        assert data["data"]["expires_in"] == 30 * 24 * 3600


class TestTokenOperations:
    """Test token verification and refresh"""
    
    def test_verify_token(self, client):
        """Test token verification"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "verify@example.com",
            "password": "TestPassword123",
            "full_name": "Verify User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Verify token
        response = client.get("/api/auth/verify", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        assert response.json()["valid"] is True
    
    def test_verify_invalid_token(self, client):
        """Test verification with invalid token"""
        response = client.get("/api/auth/verify", headers={
            "Authorization": "Bearer invalid-token"
        })
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client):
        """Test token refresh"""
        # Register and login to get refresh token
        client.post("/api/auth/register", json={
            "email": "refresh@example.com",
            "password": "TestPassword123",
            "full_name": "Refresh User"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "refresh@example.com",
            "password": "TestPassword123"
        })
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # Refresh token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()["data"]


class TestUserProfile:
    """Test user profile endpoints"""
    
    def test_get_profile(self, client):
        """Test getting current user profile"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "profile@example.com",
            "password": "TestPassword123",
            "full_name": "Profile User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Get profile
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "profile@example.com"
    
    def test_update_profile(self, client):
        """Test updating user profile"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "update@example.com",
            "password": "TestPassword123",
            "full_name": "Update User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Update profile
        response = client.put("/api/auth/me", 
            json={"full_name": "Updated Name", "theme": "light"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["fullName"] == "Updated Name"
    
    def test_change_password(self, client):
        """Test password change"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "password@example.com",
            "password": "TestPassword123",
            "full_name": "Password User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Change password
        response = client.post("/api/auth/change-password",
            json={
                "current_password": "TestPassword123",
                "new_password": "NewPassword456"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Verify new password works
        login_response = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password": "NewPassword456"
        })
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client):
        """Test password change with wrong current password"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "wrongcurrent@example.com",
            "password": "TestPassword123",
            "full_name": "Wrong Current User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Try to change with wrong current password
        response = client.post("/api/auth/change-password",
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewPassword456"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400


class TestLogout:
    """Test logout endpoint"""
    
    def test_logout(self, client):
        """Test successful logout"""
        # Register and get token
        reg_response = client.post("/api/auth/register", json={
            "email": "logout@example.com",
            "password": "TestPassword123",
            "full_name": "Logout User"
        })
        token = reg_response.json()["data"]["access_token"]
        
        # Logout
        response = client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestProtectedEndpoints:
    """Test protected endpoints require authentication"""
    
    def test_protected_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_protected_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token-here"
        })
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
