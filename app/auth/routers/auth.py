"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.auth.schemas.requests import SignupRequest, LoginRequest, ChangePasswordRequest
from app.auth.schemas.responses import TokenResponse, UserResponse, MessageResponse
from app.auth.services.auth import AuthService
from app.auth.services.security import verify_password, hash_password
from datetime import datetime

router = APIRouter(prefix="/api", tags=["auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User signup",
    description="Register a new user account with email, password, and country"
)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Register a new user

    - Creates user account with hashed password
    - Creates profile with country information
    - Creates subscription (default: FREE tier)
    - Returns JWT access token
    """
    service = AuthService(db)
    user, token = await service.signup(request.email, request.password, request.country)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and receive JWT access token"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and generate token

    - Validates email and password
    - Returns JWT access token valid for 7 days
    """
    service = AuthService(db)
    user, token = await service.login(request.email, request.password)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout user (client should discard token)"
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """
    Logout user

    Note: JWT is stateless, so logout is client-side only.
    Client should discard the token.
    """
    return MessageResponse(message="Logged out successfully")


@router.delete(
    "/account",
    response_model=MessageResponse,
    summary="Delete account",
    description="Delete user account and all associated data"
)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete user account

    - Deletes user and all associated data (profile, conversations, diary entries)
    - Cascade deletion via database relationships
    """
    service = AuthService(db)
    await service.delete_user(current_user)

    return MessageResponse(message="Account deleted successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user information"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user

    Requires: Authorization Bearer token
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change user password"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Change password for authenticated user

    - Validates current password
    - Updates to new password
    - Requires: Authorization Bearer token
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = hash_password(request.new_password)
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return MessageResponse(message="Password changed successfully")
