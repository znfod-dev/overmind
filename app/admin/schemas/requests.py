"""Admin request schemas"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    """Admin user status update request"""

    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "is_active": True,
                "is_blocked": False
            }
        }


class UserProfileUpdateRequest(BaseModel):
    """Admin user profile update request"""

    nickname: Optional[str] = Field(None, max_length=50)
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    job: Optional[str] = Field(None, max_length=100)
    hobbies: Optional[str] = None
    family_composition: Optional[str] = Field(None, max_length=200)
    pets: Optional[str] = Field(None, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "John",
                "birth_date": "1990-01-15",
                "gender": "male",
                "job": "Software Engineer",
                "hobbies": "reading, gaming",
                "family_composition": "Spouse and 2 kids",
                "pets": "1 cat"
            }
        }
