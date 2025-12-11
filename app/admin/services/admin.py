"""Admin business logic"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models import User, Profile, DiaryEntry


class AdminService:
    """Admin service for user management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0,
        role_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> tuple[list[User], int]:
        """
        List all users with filters and pagination

        Args:
            limit: Maximum number of users to return
            offset: Pagination offset
            role_filter: Filter by role (admin/user)
            status_filter: Filter by status (blocked/inactive)

        Returns:
            Tuple of (list of users, total count)
        """
        query = select(User).options(selectinload(User.profile))

        # Apply filters
        if role_filter:
            query = query.where(User.role == role_filter)
        if status_filter == "blocked":
            query = query.where(User.is_blocked == True)
        elif status_filter == "inactive":
            query = query.where(User.is_active == False)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    async def get_user_with_profile(self, user_id: int) -> Optional[User]:
        """
        Get user with profile loaded

        Args:
            user_id: User ID to fetch

        Returns:
            User object with profile or None if not found
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_status(
        self,
        user_id: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_blocked: Optional[bool] = None
    ) -> User:
        """
        Update user status fields

        Args:
            user_id: User ID to update
            role: New role (admin/user)
            is_active: New active status
            is_blocked: New blocked status

        Returns:
            Updated User object

        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_with_profile(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if is_blocked is not None:
            user.is_blocked = is_blocked

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user_profile(self, user_id: int, profile_data: dict) -> Profile:
        """
        Update user profile

        Args:
            user_id: User ID
            profile_data: Dictionary of profile fields to update

        Returns:
            Updated Profile object

        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_with_profile(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        profile = user.profile
        if not profile:
            # Create profile if doesn't exist
            profile = Profile(user_id=user_id)
            self.db.add(profile)

        # Update fields
        for key, value in profile_data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def delete_user(self, user_id: int) -> None:
        """
        Delete user (cascade deletes profile, conversations, diaries)

        Args:
            user_id: User ID to delete

        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_with_profile(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        await self.db.delete(user)
        await self.db.commit()

    async def get_statistics(self) -> dict:
        """
        Get system statistics

        Returns:
            Dictionary with various statistics
        """
        # Total users
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        # Admin users
        admin_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == "admin")
        )
        admin_users = admin_result.scalar() or 0

        # Active users (active and not blocked)
        active_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.is_active == True,
                User.is_blocked == False
            )
        )
        active_users = active_result.scalar() or 0

        # Blocked users
        blocked_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_blocked == True)
        )
        blocked_users = blocked_result.scalar() or 0

        # Total diaries
        diary_result = await self.db.execute(select(func.count(DiaryEntry.id)))
        total_diaries = diary_result.scalar() or 0

        return {
            "total_users": total_users,
            "admin_users": admin_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "total_diaries": total_diaries
        }
