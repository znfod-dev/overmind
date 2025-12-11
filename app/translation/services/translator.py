"""Translation service using HTTP calls to AI service"""

import json
import re
from typing import Any, Dict

import httpx

from app.config import settings
from app.core.ai_helper import call_ai_service
from app.core.logging_config import logger
from app.translation.services.prompts import create_translation_prompt


class TranslationService:
    """
    Translation service that calls the AI service via HTTP

    This ensures proper service separation and allows the services
    to be deployed independently.
    """

    # Temperature for translation (lower = more deterministic)
    TRANSLATION_TEMPERATURE = 0.3

    # Max tokens for translation responses
    MAX_TOKENS = 2048

    # HTTP timeout for AI service calls (seconds)
    TIMEOUT = 30.0

    def __init__(self):
        """Initialize translation service"""
        self.ai_service_url = settings.ai_service_url
        self.internal_api_key = settings.internal_api_key

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        provider: str,
        model: str | None = None,
    ) -> Dict[str, Any]:
        """
        Translate text using specified AI provider via HTTP call to AI service

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            provider: AI provider (claude, google_ai, openai)
            model: Optional specific model

        Returns:
            Dict with translation result:
            {
                "translated_text": str,
                "model": str,
                "raw_response": str (for debugging)
            }

        Raises:
            ValueError: If translation fails or response invalid
        """
        # Validation
        if source_lang == target_lang:
            logger.warning(f"Source and target languages are the same: {source_lang}")
            return {
                "translated_text": text,  # Return as-is
                "model": "none",
                "raw_response": text,
            }

        # Create translation prompt
        prompt = create_translation_prompt(text, source_lang, target_lang)

        # Call AI service via HTTP
        try:
            ai_result = await call_ai_service(
                prompt=prompt,
                provider=provider,
                model=model,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TRANSLATION_TEMPERATURE,
                timeout=self.TIMEOUT
            )

            # Parse translation from AI response
            translated_text = self._parse_translation_response(ai_result["text"])

            return {
                "translated_text": translated_text,
                "model": ai_result["model"],
                "raw_response": ai_result["text"],
            }

        except httpx.TimeoutException:
            raise ValueError(
                f"Translation request timed out after {self.TIMEOUT} seconds"
            )
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"AI service error ({e.response.status_code}): {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ValueError(f"Failed to connect to AI service: {str(e)}")
        except KeyError as e:
            logger.error(f"Invalid AI service response format: missing {str(e)}")
            raise ValueError(f"Invalid response from AI service: missing {str(e)}")
        except Exception as e:
            logger.error(f"Translation failed with {provider}: {str(e)}")
            raise ValueError(f"Translation failed: {str(e)}")

    def _parse_translation_response(self, response: str) -> str:
        """
        Parse translation from AI response

        Tries multiple strategies:
        1. JSON parsing (if response is valid JSON)
        2. JSON extraction from markdown code blocks
        3. JSON extraction using regex
        4. Fallback to entire response (cleaned)

        Args:
            response: Raw AI response

        Returns:
            Extracted translation text

        Raises:
            ValueError: If parsing fails completely
        """
        if not response or not response.strip():
            raise ValueError("Empty response from AI")

        # Strategy 1: Try direct JSON parse
        try:
            data = json.loads(response.strip())
            if "translated_text" in data:
                return data["translated_text"]
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON from markdown code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if "translated_text" in data:
                    return data["translated_text"]
            except json.JSONDecodeError:
                pass

        # Strategy 3: Extract JSON object from text
        json_match = re.search(
            r'\{[^{}]*"translated_text"[^{}]*\}', response, re.DOTALL
        )
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if "translated_text" in data:
                    return data["translated_text"]
            except json.JSONDecodeError:
                pass

        # Strategy 4: Fallback - use entire response (cleaned)
        logger.warning("Could not parse JSON response, using raw text as translation")

        # Remove common prefixes/suffixes
        cleaned = response.strip()
        cleaned = re.sub(
            r"^(Translation:|Translated text:|Result:)\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"^```.*?\n", "", cleaned)  # Remove code block starts
        cleaned = re.sub(r"\n```$", "", cleaned)  # Remove code block ends

        return cleaned.strip()
