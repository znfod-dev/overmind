"""Google AI 클라이언트 테스트"""

import pytest

from app.clients.google_ai_client import GoogleAIClient


@pytest.mark.asyncio
async def test_google_ai_send_message():
    """Google AI API 메시지 전송 테스트"""
    client = GoogleAIClient()

    # 간단한 프롬프트로 테스트
    response = await client.send_message(
        prompt="Say 'Hello from Gemini!' in one sentence.",
        max_output_tokens=100,
    )

    # 응답 확인
    assert response is not None
    assert "candidates" in response

    # 텍스트 추출
    text = client.extract_text(response)
    assert text is not None
    assert len(text) > 0

    print(f"\nGoogle AI Response: {text}")
