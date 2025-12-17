"""AI Configuration Service"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models import AIModelPriority


class AIConfigService:
    """AI 모델 우선순위 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_priorities(self) -> list[AIModelPriority]:
        """
        모든 AI 모델 우선순위 설정 조회

        Returns:
            AIModelPriority 목록 (국가, 티어별 정렬)
        """
        result = await self.db.execute(
            select(AIModelPriority).order_by(
                AIModelPriority.country,
                AIModelPriority.tier
            )
        )
        return result.scalars().all()

    async def get_priority(self, country: str, tier: str) -> AIModelPriority | None:
        """
        특정 국가/티어의 우선순위 조회

        Args:
            country: 국가 코드 (KR, VN, US, JP, WW)
            tier: 티어 (basic, premium)

        Returns:
            AIModelPriority 또는 None
        """
        result = await self.db.execute(
            select(AIModelPriority).where(
                AIModelPriority.country == country,
                AIModelPriority.tier == tier
            )
        )
        return result.scalar_one_or_none()

    async def update_priority(
        self,
        country: str,
        tier: str,
        priority_1: str,
        priority_2: str,
        priority_3: str
    ) -> AIModelPriority:
        """
        AI 모델 우선순위 업데이트 (없으면 생성)

        Args:
            country: 국가 코드
            tier: 티어
            priority_1: 1순위 AI provider
            priority_2: 2순위 AI provider
            priority_3: 3순위 AI provider

        Returns:
            업데이트된 AIModelPriority

        Raises:
            HTTPException: Invalid provider names
        """
        # Validate provider names
        valid_providers = {"openai", "google_ai", "claude"}
        for provider in [priority_1, priority_2, priority_3]:
            if provider not in valid_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {provider}. Must be one of {valid_providers}"
                )

        # Check if exists
        priority = await self.get_priority(country, tier)

        if not priority:
            # Create new
            priority = AIModelPriority(
                country=country,
                tier=tier,
                priority_1=priority_1,
                priority_2=priority_2,
                priority_3=priority_3
            )
            self.db.add(priority)
        else:
            # Update existing
            priority.priority_1 = priority_1
            priority.priority_2 = priority_2
            priority.priority_3 = priority_3
            priority.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(priority)

        return priority

    async def delete_priority(self, country: str, tier: str) -> None:
        """
        AI 모델 우선순위 삭제

        Args:
            country: 국가 코드
            tier: 티어

        Raises:
            HTTPException: Priority not found
        """
        priority = await self.get_priority(country, tier)

        if not priority:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Priority not found for {country}/{tier}"
            )

        await self.db.delete(priority)
        await self.db.commit()
