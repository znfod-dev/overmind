"""OpenAI 클라이언트"""

import json
from typing import Any, AsyncIterator

from app.config import settings
from app.core.http_client import get_http_client


class OpenAIClient:
    """
    OpenAI 클라이언트 (Stateless)

    OpenAI Chat Completions API 연동
    https://platform.openai.com/docs/api-reference/chat
    """

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # 기본 모델 (최신, GPT-4 수준 성능)

    async def send_message(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        OpenAI에 메시지 전송

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름 (기본값: gpt-3.5-turbo)
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 2.0)

        Returns:
            OpenAI API 응답 (dict)
        """
        client = get_http_client()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await client.post(
            f"{self.base_url}/chat/completions", headers=headers, json=payload
        )

        response.raise_for_status()
        return response.json()

    async def send_message_stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        OpenAI에 메시지 전송 (스트리밍)

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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        async with client.stream(
            "POST", f"{self.base_url}/chat/completions", headers=headers, json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # "data: " 제거

                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)

                        # choices에서 텍스트 추출
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield text

                    except json.JSONDecodeError:
                        continue

    def extract_text(self, response: dict[str, Any]) -> str:
        """
        OpenAI 응답에서 텍스트 추출

        Args:
            response: OpenAI API 응답

        Returns:
            생성된 텍스트
        """
        try:
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")
        except (KeyError, IndexError):
            pass
        return ""
