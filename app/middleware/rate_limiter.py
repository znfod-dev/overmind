"""Rate Limiting 미들웨어"""

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import logger


class RateLimiter(BaseHTTPMiddleware):
    """
    Rate Limiting 미들웨어

    각 API 키별로 분당 요청 횟수 제한
    """

    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        logger.info(f"Rate Limiter initialized: {requests_per_minute} requests/minute")

    async def dispatch(self, request: Request, call_next):
        # Rate Limiting은 /api/req 엔드포인트에만 적용
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # API 키 가져오기
        api_key = request.headers.get("X-API-Key", "anonymous")

        # 현재 시간
        current_time = time.time()
        one_minute_ago = current_time - 60

        # 1분 이내의 요청만 유지
        self.request_times[api_key] = [
            req_time
            for req_time in self.request_times[api_key]
            if req_time > one_minute_ago
        ]

        # 요청 횟수 체크
        if len(self.request_times[api_key]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded | API Key: {api_key[:10]}... | "
                f"Requests: {len(self.request_times[api_key])}/{self.requests_per_minute}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.requests_per_minute,
                    "window": "1 minute",
                    "message": "Too many requests. Please try again later.",
                },
            )

        # 현재 요청 기록
        self.request_times[api_key].append(current_time)

        # 요청 처리
        response = await call_next(request)

        # 남은 요청 횟수를 헤더에 추가
        remaining = self.requests_per_minute - len(self.request_times[api_key])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
