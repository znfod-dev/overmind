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
    image_url: str | None = None
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


class ConversationQualityInfo(BaseModel):
    """Real-time conversation quality information"""

    is_sufficient: bool = Field(..., description="Whether conversation is sufficient for diary generation")
    quality_level: str = Field(..., description="Quality level: insufficient, minimal, good, excellent")
    user_message_count: int = Field(..., description="Number of user messages")
    total_user_content_length: int = Field(..., description="Total characters in user messages")
    avg_user_message_length: float = Field(..., description="Average characters per user message")
    feedback_message: str = Field(..., description="User-friendly feedback message in Korean")

    class Config:
        json_schema_extra = {
            "example": {
                "is_sufficient": True,
                "quality_level": "good",
                "user_message_count": 4,
                "total_user_content_length": 120,
                "avg_user_message_length": 30.0,
                "feedback_message": "대화가 충분합니다! 일기를 생성할 수 있어요."
            }
        }


class AIMessageResponse(BaseModel):
    """AI response message"""

    message_id: int
    content: str
    created_at: datetime
    quality_info: ConversationQualityInfo | None = Field(None, description="Conversation quality information")

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 5,
                "content": "회사에서 새 프로젝트라니 흥미로워요! 어떤 프로젝트인지 더 들려주세요.",
                "created_at": "2025-12-09T14:30:00",
                "quality_info": {
                    "is_sufficient": False,
                    "quality_level": "minimal",
                    "user_message_count": 2,
                    "total_user_content_length": 45,
                    "avg_user_message_length": 22.5,
                    "feedback_message": "조금 더 대화를 나누면 더 좋은 일기를 만들 수 있어요."
                }
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


class DiaryReviewSuggestion(BaseModel):
    """Individual suggestion for improvement"""

    type: str = Field(..., description="Suggestion type: spelling, grammar, style, clarity")
    original: str = Field(..., description="Original text")
    suggested: str = Field(..., description="Suggested replacement")
    reason: str = Field(..., description="Reason for suggestion")


class DiaryReviewResponse(BaseModel):
    """AI review response for diary"""

    overall_feedback: str = Field(..., description="Overall feedback on the diary")
    mood: str | None = Field(None, description="Detected mood: positive, negative, neutral, mixed")
    suggestions: List[DiaryReviewSuggestion] = Field(default_factory=list, description="List of improvement suggestions")
    improved_content: str | None = Field(None, description="AI-improved version of the diary")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_feedback": "전반적으로 감정 표현이 잘 되어 있습니다. 다만 문장이 다소 단조로운 부분이 있어 개선하면 좋을 것 같습니다.",
                "mood": "positive",
                "suggestions": [
                    {
                        "type": "spelling",
                        "original": "있엇다",
                        "suggested": "있었다",
                        "reason": "맞춤법 오류"
                    },
                    {
                        "type": "style",
                        "original": "밥을 먹었다",
                        "suggested": "저녁 식사를 함께 했다",
                        "reason": "더 풍부한 표현"
                    }
                ],
                "improved_content": "오늘은 크리스마스 이브였다. 가족들과 함께 따뜻한 저녁 식사를 했고..."
            }
        }
