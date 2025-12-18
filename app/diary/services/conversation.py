"""Conversation management service"""

from typing import Optional
import httpx
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.config import settings
from app.core.ai_helper import call_ai_for_user
from app.core.exceptions import BadRequestError, ErrorCode
from app.models import Conversation, Message, Profile, ConversationStatus, MessageRole
from app.diary.services.prompts import create_conversation_prompt, create_initial_greeting_prompt

logger = logging.getLogger(__name__)


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
        timezone: str = "America/Los_Angeles",
        current_time: Optional[datetime] = None
    ) -> tuple[Conversation, Message]:
        """
        Start a new diary conversation with AI-generated greeting

        Args:
            user_id: User ID
            entry_date: Date for this diary entry
            timezone: User's timezone (IANA format)
            current_time: Client's current local time (timezone-aware)

        Returns:
            Tuple of (Conversation, initial Message)

        Raises:
            BadRequestError: If entry_date is in the future
        """
        # Validate timezone (fallback to America/Los_Angeles if invalid)
        try:
            tz = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            logger.warning(f"Invalid timezone: {timezone}, falling back to America/Los_Angeles")
            timezone = "America/Los_Angeles"
            tz = ZoneInfo(timezone)

        # Use client's current time (or fallback to server time)
        if current_time is None:
            current_time = datetime.now(tz)

        # Ensure current_time is timezone-aware
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=tz)

        # Validate entry date (no future dates)
        today = current_time.date()
        if entry_date > today:
            raise BadRequestError(
                error_code=ErrorCode.FUTURE_DIARY_NOT_ALLOWED,
                message="미래 날짜의 일기는 작성할 수 없습니다.",
                details={
                    "entry_date": entry_date.isoformat(),
                    "today": today.isoformat()
                }
            )

        # Generate AI greeting
        prompt = create_initial_greeting_prompt(entry_date, current_time)

        try:
            result = await call_ai_for_user(
                user_id=user_id,
                prompt=prompt,
                db=self.db,
                max_tokens=150,  # Short greeting
                temperature=0.9,  # More creative
                timeout=15.0
            )
            initial_message = result["text"].strip()
        except Exception as e:
            # Fallback to context-aware default if AI fails
            logger.error(f"Failed to generate greeting: {e}", exc_info=True)

            # Generate fallback message based on date
            days_diff = (today - entry_date).days
            if entry_date == today:
                initial_message = "안녕하세요! 오늘 하루는 어떠셨나요?"
            elif days_diff == 1:
                initial_message = "안녕하세요! 어제는 어떤 하루를 보내셨나요?"
            elif days_diff == 2:
                initial_message = "안녕하세요! 그저께는 어떤 일들이 있으셨나요?"
            elif days_diff <= 7:
                initial_message = f"안녕하세요! {entry_date.month}월 {entry_date.day}일에는 어떤 하루를 보내셨나요?"
            else:
                initial_message = f"안녕하세요! {entry_date.month}월 {entry_date.day}일을 기억해보시면, 어떤 일들이 있으셨나요?"

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
