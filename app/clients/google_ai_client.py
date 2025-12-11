"""Google AI Studio (Gemini) 클라이언트"""

import json
from typing import Any, AsyncIterator

from app.config import settings
from app.core.http_client import get_http_client


class GoogleAIClient:
    """
    Google AI (Gemini) 클라이언트 (Stateless)

    Google Generative Language API 연동
    https://ai.google.dev/api/rest
    """

    def __init__(self):
        self.api_key = settings.google_ai_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.5-flash"  # 기본 모델

    async def send_message(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> dict[str, Any]:
        """
        Google AI에 메시지 전송

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름 (기본값: gemini-pro)
            temperature: 온도 (0.0 ~ 1.0)
            max_output_tokens: 최대 출력 토큰 수

        Returns:
            Google AI API 응답 (dict)
        """
        client = get_http_client()

        model_name = model or self.model
        url = f"{self.base_url}/models/{model_name}:generateContent"

        params = {"key": self.api_key}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        response = await client.post(url, params=params, json=payload)

        response.raise_for_status()
        return response.json()

    async def send_message_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """
        Google AI에 메시지 전송 (스트리밍)

        Args:
            prompt: 사용자 프롬프트
            model: 모델 이름
            temperature: 온도
            max_output_tokens: 최대 출력 토큰 수

        Yields:
            생성된 텍스트 청크
        """
        client = get_http_client()

        model_name = model or self.model
        url = f"{self.base_url}/models/{model_name}:streamGenerateContent"

        params = {"key": self.api_key, "alt": "sse"}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        async with client.stream("POST", url, params=params, json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # "data: " 제거

                    try:
                        chunk = json.loads(data)

                        # candidates에서 텍스트 추출
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                text = parts[0].get("text", "")
                                if text:
                                    yield text

                    except json.JSONDecodeError:
                        continue

    def extract_text(self, response: dict[str, Any]) -> str:
        """
        Google AI 응답에서 텍스트 추출

        Args:
            response: Google AI API 응답

        Returns:
            생성된 텍스트
        """
        try:
            candidates = response.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except (KeyError, IndexError):
            pass
        return ""
