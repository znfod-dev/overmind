"""Tests for Translation API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.translation.main import translation_app


class TestTranslationAPI:
    """Test Translation API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(translation_app)

    def test_get_languages(self, client):
        """Test GET /api/languages endpoint"""
        response = client.get("/api/languages")

        assert response.status_code == 200
        data = response.json()

        assert "languages" in data
        assert len(data["languages"]) == 5

        # Check for all supported languages
        codes = [lang["code"] for lang in data["languages"]]
        assert "ko" in codes
        assert "vi" in codes
        assert "en" in codes
        assert "zh" in codes
        assert "ru" in codes

    def test_translate_success(self, client):
        """Test POST /api/translate with valid request - no auth required"""
        mock_result = {
            "translated_text": "안녕하세요",
            "model": "claude-3-5-sonnet-20241022",
            "raw_response": '{"translated_text": "안녕하세요"}',
        }

        with patch(
            "app.translation.routers.api.TranslationService.translate"
        ) as mock_translate:
            mock_translate.return_value = mock_result

            response = client.post(
                "/api/translate",
                json={
                    "text": "Hello",
                    "source_lang": "en",
                    "target_lang": "ko",
                    "provider": "claude",
                },
                # No X-API-Key header needed
            )

            assert response.status_code == 200
            data = response.json()

            assert data["translated_text"] == "안녕하세요"
            assert data["source_lang"] == "en"
            assert data["target_lang"] == "ko"
            assert data["provider"] == "claude"
            assert data["model"] == "claude-3-5-sonnet-20241022"

    def test_translate_missing_text(self, client):
        """Test POST /api/translate with missing text"""
        response = client.post(
            "/api/translate",
            json={
                "source_lang": "en",
                "target_lang": "ko",
                "provider": "claude",
            },
        )

        assert response.status_code == 422

    def test_translate_invalid_language(self, client):
        """Test POST /api/translate with invalid language code"""
        response = client.post(
            "/api/translate",
            json={
                "text": "Hello",
                "source_lang": "invalid",
                "target_lang": "ko",
                "provider": "claude",
            },
        )

        assert response.status_code == 422

    def test_translate_invalid_provider(self, client):
        """Test POST /api/translate with invalid provider"""
        response = client.post(
            "/api/translate",
            json={
                "text": "Hello",
                "source_lang": "en",
                "target_lang": "ko",
                "provider": "invalid_provider",
            },
        )

        assert response.status_code == 422

    def test_translate_text_too_long(self, client):
        """Test POST /api/translate with text exceeding limit"""
        long_text = "a" * 10001  # Exceeds 10,000 character limit

        response = client.post(
            "/api/translate",
            json={
                "text": long_text,
                "source_lang": "en",
                "target_lang": "ko",
                "provider": "claude",
            },
        )

        assert response.status_code == 422

    def test_translate_service_error(self, client):
        """Test POST /api/translate when service fails"""
        with patch(
            "app.translation.routers.api.TranslationService.translate"
        ) as mock_translate:
            mock_translate.side_effect = ValueError("Translation failed")

            response = client.post(
                "/api/translate",
                json={
                    "text": "Hello",
                    "source_lang": "en",
                    "target_lang": "ko",
                    "provider": "claude",
                },
            )

            assert response.status_code == 400
            assert "Translation failed" in response.json()["detail"]

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "translation"
        assert "features" in data
        assert "languages" in data
        assert "providers" in data
