"""Claude (Anthropic) AI 클라이언트"""

import json
from typing import Any, AsyncIterator

from app.config import settings
from app.core.http_client import get_http_client


class ClaudeClient:
    """
    Claude AI 클라이언트 (Stateless)

    Anthropic Messages API v1 연동
    https://docs.anthropic.com/claude/reference/messages_post
    """

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-haiku-4-5"  # 기본 모델 (최신, 빠르고 비용 효율적)

    async def send_message(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
    ) -> dict[str, Any]:
        """
        Claude에 메시지 전송

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름 (기본값: claude-3-5-sonnet-20241022)
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0)

        Returns:
            Claude API 응답 (dict)
        """
        client = get_http_client()

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = await client.post(
            f"{self.base_url}/messages", headers=headers, json=payload
        )

        response.raise_for_status()
        return response.json()

    async def send_message_stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 1.0,
    ) -> AsyncIterator[str]:
        """
        Claude에 메시지 전송 (스트리밍)

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름
            max_tokens: 최대 토큰 수
            temperature: 온도

        Yields:
            생성된 텍스트 청크
        """
        client = get_http_client()

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        async with client.stream(
            "POST", f"{self.base_url}/messages", headers=headers, json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # "data: " 제거

                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)

                        # content_block_delta 이벤트에서 텍스트 추출
                        if chunk.get("type") == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield text

                    except json.JSONDecodeError:
                        continue

    def extract_text(self, response: dict[str, Any]) -> str:
        """
        Claude 응답에서 텍스트 추출

        Args:
            response: Claude API 응답

        Returns:
            생성된 텍스트
        """
        if "content" in response and len(response["content"]) > 0:
            return response["content"][0].get("text", "")
        return ""
