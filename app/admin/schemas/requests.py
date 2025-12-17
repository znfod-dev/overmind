"""Admin request schemas"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator


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


class AIModelPriorityUpdateRequest(BaseModel):
    """AI 모델 우선순위 업데이트 요청"""

    country: str = Field(..., pattern="^[A-Z]{2}$", description="Country code (KR/VN/US/JP/WW)")
    tier: str = Field(..., pattern="^(basic|premium)$", description="Tier (basic/premium)")
    priority_1: str = Field(..., pattern="^(openai|google_ai|claude)$", description="1st priority AI provider")
    priority_2: str = Field(..., pattern="^(openai|google_ai|claude)$", description="2nd priority AI provider")
    priority_3: str = Field(..., pattern="^(openai|google_ai|claude)$", description="3rd priority AI provider")

    class Config:
        json_schema_extra = {
            "example": {
                "country": "KR",
                "tier": "basic",
                "priority_1": "openai",
                "priority_2": "google_ai",
                "priority_3": "claude"
            }
        }
