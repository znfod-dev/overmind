"""공통 AI 서비스 호출 헬퍼"""

from typing import Any, Dict

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.http_client import get_http_client
from app.core.logging_config import logger


async def call_ai_service(
    prompt: str,
    provider: str = "claude",
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    내부 서비스용 AI API 호출 공통 함수

    이 함수는 다른 서비스(translation, diary, etc)에서 AI Gateway를 호출할 때 사용합니다.
    전역 HTTP 클라이언트를 재사용하여 연결 풀을 효율적으로 관리합니다.

    Args:
        prompt: AI에게 전달할 프롬프트
        provider: AI 제공자 ("claude", "google_ai", "openai")
        model: 특정 모델 지정 (선택, None이면 기본 모델 사용)
        max_tokens: 최대 생성 토큰 수
        temperature: 생성 온도 (0.0 ~ 2.0)
        timeout: 요청 타임아웃 (초)

    Returns:
        AI API 응답 JSON (dict)
        예: {"text": "생성된 텍스트", "model": "claude-3-5-sonnet-20241022", ...}

    Raises:
        httpx.HTTPStatusError: API 호출 실패 (4xx, 5xx 에러)
        httpx.TimeoutException: 요청 타임아웃
        httpx.RequestError: 네트워크 에러

    Example:
        >>> result = await call_ai_service(
        ...     prompt="Hello, world!",
        ...     provider="claude",
        ...     max_tokens=100,
        ...     temperature=0.7,
        ...     timeout=30.0
        ... )
        >>> print(result["text"])
    """
    client = get_http_client()

    try:
        response = await client.post(
            f"{settings.ai_service_url}/ai/api/req",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": settings.internal_api_key,
            },
            json={
                "provider": provider,
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=timeout
        )

        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException as e:
        logger.error(f"AI service timeout after {timeout}s: {e}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"AI service HTTP error {e.response.status_code}: {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"AI service request error: {e}")
        raise


async def call_ai_for_user(
    user_id: int,
    prompt: str,
    db: AsyncSession,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    사용자별 최적 AI 모델로 호출 (국가 + 구독 티어 기반)

    이 함수는 사용자의 국가 정보와 구독 티어에 따라 자동으로 최적 AI 모델을 선택하여 호출합니다.
    AIModelSelector 서비스를 통해 우선순위가 높은 모델을 선택합니다.

    Args:
        user_id: 사용자 ID
        prompt: AI에게 전달할 프롬프트
        db: 데이터베이스 세션 (필수)
        max_tokens: 최대 생성 토큰 수
        temperature: 생성 온도 (0.0 ~ 2.0)
        timeout: 요청 타임아웃 (초)

    Returns:
        AI API 응답 JSON (dict)

    Raises:
        httpx.HTTPStatusError: API 호출 실패
        httpx.TimeoutException: 요청 타임아웃
        httpx.RequestError: 네트워크 에러

    Example:
        >>> result = await call_ai_for_user(
        ...     user_id=1,
        ...     prompt="안녕하세요!",
        ...     db=db_session,
        ...     max_tokens=100
        ... )
        >>> print(result["text"])
    """
    from app.core.model_selector import AIModelSelector

    selector = AIModelSelector(db)
    provider, model = await selector.get_model_for_user(user_id)

    logger.info(f"User {user_id} using AI model: {provider}/{model}")

    return await call_ai_service(
        prompt=prompt,
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout
    )
