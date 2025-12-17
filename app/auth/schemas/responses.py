"""Auth response schemas"""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User information response"""

    id: int
    email: str
    role: str
    is_active: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "is_active": True,
                "is_blocked": False,
                "created_at": "2025-12-09T10:00:00"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "created_at": "2025-12-09T10:00:00"
                }
            }
        }


class ProfileResponse(BaseModel):
    """User profile response"""

    id: int
    user_id: int
    nickname: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    job: Optional[str] = None
    hobbies: Optional[str] = None
    family_composition: Optional[str] = None
    pets: Optional[str] = None
    country: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "nickname": "John",
                "birth_date": "1990-01-15",
                "gender": "male",
                "job": "Software Engineer",
                "hobbies": "reading, gaming",
                "family_composition": "Spouse and 2 kids",
                "pets": "1 cat",
                "country": "KR"
            }
        }


class MessageResponse(BaseModel):
    """Simple message response"""

    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation successful"
            }
        }
