"""Translation response schemas"""

from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    """Translation response model"""

    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    provider: str = Field(..., description="AI provider used")
    model: str = Field(..., description="Model used")
    detected_source_lang: str | None = Field(
        default=None, description="Auto-detected source language (if available)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "translated_text": "안녕하세요, 어떻게 지내세요?",
                "source_lang": "en",
                "target_lang": "ko",
                "provider": "claude",
                "model": "claude-3-5-sonnet-20241022",
            }
        }


class LanguageInfo(BaseModel):
    """Language information model"""

    code: str = Field(..., description="Language code (ISO 639-1 style)")
    name: str = Field(..., description="Language name in English")
    native_name: str = Field(..., description="Language name in native script")


class LanguagesResponse(BaseModel):
    """Supported languages response"""

    languages: list[LanguageInfo] = Field(..., description="Supported languages")

    class Config:
        json_schema_extra = {
            "example": {
                "languages": [
                    {"code": "ko", "name": "Korean", "native_name": "한국어"},
                    {"code": "en", "name": "English", "native_name": "English"},
                ]
            }
        }
