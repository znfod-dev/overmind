"""Admin response schemas"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.auth.schemas.responses import ProfileResponse


class UserDetailResponse(BaseModel):
    """User detail with profile information"""

    id: int
    email: str
    role: str
    is_active: bool
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
    profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "is_active": True,
                "is_blocked": False,
                "created_at": "2025-12-09T10:00:00",
                "updated_at": "2025-12-09T10:00:00",
                "profile": {
                    "id": 1,
                    "user_id": 1,
                    "nickname": "John",
                    "birth_date": "1990-01-15",
                    "gender": "male",
                    "job": "Software Engineer",
                    "hobbies": "reading, gaming",
                    "family_composition": "Spouse and 2 kids",
                    "pets": "1 cat"
                }
            }
        }


class UserListResponse(BaseModel):
    """Paginated user list response"""

    users: List[UserDetailResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": 1,
                        "email": "user@example.com",
                        "role": "user",
                        "is_active": True,
                        "is_blocked": False,
                        "created_at": "2025-12-09T10:00:00",
                        "updated_at": "2025-12-09T10:00:00"
                    }
                ],
                "total": 100
            }
        }


class StatsResponse(BaseModel):
    """System statistics response"""

    total_users: int
    admin_users: int
    active_users: int
    blocked_users: int
    total_diaries: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 100,
                "admin_users": 5,
                "active_users": 95,
                "blocked_users": 2,
                "total_diaries": 450
            }
        }
