"""인증 관련 의존성"""

from typing import Optional, TYPE_CHECKING
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User

if TYPE_CHECKING:
    from app.auth.services.security import decode_access_token


# X-API-Key authentication (existing - keep for AI service)
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """
    X-API-Key 헤더 검증

    외부 사용자 키(API_AUTH_KEY)와 내부 서비스 키(INTERNAL_API_KEY) 모두 허용

    Args:
        x_api_key: 요청 헤더의 X-API-Key 값

    Returns:
        검증된 API 키

    Raises:
        HTTPException: 인증 실패 시 401 에러
    """
    # 외부 사용자 키 또는 내부 서비스 키 확인
    valid_keys = [settings.api_auth_key, settings.internal_api_key]

    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key


# JWT Bearer token authentication (new - for Auth/Diary services)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Import here to avoid circular dependency
    from app.auth.services.security import decode_access_token

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None

    For optional authentication scenarios
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify admin role

    Usage:
        @router.get("/admin/users")
        async def list_users(admin: User = Depends(get_admin_user)):
            return admin_service.list_users()

    Args:
        current_user: Current authenticated user

    Returns:
        Authenticated admin User object

    Raises:
        HTTPException: If user is not admin or account is inactive/blocked
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    if not current_user.is_active or current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

    return current_user
