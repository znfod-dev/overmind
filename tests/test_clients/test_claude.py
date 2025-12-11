"""Claude 클라이언트 테스트"""

import pytest

from app.clients.claude_client import ClaudeClient


@pytest.mark.asyncio
async def test_claude_send_message():
    """Claude API 메시지 전송 테스트"""
    client = ClaudeClient()

    # 간단한 프롬프트로 테스트
    response = await client.send_message(
        prompt="Say 'Hello from Claude!' in one sentence.", max_tokens=100
    )

    # 응답 확인
    assert response is not None
    assert "content" in response
    assert len(response["content"]) > 0

    # 텍스트 추출
    text = client.extract_text(response)
    assert text is not None
    assert len(text) > 0

    print(f"\nClaude Response: {text}")
