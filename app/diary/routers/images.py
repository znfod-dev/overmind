"""Image upload endpoints for diary conversations"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.models import User
from app.core.storage import image_storage

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageUploadResponse(BaseModel):
    """Image upload response"""
    image_url: str
    message: str = "Image uploaded successfully"

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://storage.googleapis.com/overmind-images/messages/user_1/20251224_123456_abc123.jpg",
                "message": "Image uploaded successfully"
            }
        }


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image",
    description="Upload an image file for use in diary conversations"
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user)
) -> ImageUploadResponse:
    """
    Upload image to storage

    - Accepts JPEG, PNG, WebP, HEIC formats
    - Maximum size: 5MB
    - Returns public URL or path to the uploaded image
    - Images are organized by user ID and timestamp
    """
    # Validate file is provided
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Save image
    image_url = await image_storage.save_image(
        file=file,
        user_id=current_user.id,
        folder="messages"
    )

    return ImageUploadResponse(image_url=image_url)
