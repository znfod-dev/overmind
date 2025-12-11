"""통합 채팅 API 라우터"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.clients.claude_client import ClaudeClient
from app.clients.google_ai_client import GoogleAIClient
from app.clients.openai_client import OpenAIClient
from app.core.logging_config import logger
from app.dependencies.auth import verify_api_key
from app.schemas.requests import ChatRequest
from app.schemas.responses import ChatResponse, ErrorResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/req",
    response_model=ChatResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    },
)
async def chat_request(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """
    통합 AI 채팅 엔드포인트

    **인증 필요**: X-API-Key 헤더 필수

    **지원 Provider:**
    - `claude`: Claude (Anthropic)
    - `google_ai`: Google AI (Gemini)
    - `openai`: OpenAI (GPT)
    """

    try:
        # Provider별 클라이언트 선택 및 호출
        if request.provider == "claude":
            client = ClaudeClient()
            response = await client.send_message(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            text = client.extract_text(response)
            model_used = response.get("model", client.model)

        elif request.provider == "google_ai":
            client = GoogleAIClient()
            response = await client.send_message(
                prompt=request.prompt,
                model=request.model,
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            text = client.extract_text(response)
            model_used = request.model or client.model

        elif request.provider == "openai":
            client = OpenAIClient()
            response = await client.send_message(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            text = client.extract_text(response)
            model_used = response.get("model", client.model)

        else:
            # 이 경우는 Pydantic validation에서 걸러지지만 명시적 처리
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.provider}",
            )

        # 텍스트 생성 실패 체크
        if not text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract text from AI response",
            )

        return ChatResponse(
            provider=request.provider,
            text=text,
            model=model_used,
        )

    except HTTPException:
        # HTTPException은 그대로 전달
        raise

    except Exception as e:
        # 기타 예외는 500 에러로 변환
        logger.error(f"AI service error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}",
        )


@router.post(
    "/req/stream",
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    },
)
async def chat_request_stream(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    통합 AI 채팅 엔드포인트 (스트리밍)

    **인증 필요**: X-API-Key 헤더 필수

    **지원 Provider:**
    - `claude`: Claude (Anthropic)
    - `google_ai`: Google AI (Gemini)
    - `openai`: OpenAI (GPT)

    **응답 형식**: Server-Sent Events (text/event-stream)
    """

    async def generate_stream():
        """스트리밍 제네레이터"""
        try:
            # Provider별 클라이언트 선택 및 호출
            if request.provider == "claude":
                client = ClaudeClient()
                stream = client.send_message_stream(
                    prompt=request.prompt,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

            elif request.provider == "google_ai":
                client = GoogleAIClient()
                stream = client.send_message_stream(
                    prompt=request.prompt,
                    model=request.model,
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

            elif request.provider == "openai":
                client = OpenAIClient()
                stream = client.send_message_stream(
                    prompt=request.prompt,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported provider: {request.provider}",
                )

            # 스트림 데이터 전송
            async for chunk in stream:
                yield f"data: {chunk}\n\n"

            # 완료 시그널
            yield "data: [DONE]\n\n"

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
        },
    )
