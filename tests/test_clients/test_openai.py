"""OpenAI 클라이언트 테스트"""

import pytest

from app.clients.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_openai_send_message():
    """OpenAI API 메시지 전송 테스트"""
    client = OpenAIClient()

    # 간단한 프롬프트로 테스트
    response = await client.send_message(
        prompt="Say 'Hello from OpenAI!' in one sentence.", max_tokens=100
    )

    # 응답 확인
    assert response is not None
    assert "choices" in response
    assert len(response["choices"]) > 0

    # 텍스트 추출
    text = client.extract_text(response)
    assert text is not None
    assert len(text) > 0

    print(f"\nOpenAI Response: {text}")
