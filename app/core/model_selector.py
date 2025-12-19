"""AI Model Selector Service"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, Subscription, AIModelPriority
from app.models.subscription import SubscriptionTier


class AIModelSelector:
    """사용자 국가 및 티어에 따라 최적 AI 모델 선택"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_model_for_user(
        self,
        user_id: int
    ) -> tuple[str, str]:
        """
        사용자에게 적합한 AI 모델 반환

        Args:
            user_id: 사용자 ID

        Returns:
            (provider, model) - 예: ("openai", "gpt-4o-mini")

        Example:
            >>> selector = AIModelSelector(db)
            >>> provider, model = await selector.get_model_for_user(user_id=1)
            >>> print(f"{provider}: {model}")
            openai: gpt-4o-mini
        """
        # 1. 사용자 프로필 조회 (국가 정보)
        profile_result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        country = profile.country if profile and profile.country else "WW"

        # 2. 사용자 구독 정보 조회 (티어 결정)
        subscription_result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = subscription_result.scalar_one_or_none()

        # tier 결정: PREMIUM이면 "premium", 아니면 "basic"
        tier = "premium" if subscription and subscription.tier == SubscriptionTier.PREMIUM else "basic"

        # 3. 국가별 우선순위 조회
        result = await self.db.execute(
            select(AIModelPriority).where(
                AIModelPriority.country == country,
                AIModelPriority.tier == tier
            )
        )
        priority = result.scalar_one_or_none()

        # 4. 우선순위가 없으면 전세계(WW) 기본값 사용
        if not priority:
            result = await self.db.execute(
                select(AIModelPriority).where(
                    AIModelPriority.country == "WW",
                    AIModelPriority.tier == tier
                )
            )
            priority = result.scalar_one_or_none()

        # 5. 1순위 모델 선택 (DB에 데이터가 없으면 하드코딩된 기본값 사용)
        if priority:
            provider = priority.priority_1
        else:
            # DB에 우선순위 설정이 전혀 없을 경우: WW basic 기본값 (openai)
            provider = "openai"

        # 6. Provider별 기본 모델 매핑
        model_map = {
            "openai": "gpt-4o-mini" if tier == "basic" else "gpt-4o",
            "google_ai": "gemini-2.0-flash-exp" if tier == "basic" else "gemini-2.0-flash-exp",
            "claude": "claude-haiku-4-5" if tier == "basic" else "claude-opus-4-5-20251101"
        }

        return provider, model_map.get(provider, "gpt-4o-mini")
