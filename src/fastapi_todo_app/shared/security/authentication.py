"""
Advanced Authentication and Security System
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from pydantic import BaseModel
import secrets
import hashlib
from functools import wraps
import time
from starlette.middleware.base import BaseHTTPMiddleware

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKey(BaseModel):
    key: str
    name: str
    permissions: list[str]
    expires_at: Optional[datetime] = None


class SecurityManager:
    """Advanced security management system"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, list] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.jwt_blacklist: set = set()
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            if token in self.jwt_blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def generate_api_key(self, name: str, permissions: list[str], expires_days: Optional[int] = None) -> str:
        """Generate API key with permissions"""
        key = f"ak_{secrets.token_urlsafe(32)}"
        expires_at = None
        
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        api_key = APIKey(
            key=key,
            name=name,
            permissions=permissions,
            expires_at=expires_at
        )
        
        self.api_keys[key] = api_key
        return key
    
    def validate_api_key(self, api_key: str) -> APIKey:
        """Validate API key and return permissions"""
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        key_info = self.api_keys[api_key]
        
        if key_info.expires_at and datetime.utcnow() > key_info.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired"
            )
        
        return key_info
    
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if user/IP has exceeded rate limits"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > window_start
        ]
        
        return len(self.failed_attempts[identifier]) < max_attempts
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(time.time())
    
    def blacklist_token(self, token: str):
        """Add token to blacklist (for logout)"""
        self.jwt_blacklist.add(token)


# Global security manager instance
security_manager = SecurityManager()


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = security_manager.verify_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return {"username": username, "permissions": payload.get("permissions", [])}


async def get_api_key_user(request: Request):
    """Get current user from API key"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    key_info = security_manager.validate_api_key(api_key)
    return {"api_key": key_info.name, "permissions": key_info.permissions}


def require_permissions(required_permissions: list[str]):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by dependency)
            user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = user.get("permissions", [])
            
            # Check if user has required permissions
            if not any(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'SELECT.*FROM',
            r'UNION.*SELECT',
            r'DROP.*TABLE',
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process security checks on requests"""
        
        # Rate limiting check
        client_ip = request.client.host if request.client else "unknown"
        if not security_manager.check_rate_limit(client_ip, max_attempts=100, window_minutes=1):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Continue to next middleware/app and add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


# Export main components
__all__ = [
    'SecurityManager',
    'security_manager',
    'UserCreate',
    'UserLogin', 
    'Token',
    'get_current_user',
    'get_api_key_user',
    'require_permissions',
    'SecurityMiddleware'
]