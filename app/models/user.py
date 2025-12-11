"""User and Profile models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User authentication model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Admin and account status fields
    role = Column(String(20), default="user", nullable=False)  # "admin" or "user"
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntry", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """User profile for AI personalization"""

    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Profile fields (all optional)
    nickname = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other, prefer_not_to_say
    job = Column(String(100), nullable=True)
    hobbies = Column(Text, nullable=True)  # JSON string: ["reading", "gaming"]
    family_composition = Column(String(200), nullable=True)
    pets = Column(String(200), nullable=True)

    # Relationship
    user = relationship("User", back_populates="profile")
