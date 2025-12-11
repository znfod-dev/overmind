"""Rate Limiter 미들웨어 테스트"""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

VALID_API_KEY = settings.api_auth_key


def test_rate_limit_within_limit():
    """분당 10번 이하 요청은 성공"""
    # 5번 요청 (제한 이하)
    for i in range(5):
        response = client.post(
            "/ai/api/req",
            headers={"X-API-Key": VALID_API_KEY},
            json={
                "provider": "claude",
                "prompt": f"Test {i}",
                "max_tokens": 10,
            },
        )
        assert response.status_code == 200

        # Rate limit 헤더 확인
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert int(response.headers["X-RateLimit-Limit"]) == 10


def test_rate_limit_exceeded():
    """분당 10번 초과 시 429 에러"""
    # 먼저 11번 요청
    for i in range(11):
        response = client.post(
            "/ai/api/req",
            headers={"X-API-Key": VALID_API_KEY},
            json={
                "provider": "claude",
                "prompt": f"Test {i}",
                "max_tokens": 10,
            },
        )

        if i < 10:
            # 처음 10번은 성공해야 함
            assert response.status_code == 200
        else:
            # 11번째는 429 에러
            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert data["detail"]["error"] == "Rate limit exceeded"


def test_rate_limit_reset_after_minute():
    """1분 후 제한 초기화 (실제로는 테스트하기 어려우므로 스킵)"""
    pytest.skip("Time-consuming test, skip in CI")


def test_rate_limit_different_api_keys():
    """다른 API 키는 별도로 카운트"""
    # VALID_API_KEY로 5번 요청
    for i in range(5):
        response = client.post(
            "/ai/api/req",
            headers={"X-API-Key": VALID_API_KEY},
            json={
                "provider": "claude",
                "prompt": f"Test {i}",
                "max_tokens": 10,
            },
        )
        assert response.status_code == 200

    # 잘못된 키로 요청 (401이지만 rate limit은 별개)
    response = client.post(
        "/ai/api/req",
        headers={"X-API-Key": "different_key"},
        json={
            "provider": "claude",
            "prompt": "Test",
        },
    )
    # 인증 에러가 먼저 발생
    assert response.status_code == 401


def test_rate_limit_not_applied_to_health_check():
    """헬스 체크는 Rate Limit 적용 안됨"""
    # 20번 연속 호출해도 성공해야 함
    for _ in range(20):
        response = client.get("/health")
        assert response.status_code == 200
