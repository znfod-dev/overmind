"""Admin API endpoints"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_admin_user
from app.models import User
from app.admin.schemas.requests import UserUpdateRequest, UserProfileUpdateRequest, AIModelPriorityUpdateRequest
from app.admin.schemas.responses import UserDetailResponse, UserListResponse, StatsResponse, AIModelPriorityResponse
from app.admin.services.admin import AdminService
from app.admin.services.ai_config import AIConfigService
from app.auth.schemas.responses import ProfileResponse

router = APIRouter(prefix="/api", tags=["admin-api"])


@router.get("/users", response_model=UserListResponse, summary="List all users")
async def list_users(
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    role: Optional[str] = Query(None, description="Filter by role (admin/user)"),
    status: Optional[str] = Query(None, description="Filter by status (blocked/inactive)"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with filtering and pagination

    - **limit**: Maximum number of users to return (1-100)
    - **offset**: Pagination offset
    - **role**: Filter by role (admin/user)
    - **status**: Filter by status (blocked/inactive)
    """
    service = AdminService(db)
    users, total = await service.list_users(
        limit=limit,
        offset=offset,
        role_filter=role,
        status_filter=status
    )

    return UserListResponse(
        users=[UserDetailResponse.model_validate(u) for u in users],
        total=total
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse, summary="Get user details")
async def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information including profile"""
    service = AdminService(db)
    user = await service.get_user_with_profile(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserDetailResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserDetailResponse, summary="Update user status")
async def update_user_status(
    user_id: int,
    request: UserUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user status (role, is_active, is_blocked)

    - Cannot change your own role
    - Cannot deactivate or block yourself
    """
    # Prevent admin from changing their own role
    if user_id == admin.id and request.role and request.role != admin.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Prevent admin from deactivating/blocking themselves
    if user_id == admin.id:
        if request.is_active is False or request.is_blocked is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate or block yourself"
            )

    service = AdminService(db)
    user = await service.update_user_status(
        user_id=user_id,
        role=request.role,
        is_active=request.is_active,
        is_blocked=request.is_blocked
    )

    return UserDetailResponse.model_validate(user)


@router.put("/users/{user_id}/profile", response_model=ProfileResponse, summary="Update user profile")
async def update_user_profile(
    user_id: int,
    request: UserProfileUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information"""
    service = AdminService(db)
    profile_data = request.model_dump(exclude_unset=True)
    profile = await service.update_user_profile(user_id, profile_data)

    return ProfileResponse.model_validate(profile)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user permanently (cascade deletes profile, conversations, diaries)

    - Cannot delete yourself
    """
    # Prevent admin from deleting themselves
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    service = AdminService(db)
    await service.delete_user(user_id)


@router.get("/stats", response_model=StatsResponse, summary="Get system statistics")
async def get_statistics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide statistics"""
    service = AdminService(db)
    stats = await service.get_statistics()

    return StatsResponse(**stats)


@router.get("/ai-priorities", response_model=list[AIModelPriorityResponse], summary="List AI model priorities")
async def list_ai_priorities(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all AI model priorities

    Shows priority settings for all countries and tiers
    """
    service = AIConfigService(db)
    priorities = await service.list_priorities()

    return [AIModelPriorityResponse.model_validate(p) for p in priorities]


@router.put("/ai-priorities", response_model=AIModelPriorityResponse, summary="Update AI model priority")
async def update_ai_priority(
    request: AIModelPriorityUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update or create AI model priority for a country/tier

    - Updates existing priority if found
    - Creates new priority if not found
    - Validates provider names (openai, google_ai, claude)
    """
    service = AIConfigService(db)
    priority = await service.update_priority(
        country=request.country,
        tier=request.tier,
        priority_1=request.priority_1,
        priority_2=request.priority_2,
        priority_3=request.priority_3
    )

    return AIModelPriorityResponse.model_validate(priority)


@router.delete("/ai-priorities/{country}/{tier}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete AI priority")
async def delete_ai_priority(
    country: str,
    tier: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete AI model priority for a country/tier

    - Removes priority configuration
    - System will fall back to WW (worldwide) default
    """
    service = AIConfigService(db)
    await service.delete_priority(country, tier)
