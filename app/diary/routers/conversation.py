"""Conversation management endpoints"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User, Conversation, Message
from app.diary.schemas.requests import StartConversationRequest, SendMessageRequest
from app.diary.schemas.responses import ConversationResponse, AIMessageResponse, MessageResponse
from app.diary.services.conversation import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start new conversation",
    description="Start a new diary conversation session"
)
async def start_conversation(
    request: StartConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """
    Start a new diary conversation

    - One active conversation per user per date
    - AI starts with greeting message
    """
    service = ConversationService(db)
    conversation, initial_message = await service.start_conversation(
        user_id=current_user.id,
        entry_date=request.entry_date,
        initial_message=request.initial_message
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

    - Saves user message
    - Calls AI service for response
    - Returns AI response
    """
    service = ConversationService(db)
    ai_message = await service.send_message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=request.content
    )

    return AIMessageResponse(
        message_id=ai_message.id,
        content=ai_message.content,
        created_at=ai_message.created_at
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
