"""Diary generation service"""

from datetime import datetime, date
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.config import settings
from app.core.ai_helper import call_ai_service
from app.core.logging_config import logger
from app.models import DiaryEntry, Conversation, Message, Profile, DiaryLengthType, ConversationStatus
from app.diary.services.prompts import (
    create_diary_generation_prompt,
    create_mood_analysis_prompt,
    create_summary_prompt
)


class DiaryService:
    """Diary management service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service_url = settings.ai_service_url
        self.internal_api_key = settings.internal_api_key

    async def generate_diary(
        self,
        user_id: int,
        conversation_id: int,
        title: str,
        length_type: str = "normal"
    ) -> DiaryEntry:
        """
        Generate diary from conversation

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            title: Diary title
            length_type: "summary" | "normal" | "detailed"

        Returns:
            Created DiaryEntry
        """
        # Get conversation with messages
        conv_result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Use the entry_date from the conversation
        entry_date = conversation.entry_date

        # Get messages
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation has no messages"
            )

        # Get profile
        profile_result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile_obj = profile_result.scalar_one_or_none()

        profile_dict = None
        if profile_obj:
            profile_dict = {
                "nickname": profile_obj.nickname,
            }

        # Prepare messages for prompt
        message_list = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        # Generate diary content
        diary_content = await self._generate_diary_content(
            conversation_messages=message_list,
            length_type=length_type,
            entry_date=datetime.combine(entry_date, datetime.min.time()),
            profile=profile_dict
        )

        # Generate mood analysis and summary
        mood = await self._generate_mood_analysis(diary_content)
        summary = await self._generate_summary(diary_content)

        # Create diary entry
        diary_entry = DiaryEntry(
            user_id=user_id,
            conversation_id=conversation_id,
            title=title,
            content=diary_content,
            entry_date=entry_date,
            length_type=DiaryLengthType[length_type],
            mood=mood,
            summary=summary
        )

        self.db.add(diary_entry)
        await self.db.commit()
        await self.db.refresh(diary_entry)

        # Mark conversation as completed
        conversation.status = ConversationStatus.completed
        await self.db.commit()

        return diary_entry

    async def get_diary(self, diary_id: int, user_id: int) -> DiaryEntry:
        """Get specific diary entry"""
        result = await self.db.execute(
            select(DiaryEntry)
            .where(
                DiaryEntry.id == diary_id,
                DiaryEntry.user_id == user_id
            )
        )
        diary = result.scalar_one_or_none()

        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary not found"
            )

        return diary

    async def get_diary_by_date(self, entry_date: date, user_id: int) -> DiaryEntry:
        """Get diary by date"""
        result = await self.db.execute(
            select(DiaryEntry)
            .where(
                DiaryEntry.user_id == user_id,
                DiaryEntry.entry_date == entry_date
            )
        )
        diary = result.scalar_one_or_none()

        if not diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary not found for this date"
            )

        return diary

    async def list_diaries(
        self,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[DiaryEntry], int]:
        """List user's diary entries with optional date range filter"""
        # Build query
        query = select(DiaryEntry).where(DiaryEntry.user_id == user_id)

        # Apply date filters if provided
        if start_date:
            query = query.where(DiaryEntry.entry_date >= start_date)
        if end_date:
            query = query.where(DiaryEntry.entry_date <= end_date)

        # Get total count
        count_result = await self.db.execute(query)
        total = len(count_result.scalars().all())

        # Get entries with pagination
        result = await self.db.execute(
            query
            .order_by(desc(DiaryEntry.entry_date))
            .limit(limit)
            .offset(offset)
        )
        entries = result.scalars().all()

        return entries, total

    async def delete_diary(self, diary_id: int, user_id: int) -> None:
        """Delete diary entry"""
        diary = await self.get_diary(diary_id, user_id)
        await self.db.delete(diary)
        await self.db.commit()

    async def _generate_diary_content(
        self,
        conversation_messages: list[dict],
        length_type: str,
        entry_date: datetime,
        profile: dict = None
    ) -> str:
        """Call AI service to generate diary content"""
        prompt = create_diary_generation_prompt(
            conversation_messages=conversation_messages,
            length_type=length_type,
            entry_date=entry_date,
            profile=profile
        )

        # Token limits based on length type
        max_tokens = {
            "summary": 500,
            "normal": 2000,
            "detailed": 4000
        }

        try:
            result = await call_ai_service(
                prompt=prompt,
                provider="claude",
                max_tokens=max_tokens.get(length_type, 2000),
                temperature=0.7,
                timeout=60.0
            )
            return result["text"]

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Diary generation timeout"
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

    async def _generate_mood_analysis(self, diary_content: str) -> str:
        """Generate mood analysis from diary content"""
        prompt = create_mood_analysis_prompt(diary_content)

        try:
            result = await call_ai_service(
                prompt=prompt,
                provider="claude",
                max_tokens=50,
                temperature=0.3,
                timeout=15.0
            )
            return result["text"].strip()

        except Exception as e:
            logger.error(f"Mood analysis error: {e}", exc_info=True)
            return "중립"  # Default fallback

    async def _generate_summary(self, diary_content: str) -> str:
        """Generate summary from diary content"""
        prompt = create_summary_prompt(diary_content)

        try:
            result = await call_ai_service(
                prompt=prompt,
                provider="claude",
                max_tokens=200,
                temperature=0.5,
                timeout=15.0
            )
            return result["text"].strip()

        except Exception as e:
            logger.error(f"Summary generation error: {e}", exc_info=True)
            return None  # Summary is optional
