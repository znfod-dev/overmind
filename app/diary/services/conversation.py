"""Conversation management service"""

from typing import Optional
import httpx
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.config import settings
from app.core.ai_helper import call_ai_for_user
from app.models import Conversation, Message, Profile, ConversationStatus, MessageRole
from app.diary.services.prompts import create_conversation_prompt


class ConversationService:
    """Conversation management service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service_url = settings.ai_service_url
        self.internal_api_key = settings.internal_api_key

    async def start_conversation(
        self,
        user_id: int,
        entry_date: date,
        initial_message: str = "오늘 하루 어떠셨어요?"
    ) -> tuple[Conversation, Message]:
        """
        Start a new diary conversation

        Args:
            user_id: User ID
            entry_date: Date for this diary entry
            initial_message: AI's first message

        Returns:
            Tuple of (Conversation, initial Message)
        """
        # Create conversation
        conversation = Conversation(
            user_id=user_id,
            entry_date=entry_date,
            status=ConversationStatus.active
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        # Create initial AI message
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ai,
            content=initial_message
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return conversation, message

    async def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """Get conversation with messages"""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_conversation(
        self,
        user_id: int,
        entry_date: date
    ) -> Optional[Conversation]:
        """Get user's active conversation for specific date"""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.entry_date == entry_date,
                Conversation.status == ConversationStatus.active
            )
        )
        return result.scalar_one_or_none()

    async def send_message(
        self,
        conversation_id: int,
        user_id: int,
        content: str
    ) -> Message:
        """
        Send user message and get AI response

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            content: User message content

        Returns:
            AI response Message
        """
        # Get conversation
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        if conversation.status != ConversationStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is not active"
            )

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.user,
            content=content
        )
        self.db.add(user_message)
        await self.db.commit()

        # Get conversation history
        history_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = history_result.scalars().all()

        # Get user profile
        profile_result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile_obj = profile_result.scalar_one_or_none()

        profile_dict = None
        if profile_obj:
            profile_dict = {
                "nickname": profile_obj.nickname,
                "job": profile_obj.job,
                "hobbies": profile_obj.hobbies,
                "family_composition": profile_obj.family_composition,
                "pets": profile_obj.pets,
            }

        # Build conversation history for prompt
        history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages[:-1]  # Exclude the latest user message
        ]

        # Generate AI response
        ai_response_text = await self._call_ai_service(
            user_id=user_id,
            user_message=content,
            conversation_history=history,
            profile=profile_dict
        )

        # Save AI message
        ai_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ai,
            content=ai_response_text
        )
        self.db.add(ai_message)
        await self.db.commit()
        await self.db.refresh(ai_message)

        return ai_message

    async def complete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Conversation:
        """Mark conversation as completed"""
        conversation = await self.get_conversation(conversation_id, user_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        conversation.status = ConversationStatus.completed
        conversation.ended_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def _call_ai_service(
        self,
        user_id: int,
        user_message: str,
        conversation_history: list[dict],
        profile: Optional[dict] = None
    ) -> str:
        """
        Call AI service to generate response (사용자별 최적 모델)

        Uses call_ai_for_user to automatically select best AI model
        based on user's country and subscription tier.
        """
        prompt = create_conversation_prompt(user_message, conversation_history, profile)

        try:
            result = await call_ai_for_user(
                user_id=user_id,
                prompt=prompt,
                db=self.db,
                max_tokens=500,
                temperature=0.8,
                timeout=30.0
            )
            return result["text"]

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI service timeout"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI service error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service unavailable: {str(e)}"
            )
