"""AI Configuration models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from app.database import Base


class AIModelPriority(Base):
    """AI 모델 우선순위 설정"""
    __tablename__ = "ai_model_priorities"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(2), nullable=False, index=True)  # KR, VN, US, JP, WW(전세계)
    tier = Column(String(20), nullable=False, index=True)  # "basic", "premium"
    priority_1 = Column(String(20), nullable=False)  # "openai", "google_ai", "claude"
    priority_2 = Column(String(20), nullable=False)
    priority_3 = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # unique constraint: (country, tier)
    __table_args__ = (
        UniqueConstraint('country', 'tier', name='uq_country_tier'),
    )
