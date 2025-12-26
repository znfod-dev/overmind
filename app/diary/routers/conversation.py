"""Conversation management endpoints"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User, Conversation, Message
from app.diary.schemas.requests import StartConversationRequest, SendMessageRequest
from app.diary.schemas.responses import ConversationResponse, AIMessageResponse, MessageResponse, ConversationQualityInfo
from app.diary.services.conversation import ConversationService
from app.core.storage import image_storage

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start new conversation",
    description="Start a new diary conversation session with AI-generated greeting"
)
async def start_conversation(
    request: StartConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """
    Start a new diary conversation

    - AI generates contextual greeting based on time and date
    - Timezone and current time provided by client
    - One active conversation per user per date
    """
    service = ConversationService(db)
    conversation, initial_message = await service.start_conversation(
        user_id=current_user.id,
        entry_date=request.entry_date,
        timezone=request.timezone,
        current_time=request.current_time,
        force_new=request.force_new
    )

    # Reload with messages
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation.id)
    )
    conversation = result.scalar_one()

    return ConversationResponse.model_validate(conversation, from_attributes=True)


@router.get(
    "/active",
    response_model=ConversationResponse,
    summary="Get active conversation",
    description="Get user's current active conversation for specific date"
)
async def get_active_conversation(
    entry_date: date = Query(..., description="Date for the diary entry"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """Get active conversation with messages for specific date"""
    service = ConversationService(db)
    conversation = await service.get_active_conversation(current_user.id, entry_date)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active conversation found"
        )

    # Load messages
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation.id)
    )
    conversation = result.scalar_one()

    return ConversationResponse.model_validate(conversation, from_attributes=True)


@router.post(
    "/{conversation_id}/messages",
    response_model=AIMessageResponse,
    summary="Send message",
    description="Send a message and receive AI response"
)
async def send_message(
    conversation_id: int,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AIMessageResponse:
    """
    Send message to conversation

    - Accepts JSON with content field
    - Calls AI service for response
    - Returns AI response with quality info
    """
    message_content = request.content

    # No image handling for now - JSON only
    image_url = None

    # Send message with optional image URL
    print(f"💬 [Router] Received message: conv_id={conversation_id}, user={current_user.id}, content_len={len(message_content)}")

    service = ConversationService(db)
    try:
        ai_message = await service.send_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=message_content,
            image_url=image_url
        )
        print(f"✅ [Router] AI message received: msg_id={ai_message.id}")
    except Exception as e:
        print(f"❌ [Router] Error in send_message: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    # Build quality info from attached quality data
    quality_info = None
    if hasattr(ai_message, 'quality_info') and ai_message.quality_info:
        quality = ai_message.quality_info
        quality_info = ConversationQualityInfo(
            is_sufficient=quality.is_sufficient,
            quality_level=quality.quality_level.value,
            user_message_count=quality.user_message_count,
            total_user_content_length=quality.total_user_content_length,
            avg_user_message_length=quality.avg_user_message_length,
            feedback_message=quality.feedback_message
        )

    return AIMessageResponse(
        message_id=ai_message.id,
        content=ai_message.content,
        created_at=ai_message.created_at,
        quality_info=quality_info
    )


@router.post(
    "/{conversation_id}/complete",
    response_model=ConversationResponse,
    summary="Complete conversation",
    description="Mark conversation as completed"
)
async def complete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """
    Complete conversation

    - Marks conversation as completed
    - Allows starting a new conversation
    """
    service = ConversationService(db)
    conversation = await service.complete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )

    # Reload with messages
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation.id)
    )
    conversation = result.scalar_one()

    return ConversationResponse.model_validate(conversation, from_attributes=True)
