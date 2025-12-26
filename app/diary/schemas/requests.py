"""Diary request schemas"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class StartConversationRequest(BaseModel):
    """Start a new diary conversation"""

    entry_date: date = Field(..., description="Date for this diary entry")
    timezone: str = Field(
        default="America/Los_Angeles",
        description="User's timezone (IANA timezone format, e.g., 'America/Los_Angeles', 'Asia/Seoul')"
    )
    current_time: Optional[datetime] = Field(
        default=None,
        description="Client's current local time (ISO 8601 format with timezone). If not provided, server time will be used."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entry_date": "2025-12-18",
                "timezone": "America/Los_Angeles",
                "current_time": "2025-12-18T09:30:00-08:00"
            }
        }


class SendMessageRequest(BaseModel):
    """Send a message in conversation"""

    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    image_url: Optional[str] = Field(None, max_length=500, description="URL or path to attached image")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "오늘은 회사에서 새로운 프로젝트를 시작했어요.",
                "image_url": "https://storage.googleapis.com/overmind-images/messages/user_1/20251224_123456_abc123.jpg"
            }
        }


class GenerateDiaryRequest(BaseModel):
    """Generate diary from conversation"""

    length_type: str = Field(
        default="normal",
        description="Diary length type"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Diary title (user-provided or auto-generated)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "length_type": "normal",
                "title": "새로운 프로젝트 시작"
            }
        }


class CreateDiaryRequest(BaseModel):
    """Create diary manually (without conversation)"""

    entry_date: date = Field(..., description="Date for this diary entry")
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Diary title"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Diary content"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entry_date": "2025-12-24",
                "title": "크리스마스 이브",
                "content": "오늘은 크리스마스 이브였다. 가족들과 함께 따뜻한 저녁 식사를 했고..."
            }
        }


class ReviewDiaryRequest(BaseModel):
    """Request AI review for diary content"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Diary title"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Diary content to review"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "크리스마스 이브",
                "content": "오늘은 크리스마스 이브였다. 가족들과 함께 따뜻한 저녁 식사를 했고..."
            }
        }
