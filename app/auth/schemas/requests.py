"""Auth request schemas"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, EmailStr


class SignupRequest(BaseModel):
    """User signup request"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (8-100 characters)")
    country: str = Field(default="WW", pattern="^(KR|VN|US|JP|WW)$", description="Country code (KR/VN/US/JP/WW)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePassword123",
                "country": "KR"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePassword123"
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Profile update request - all fields optional"""

    nickname: Optional[str] = Field(None, max_length=50, description="User nickname")
    birth_date: Optional[date] = Field(None, description="Birth date (YYYY-MM-DD)")
    gender: Optional[str] = Field(
        None, description="Gender"
    )
    job: Optional[str] = Field(None, max_length=100, description="Job/Occupation")
    hobbies: Optional[str] = Field(None, description="Hobbies (comma-separated)")
    family_composition: Optional[str] = Field(None, max_length=200, description="Family composition")
    pets: Optional[str] = Field(None, max_length=200, description="Pets information")
    country: Optional[str] = Field(None, pattern="^(KR|VN|US|JP|WW)$", description="Country code (KR/VN/US/JP/WW)")

    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "John",
                "birth_date": "1990-01-15",
                "gender": "male",
                "job": "Software Engineer",
                "hobbies": "reading, gaming, hiking",
                "family_composition": "Living with spouse and 2 kids",
                "pets": "1 cat named Whiskers"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Password change request"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (8-100 characters)")

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldPassword123",
                "new_password": "newSecurePassword456"
            }
        }
