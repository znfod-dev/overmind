"""Tests for TranslationService"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.translation.services.translator import TranslationService


class TestTranslationService:
    """Test TranslationService class"""

    @pytest.fixture
    def service(self):
        """Create TranslationService instance"""
        return TranslationService()

    @pytest.mark.asyncio
    async def test_same_language_translation(self, service):
        """Test translation with same source and target language"""
        result = await service.translate(
            text="Hello",
            source_lang="en",
            target_lang="en",
            provider="claude",
        )

        assert result["translated_text"] == "Hello"
        assert result["model"] == "none"

    @pytest.mark.asyncio
    async def test_translate_with_claude(self, service):
        """Test translation using Claude via HTTP"""
        mock_ai_response = {
            "text": json.dumps({"translated_text": "안녕하세요"}),
            "model": "claude-3-5-sonnet-20241022",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_ai_response
            mock_post.return_value = mock_response

            result = await service.translate(
                text="Hello",
                source_lang="en",
                target_lang="ko",
                provider="claude",
            )

            assert result["translated_text"] == "안녕하세요"
            assert result["model"] == "claude-3-5-sonnet-20241022"

            # Verify HTTP call was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/ai/api/req" in call_args[0][0]
            assert call_args[1]["headers"]["X-API-Key"] == service.internal_api_key
            assert call_args[1]["json"]["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_translate_with_google_ai(self, service):
        """Test translation using Google AI via HTTP"""
        mock_ai_response = {
            "text": json.dumps({"translated_text": "Xin chào"}),
            "model": "gemini-2.0-flash-exp",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_ai_response
            mock_post.return_value = mock_response

            result = await service.translate(
                text="Hello",
                source_lang="en",
                target_lang="vi",
                provider="google_ai",
            )

            assert result["translated_text"] == "Xin chào"
            assert result["model"] == "gemini-2.0-flash-exp"

    @pytest.mark.asyncio
    async def test_translate_with_openai(self, service):
        """Test translation using OpenAI via HTTP"""
        mock_ai_response = {
            "text": json.dumps({"translated_text": "你好"}),
            "model": "gpt-4o-mini",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_ai_response
            mock_post.return_value = mock_response

            result = await service.translate(
                text="Hello",
                source_lang="en",
                target_lang="zh",
                provider="openai",
            )

            assert result["translated_text"] == "你好"
            assert result["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_ai_service_error(self, service):
        """Test handling of AI service HTTP errors"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response

            with pytest.raises(ValueError, match="AI service error"):
                await service.translate(
                    text="Hello",
                    source_lang="en",
                    target_lang="ko",
                    provider="claude",
                )

    @pytest.mark.asyncio
    async def test_ai_service_timeout(self, service):
        """Test handling of AI service timeout"""
        import httpx

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(ValueError, match="timed out"):
                await service.translate(
                    text="Hello",
                    source_lang="en",
                    target_lang="ko",
                    provider="claude",
                )

    @pytest.mark.asyncio
    async def test_ai_service_connection_error(self, service):
        """Test handling of AI service connection errors"""
        import httpx

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(ValueError, match="Failed to connect"):
                await service.translate(
                    text="Hello",
                    source_lang="en",
                    target_lang="ko",
                    provider="claude",
                )

    def test_parse_translation_response_json(self, service):
        """Test parsing valid JSON response"""
        response = json.dumps({"translated_text": "안녕하세요"})
        result = service._parse_translation_response(response)
        assert result == "안녕하세요"

    def test_parse_translation_response_markdown(self, service):
        """Test parsing JSON from markdown code block"""
        response = '```json\n{"translated_text": "안녕하세요"}\n```'
        result = service._parse_translation_response(response)
        assert result == "안녕하세요"

    def test_parse_translation_response_raw_text(self, service):
        """Test parsing raw text (fallback)"""
        response = "안녕하세요"
        result = service._parse_translation_response(response)
        assert result == "안녕하세요"

    def test_parse_translation_response_with_prefix(self, service):
        """Test parsing text with common prefixes"""
        response = "Translation: 안녕하세요"
        result = service._parse_translation_response(response)
        assert result == "안녕하세요"

    def test_parse_translation_response_empty(self, service):
        """Test parsing empty response"""
        with pytest.raises(ValueError, match="Empty response from AI"):
            service._parse_translation_response("")
