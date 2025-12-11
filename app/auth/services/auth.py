"""Authentication business logic"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models import User, Profile
from app.auth.services.security import hash_password, verify_password, create_access_token


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str) -> tuple[User, str]:
        """
        Register a new user

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User object, JWT token)

        Raises:
            HTTPException: If email already exists
        """
        # Check if user exists
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user (default role: user)
        hashed_pwd = hash_password(password)
        user = User(email=email, hashed_password=hashed_pwd)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Create empty profile
        profile = Profile(user_id=user.id)
        self.db.add(profile)
        await self.db.commit()

        # Generate token
        access_token = create_access_token(data={"sub": user.email})

        return user, access_token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate user and generate token

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User object, JWT token)

        Raises:
            HTTPException: If credentials invalid or account inactive/blocked
        """
        # Get user
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support."
            )

        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is blocked. Please contact support."
            )

        # Generate token
        access_token = create_access_token(data={"sub": user.email})

        return user, access_token

    async def delete_user(self, user: User) -> None:
        """
        Delete user account (cascade deletes profile, conversations, diaries)

        Args:
            user: User object to delete
        """
        await self.db.delete(user)
        await self.db.commit()

    async def get_profile(self, user_id: int) -> Optional[Profile]:
        """Get user profile"""
        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: int, profile_data: dict) -> Profile:
        """
        Update user profile

        Args:
            user_id: User ID
            profile_data: Dictionary of profile fields to update

        Returns:
            Updated Profile object
        """
        profile = await self.get_profile(user_id)

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
