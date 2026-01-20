"""
Authentication Routes
API endpoints for user registration, login, and profile management
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.base import get_db
from app.services.auth_service import (
    UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    PasswordChange, Token, TokenData,
    create_user, authenticate_user, get_user_by_email, get_user_by_id,
    create_access_token, create_refresh_token, decode_token,
    update_user_profile, change_password, user_to_dict
)
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ============ Pydantic Schemas ============

class RefreshTokenRequest(BaseModel):
    """Refresh token request body"""
    refresh_token: str


# ============ Dependency Functions ============

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Get current authenticated user from JWT token
    Returns None if not authenticated (for optional auth)
    """
    if not token:
        return None
    
    token_data = decode_token(token)
    
    if not token_data or not token_data.user_id:
        return None
    
    user = get_user_by_id(db, token_data.user_id)
    
    if not user:
        return None
    
    # Check if user is active
    is_active = getattr(user, 'is_active', True)
    if not is_active:
        return None
    
    return user_to_dict(user)


async def get_current_user_required(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user (required)
    Raises 401 if not authenticated
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_token(token)
    
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(db, token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    is_active = getattr(user, 'is_active', True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı bırakılmış",
        )
    
    return user_to_dict(user)


# ============ Auth Endpoints ============

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Min 8 chars, must include lowercase, uppercase, and number
    - **full_name**: User's full name
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kayıtlı"
        )
    
    try:
        # Create user
        user = create_user(db, user_data)
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "success": True,
            "message": "Kayıt başarılı",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.jwt_expiration_hours * 3600,
                "user": user_to_dict(user)
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kayıt sırasında bir hata oluştu"
        )


@router.post("/login", response_model=dict)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Returns JWT access token on success
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set token expiration based on remember_me
    if login_data.remember_me:
        expires_delta = timedelta(days=30)
        expires_in = 30 * 24 * 3600
    else:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)
        expires_in = settings.jwt_expiration_hours * 3600
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=expires_delta
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"User logged in: {user.email} from {client_host}")
    
    return {
        "success": True,
        "message": "Giriş başarılı",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": user_to_dict(user)
        }
    }


@router.post("/login/form", response_model=dict)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with OAuth2 password form (for Swagger UI testing)
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=dict)
async def refresh_token_endpoint(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    token_data = decode_token(token_request.refresh_token)
    
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token"
        )
    
    user = get_user_by_id(db, token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı veya hesap devre dışı"
        )
    
    # Check if user is active
    is_active = getattr(user, 'is_active', True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hesap devre dışı"
        )
    
    # Generate new access token
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {
        "success": True,
        "data": {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expiration_hours * 3600
        }
    }


@router.get("/me", response_model=dict)
async def get_me(
    current_user: dict = Depends(get_current_user_required)
):
    """
    Get current user profile
    Requires authentication
    """
    return {
        "success": True,
        "data": current_user
    }


@router.put("/me", response_model=dict)
async def update_me(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    Requires authentication
    """
    updated_user = update_user_profile(db, current_user["id"], profile_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    return {
        "success": True,
        "message": "Profil güncellendi",
        "data": user_to_dict(updated_user)
    }


@router.post("/change-password", response_model=dict)
async def change_user_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    Change user password
    Requires authentication and current password
    """
    success = change_password(
        db, 
        current_user["id"], 
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre hatalı"
        )
    
    return {
        "success": True,
        "message": "Şifre başarıyla değiştirildi"
    }


@router.post("/logout", response_model=dict)
async def logout(
    current_user: dict = Depends(get_current_user_required)
):
    """
    Logout current user
    Note: JWT tokens are stateless, so we just return success
    Client should remove the token from storage
    """
    logger.info(f"User logged out: {current_user['email']}")
    
    return {
        "success": True,
        "message": "Çıkış yapıldı"
    }


@router.get("/verify", response_model=dict)
async def verify_token(
    current_user: dict = Depends(get_current_user_required)
):
    """
    Verify if current token is valid
    Useful for frontend to check auth status
    """
    return {
        "success": True,
        "valid": True,
        "user": current_user
    }
