"""Diary request schemas"""

from datetime import date
from pydantic import BaseModel, Field


class StartConversationRequest(BaseModel):
    """Start a new diary conversation"""

    entry_date: date = Field(..., description="Date for this diary entry")
    initial_message: str = Field(
        default="오늘 하루 어떠셨어요?",
        description="Initial AI message to start conversation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entry_date": "2025-12-11",
                "initial_message": "오늘 하루 어떠셨어요?"
            }
        }


class SendMessageRequest(BaseModel):
    """Send a message in conversation"""

    content: str = Field(..., min_length=1, max_length=5000, description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "오늘은 회사에서 새로운 프로젝트를 시작했어요."
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
