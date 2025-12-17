"""Subscription models"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class SubscriptionTier(enum.Enum):
    """구독 티어"""
    FREE = "free"
    PREMIUM = "premium"


class Subscription(Base):
    """사용자 구독 정보"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)

    # 광고 제거 (일회성 구매)
    ad_free_purchased = Column(Boolean, default=False, nullable=False)
    ad_free_purchased_at = Column(DateTime, nullable=True)

    # 프리미엄 구독 (월 단위)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="subscription")
