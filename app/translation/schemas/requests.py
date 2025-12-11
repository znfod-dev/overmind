"""Translation request schemas"""

from pydantic import BaseModel, Field


# Language code type (5 supported languages)
LanguageCode = str

# Provider type (reuse from AI)
ProviderType = str


class TranslationRequest(BaseModel):
    """Translation request model"""

    text: str = Field(
        ...,
        description="Text to translate",
        min_length=1,
        max_length=10000,
    )
    source_lang: LanguageCode = Field(..., description="Source language code")
    target_lang: LanguageCode = Field(..., description="Target language code")
    provider: ProviderType = Field(
        default="claude", description="AI provider to use for translation"
    )
    model: str | None = Field(default=None, description="Specific model (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, how are you?",
                "source_lang": "en",
                "target_lang": "ko",
                "provider": "claude",
            }
        }
