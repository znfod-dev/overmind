"""Translation API endpoints"""

from fastapi import APIRouter, HTTPException, status

from app.core.logging_config import logger
from app.translation.schemas.requests import TranslationRequest
from app.translation.schemas.responses import (
    LanguageInfo,
    LanguagesResponse,
    TranslationResponse,
)
from app.translation.services.prompts import LANGUAGE_INFO
from app.translation.services.translator import TranslationService

router = APIRouter(prefix="/api", tags=["translation"])


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Translate text",
    description="Translate text between supported languages using AI",
)
async def translate_text(request: TranslationRequest) -> TranslationResponse:
    """
    Translate text using AI

    **No authentication required** - Public endpoint

    **Supported languages**: ko, vi, en, zh, ru
    **Supported providers**: claude, google_ai, openai
    """
    try:
        # Create translation service
        service = TranslationService()

        # Perform translation
        result = await service.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider,
            model=request.model,
        )

        # Build response
        return TranslationResponse(
            translated_text=result["translated_text"],
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider,
            model=result["model"],
        )

    except ValueError as e:
        # Translation-specific errors
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected translation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation service error: {str(e)}",
        )


@router.get(
    "/languages",
    response_model=LanguagesResponse,
    summary="Get supported languages",
    description="List all supported languages for translation",
)
async def get_languages() -> LanguagesResponse:
    """
    Get list of supported languages

    **No authentication required** for this endpoint
    """
    return LanguagesResponse(
        languages=[LanguageInfo(**lang) for lang in LANGUAGE_INFO]
    )
