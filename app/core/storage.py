"""Image storage service with GCS support"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import UploadFile, HTTPException, status
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image
import io

from app.config import settings

logger = logging.getLogger(__name__)


class ImageStorageService:
    """
    Image storage service with GCS and local fallback

    - Uses Google Cloud Storage if configured
    - Falls back to local file storage if GCS not available
    - Validates image format and size
    - Generates unique filenames
    """

    def __init__(self):
        self.gcs_bucket_name = settings.gcs_bucket_name
        self.gcs_credentials_path = settings.gcs_credentials_path
        self.local_storage_path = settings.local_storage_path
        self.max_size_bytes = settings.max_image_size_mb * 1024 * 1024
        self.allowed_types = settings.allowed_image_types

        self.use_gcs = False
        self.gcs_client = None
        self.gcs_bucket = None

        # Initialize GCS if configured
        if self.gcs_bucket_name and self.gcs_credentials_path:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.gcs_credentials_path
                )
                self.gcs_client = storage.Client(credentials=credentials)
                self.gcs_bucket = self.gcs_client.bucket(self.gcs_bucket_name)
                self.use_gcs = True
                logger.info(f"GCS initialized with bucket: {self.gcs_bucket_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize GCS, falling back to local storage: {e}")
                self.use_gcs = False
        else:
            logger.info("GCS not configured, using local storage")

        # Ensure local storage directory exists (as fallback or primary)
        if not self.use_gcs:
            Path(self.local_storage_path).mkdir(parents=True, exist_ok=True)

    async def save_image(
        self,
        file: UploadFile,
        user_id: int,
        folder: str = "messages"
    ) -> str:
        """
        Save uploaded image to storage

        Args:
            file: Uploaded image file
            user_id: User ID for organizing files
            folder: Subfolder for organization (e.g., 'messages', 'profiles')

        Returns:
            URL or path to the saved image

        Raises:
            HTTPException: If validation fails or upload error occurs
        """
        # Validate file type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_types)}"
            )

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_image_size_mb}MB"
            )

        # Validate image format with Pillow
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}"
            )

        # Generate unique filename
        file_extension = self._get_file_extension(file.content_type)
        unique_filename = self._generate_filename(user_id, folder, file_extension)

        # Save to storage
        if self.use_gcs:
            return await self._save_to_gcs(content, unique_filename)
        else:
            return await self._save_to_local(content, unique_filename)

    async def delete_image(self, image_url: str) -> bool:
        """
        Delete image from storage

        Args:
            image_url: URL or path to the image

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if self.use_gcs and image_url.startswith("https://storage.googleapis.com"):
                # Extract blob name from URL
                blob_name = self._extract_blob_name_from_url(image_url)
                blob = self.gcs_bucket.blob(blob_name)
                blob.delete()
                logger.info(f"Deleted from GCS: {blob_name}")
                return True
            else:
                # Local file deletion
                file_path = Path(self.local_storage_path) / Path(image_url).name
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted local file: {file_path}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete image {image_url}: {e}")
            return False

    async def _save_to_gcs(self, content: bytes, filename: str) -> str:
        """Save image to Google Cloud Storage"""
        try:
            blob = self.gcs_bucket.blob(filename)
            blob.upload_from_string(content)

            # Make the blob publicly accessible
            blob.make_public()

            public_url = blob.public_url
            logger.info(f"Uploaded to GCS: {filename}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )

    async def _save_to_local(self, content: bytes, filename: str) -> str:
        """Save image to local file system"""
        try:
            file_path = Path(self.local_storage_path) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(content)

            # Return relative path (to be served by FastAPI static files)
            relative_path = f"/storage/images/{filename}"
            logger.info(f"Saved to local storage: {file_path}")
            return relative_path
        except Exception as e:
            logger.error(f"Failed to save to local storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save image: {str(e)}"
            )

    def _generate_filename(self, user_id: int, folder: str, extension: str) -> str:
        """Generate unique filename with timestamp and UUID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{folder}/user_{user_id}/{timestamp}_{unique_id}{extension}"

    def _get_file_extension(self, content_type: str) -> str:
        """Get file extension from content type"""
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/heic": ".heic"
        }
        return extensions.get(content_type, ".jpg")

    def _extract_blob_name_from_url(self, url: str) -> str:
        """Extract blob name from GCS public URL"""
        # URL format: https://storage.googleapis.com/bucket-name/blob-name
        parts = url.split(f"{self.gcs_bucket_name}/")
        if len(parts) > 1:
            return parts[1]
        return ""


# Singleton instance
image_storage = ImageStorageService()
