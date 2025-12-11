"""Diary response schemas"""

from typing import List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class MessageResponse(BaseModel):
    """Single message in conversation"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    """Conversation with messages"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    entry_date: date
    started_at: datetime
    ended_at: datetime | None
    status: str
    messages: List[MessageResponse] = []


class AIMessageResponse(BaseModel):
    """AI response message"""

    message_id: int
    content: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 5,
                "content": "회사에서 새 프로젝트라니 흥미로워요! 어떤 프로젝트인지 더 들려주세요.",
                "created_at": "2025-12-09T14:30:00"
            }
        }


class DiaryEntryResponse(BaseModel):
    """Diary entry response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "conversation_id": 1,
                "title": "새로운 프로젝트 시작",
                "content": "2025년 12월 9일 화요일\n\n오늘은...",
                "entry_date": "2025-12-09",
                "length_type": "normal",
                "mood": "긍정적",
                "summary": "새 프로젝트를 시작하며 설레는 하루를 보냈다.",
                "created_at": "2025-12-09T15:00:00"
            }
        }
    )

    id: int
    user_id: int
    conversation_id: int | None
    title: str
    content: str
    entry_date: date
    length_type: str
    mood: str | None = None  # 감정 분석 결과
    summary: str | None = None  # 일기 요약
    created_at: datetime


class DiaryListResponse(BaseModel):
    """List of diary entries"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [],
                "total": 0
            }
        }
    )

    entries: List[DiaryEntryResponse]
    total: int
