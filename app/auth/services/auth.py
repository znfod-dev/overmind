"""Authentication business logic"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status, UploadFile
from pathlib import Path
import uuid
import os

from app.models import User, Profile, Subscription, SubscriptionTier
from app.auth.services.security import hash_password, verify_password, create_access_token

# Constants for image upload
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]
MAX_IMAGE_SIZE_MB = 5
STORAGE_DIR = Path("storage") # Relative to project root

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str, country: str = "WW") -> tuple[User, str]:
        """
        Register a new user

        Args:
            email: User email
            password: Plain text password
            country: Country code (KR, VN, US, JP, WW)

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
        await self.db.flush()

        # Create profile with country
        profile = Profile(user_id=user.id, country=country)
        self.db.add(profile)

        # Create subscription (default: FREE tier)
        subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE)
        self.db.add(subscription)

        await self.db.commit()
        await self.db.refresh(user)

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

    async def upload_profile_image(self, user_id: int, file: UploadFile) -> Profile:
        """
        Uploads a profile image for the user.

        Args:
            user_id: The ID of the user.
            file: The uploaded image file.

        Returns:
            The updated Profile object.

        Raises:
            HTTPException: If the file type is not allowed or the file size exceeds the limit.
        """
        profile = await self.get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create a profile first."
            )

        # 1. Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        # 2. Validate file size
        # FastAPI's UploadFile doesn't directly expose file size without reading it.
        # We'll read a chunk to check size or rely on the read_file method to handle large files.
        # For a robust solution, consider streaming and checking size during read.
        # For now, a simplified check after reading fully is done, but ideally this should be before full read.
        file_content = await file.read()
        if len(file_content) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image file size exceeds {MAX_IMAGE_SIZE_MB}MB limit."
            )

        # 3. Generate unique filename and path
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = STORAGE_DIR / unique_filename

        # 4. Save file to local storage
        try:
            await file_path.write_bytes(file_content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not save image: {e}"
            )

        # 5. Delete old profile image if exists
        if profile.profile_image_url:
            old_image_path = Path(profile.profile_image_url.lstrip("/")) # Remove leading / if present
            if old_image_path.is_file():
                os.remove(old_image_path)
                print(f"Deleted old profile image: {old_image_path}")

        # 6. Update profile with new image URL
        profile.profile_image_url = f"/{file_path}" # Store as /storage/unique_filename
        await self.db.commit()
        await self.db.refresh(profile)

        return profile
