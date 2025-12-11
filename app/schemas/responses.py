"""Response schemas"""

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """통합 채팅 응답 모델"""

    provider: str = Field(..., description="사용된 AI 제공자")
    text: str = Field(..., description="생성된 텍스트")
    model: str = Field(..., description="사용된 모델명")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "claude",
                "text": "Hello! I'm doing well, thank you for asking.",
                "model": "claude-3-opus-20240229",
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 모델"""

    error: str = Field(..., description="에러 메시지")
    detail: str | None = Field(default=None, description="상세 에러 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Authentication failed",
                "detail": "Invalid or missing X-API-Key header",
            }
        }
