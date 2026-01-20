"""
Authentication Service
JWT token management and password hashing with bcrypt
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any, TYPE_CHECKING
try:
    from jose import JWTError, jwt as jose_jwt
    jwt = jose_jwt
except ImportError:
    jwt = None
    JWTError = Exception  # type: ignore

# Use bcrypt directly instead of passlib (better compatibility with bcrypt 5.x)
try:
    import bcrypt
    _bcrypt_available = True
except ImportError:
    bcrypt = None  # type: ignore
    _bcrypt_available = False

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, UserProfile, MembershipType
from app.utils.logger import logger
import re
import hashlib
import secrets


# ============ Password Functions ============

def verify_password(plain_password: str, hashed_password: Any) -> bool:
    """Verify a plain password against a hashed password"""
    hashed_str = str(hashed_password) if hashed_password else ""
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')[:72]
    
    if _bcrypt_available and bcrypt:
        try:
            return bcrypt.checkpw(password_bytes, hashed_str.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    # Fallback for simple hash (not recommended for production)
    return _simple_hash(plain_password) == hashed_str


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    
    if _bcrypt_available and bcrypt:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    # Fallback for simple hash (not recommended for production)
    return _simple_hash(password)

class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserCreate(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalıdır')
        if not re.search(r'[a-z]', v):
            raise ValueError('Şifre en az bir küçük harf içermelidir')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Şifre en az bir büyük harf içermelidir')
        if not re.search(r'\d', v):
            raise ValueError('Şifre en az bir rakam içermelidir')
        return v


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str
    remember_me: bool = False


class UserResponse(BaseModel):
    """User response schema (without password)"""
    id: int
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    membership: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    default_ticker: Optional[str] = None
    default_interval: Optional[str] = None
    risk_tolerance: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    price_alert_enabled: Optional[bool] = None
    signal_alert_enabled: Optional[bool] = None


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalıdır')
        if not re.search(r'[a-z]', v):
            raise ValueError('Şifre en az bir küçük harf içermelidir')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Şifre en az bir büyük harf içermelidir')
        if not re.search(r'\d', v):
            raise ValueError('Şifre en az bir rakam içermelidir')
        return v


def _simple_hash(password: str) -> str:
    """Simple SHA256 hash fallback (use bcrypt in production!)"""
    salt = "trading_bot_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()


# ============ Token Functions ============

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Optional expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    if jwt is None:
        raise RuntimeError("jose library not installed")
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token (longer expiration)
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    if jwt is None:
        raise RuntimeError("jose library not installed")
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None if invalid
    """
    if jwt is None:
        logger.error("jose library not installed")
        return None
    
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=int(user_id), email=str(email) if email else None)
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.warning(f"Token decode error: {e}")
        return None


# ============ User CRUD Functions ============

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password
    
    Args:
        db: Database session
        user_data: User registration data
        
    Returns:
        Created User object
    """
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
        membership=MembershipType.FREE
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default profile
    profile = UserProfile(
        user_id=db_user.id,
        theme="dark",
        language="tr"
    )
    db.add(profile)
    db.commit()
    
    logger.info(f"New user created: {db_user.email}")
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User object if authenticated, None otherwise
    """
    user = get_user_by_email(db, email)
    
    if not user:
        logger.warning(f"Login attempt with non-existent email: {email}")
        return None
    
    # Check if user is active
    is_active = getattr(user, 'is_active', True)
    if not is_active:
        logger.warning(f"Login attempt with inactive account: {email}")
        return None
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {email}")
        return None
    
    # Update last login
    try:
        user.last_login = datetime.now(timezone.utc)  # type: ignore
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to update last_login: {e}")
    
    logger.info(f"User logged in: {email}")
    return user


def update_user_profile(
    db: Session, 
    user_id: int, 
    profile_data: UserProfileUpdate
) -> Optional[User]:
    """
    Update user profile
    """
    user = get_user_by_id(db, user_id)
    
    if not user:
        return None
    
    # Update user fields
    if profile_data.full_name:
        user.full_name = profile_data.full_name  # type: ignore
    
    # Update profile fields
    if user.profile:
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            if field != 'full_name' and hasattr(user.profile, field):
                setattr(user.profile, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


def change_password(
    db: Session, 
    user_id: int, 
    current_password: str, 
    new_password: str
) -> bool:
    """
    Change user password
    
    Returns:
        True if password changed successfully, False otherwise
    """
    user = get_user_by_id(db, user_id)
    
    if not user:
        return False
    
    if not verify_password(current_password, user.hashed_password):
        return False
    
    user.hashed_password = get_password_hash(new_password)  # type: ignore
    db.commit()
    
    logger.info(f"Password changed for user: {user.email}")
    return True


def user_to_dict(user: User) -> dict:
    """Convert User model to dictionary for response"""
    # Helper to safely get attribute value
    def safe_get(obj, attr, default=None):  # type: ignore
        val = getattr(obj, attr, default)
        return val if val is not None else default
    
    # Safely get membership value
    membership_val = "free"
    membership = safe_get(user, 'membership')
    if membership is not None:
        membership_val = membership.value if hasattr(membership, 'value') else str(membership)
    
    # Safely format dates
    created_at = None
    ca = safe_get(user, 'created_at')
    if ca is not None:
        try:
            created_at = ca.isoformat() if hasattr(ca, 'isoformat') else str(ca)
        except Exception:
            pass
    
    last_login = None
    ll = safe_get(user, 'last_login')
    if ll is not None:
        try:
            last_login = ll.isoformat() if hasattr(ll, 'isoformat') else str(ll)
        except Exception:
            pass
    
    email = safe_get(user, 'email')
    full_name = safe_get(user, 'full_name')
    is_active = safe_get(user, 'is_active', True)
    is_verified = safe_get(user, 'is_verified', False)
    
    result = {
        "id": user.id,
        "email": str(email) if email is not None else None,
        "fullName": str(full_name) if full_name is not None else None,
        "isActive": bool(is_active) if is_active is not None else True,
        "isVerified": bool(is_verified) if is_verified is not None else False,
        "membership": membership_val,
        "createdAt": created_at,
        "lastLogin": last_login,
        "profile": None
    }
    
    profile = safe_get(user, 'profile')
    if profile is not None:
        result["profile"] = {
            "avatarUrl": str(safe_get(profile, 'avatar_url')) if safe_get(profile, 'avatar_url') else None,
            "phone": str(safe_get(profile, 'phone')) if safe_get(profile, 'phone') else None,
            "theme": str(safe_get(profile, 'theme', 'dark')),
            "language": str(safe_get(profile, 'language', 'tr')),
            "defaultTicker": str(safe_get(profile, 'default_ticker', 'THYAO.IS')),
            "riskTolerance": str(safe_get(profile, 'risk_tolerance', 'moderate')),
            "emailNotifications": bool(safe_get(profile, 'email_notifications', True)),
            "priceAlertEnabled": bool(safe_get(profile, 'price_alert_enabled', True)),
            "signalAlertEnabled": bool(safe_get(profile, 'signal_alert_enabled', True)),
        }
    
    return result
