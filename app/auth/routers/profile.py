"""Profile management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.auth.schemas.requests import ProfileUpdateRequest
from app.auth.schemas.responses import ProfileResponse
from app.auth.services.auth import AuthService

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get user profile",
    description="Get authenticated user's profile information"
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProfileResponse:
    """
    Get user profile

    Returns profile information for AI personalization
    """
    service = AuthService(db)
    profile = await service.get_profile(current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return ProfileResponse.model_validate(profile)


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update user profile",
    description="Update user profile information (all fields optional)"
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProfileResponse:
    """
    Update user profile

    - All fields are optional
    - Only provided fields will be updated
    - Profile information is used by AI for personalized diary conversations
    """
    service = AuthService(db)

    # Convert request to dict, excluding unset fields
    profile_data = request.model_dump(exclude_unset=True)

    profile = await service.update_profile(current_user.id, profile_data)

    return ProfileResponse.model_validate(profile)
