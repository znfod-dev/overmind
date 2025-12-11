"""요청/응답 로깅 미들웨어"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import logger


class RequestLogger(BaseHTTPMiddleware):
    """요청 및 응답 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # 시작 시간
        start_time = time.time()

        # API 키 마스킹 (보안)
        api_key = request.headers.get("X-API-Key", "none")
        masked_key = f"{api_key[:10]}..." if len(api_key) > 10 else api_key

        # 요청 로깅
        logger.info(
            f"Request | {request.method} {request.url.path} | "
            f"API Key: {masked_key} | Client: {request.client.host if request.client else 'unknown'}"
        )

        # 요청 처리
        try:
            response = await call_next(request)

            # 응답 시간 계산
            duration = time.time() - start_time

            # 응답 로깅
            logger.info(
                f"Response | {request.method} {request.url.path} | "
                f"Status: {response.status_code} | Duration: {duration:.2f}s"
            )

            return response

        except Exception as e:
            # 에러 로깅
            duration = time.time() - start_time
            logger.error(
                f"Error | {request.method} {request.url.path} | "
                f"Duration: {duration:.2f}s | Error: {str(e)}",
                exc_info=True,
            )
            raise
