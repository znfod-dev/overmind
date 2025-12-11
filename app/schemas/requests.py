"""Request schemas"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """통합 채팅 요청 모델"""

    provider: str = Field(
        ..., description="AI 제공자 선택"
    )
    prompt: str = Field(..., description="사용자 프롬프트", min_length=1)
    max_tokens: int = Field(default=1024, description="최대 토큰 수", ge=1, le=8192)
    temperature: float = Field(
        default=0.7, description="생성 온도 (0.0 ~ 2.0)", ge=0.0, le=2.0
    )
    model: str | None = Field(default=None, description="특정 모델 지정 (선택)")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "claude",
                "prompt": "Hello, how are you?",
                "max_tokens": 100,
                "temperature": 0.7,
            }
        }
