"""통합 채팅 API 테스트"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

# 올바른 API 키
VALID_API_KEY = settings.api_auth_key


def test_chat_without_api_key():
    """API 키 없이 요청 시 422 에러 (FastAPI가 헤더 필수 파라미터 검증)"""
    response = client.post(
        "/ai/api/req",
        json={"provider": "claude", "prompt": "Hello"},
    )
    assert response.status_code == 422


def test_chat_with_invalid_api_key():
    """잘못된 API 키로 요청 시 401 에러"""
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": "wrong_key"},
        json={"provider": "claude", "prompt": "Hello"},
    )
    assert response.status_code == 401


def test_chat_with_claude():
    """Claude provider 테스트"""
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": VALID_API_KEY},
        json={
            "provider": "claude",
            "prompt": "Say 'test success' in 2 words.",
            "max_tokens": 50,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "claude"
    assert "text" in data
    assert len(data["text"]) > 0
    assert "model" in data
    print(f"\nClaude Response: {data}")


def test_chat_with_google_ai():
    """Google AI provider 테스트"""
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": VALID_API_KEY},
        json={
            "provider": "google_ai",
            "prompt": "Say 'test success' in 2 words.",
            "max_tokens": 50,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "google_ai"
    assert "text" in data
    assert len(data["text"]) > 0
    assert "model" in data
    print(f"\nGoogle AI Response: {data}")


def test_chat_with_openai():
    """OpenAI provider 테스트"""
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": VALID_API_KEY},
        json={
            "provider": "openai",
            "prompt": "Say 'test success' in 2 words.",
            "max_tokens": 50,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert "text" in data
    assert len(data["text"]) > 0
    assert "model" in data
    print(f"\nOpenAI Response: {data}")


def test_chat_with_invalid_provider():
    """잘못된 provider 테스트"""
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": VALID_API_KEY},
        json={
            "provider": "invalid_provider",
            "prompt": "Hello",
        },
    )

    # Pydantic validation error
    assert response.status_code == 422
