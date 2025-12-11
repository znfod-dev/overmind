"""HTTP 클라이언트 관리 - 전역 AsyncClient 인스턴스"""

import httpx

# 전역 HTTP 클라이언트 (앱 생명주기 동안 유지)
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """
    공유 HTTP 클라이언트 인스턴스 반환

    연결 풀을 재사용하여 성능 최적화
    """
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client():
    """HTTP 클라이언트 종료"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
