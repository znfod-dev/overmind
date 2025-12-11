"""Diary conversation and entry models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Date
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ConversationStatus(enum.Enum):
    """Conversation status enum"""
    active = "active"
    completed = "completed"


class MessageRole(enum.Enum):
    """Message role enum"""
    ai = "ai"
    user = "user"


class DiaryLengthType(enum.Enum):
    """Diary length type enum"""
    summary = "summary"
    normal = "normal"
    detailed = "detailed"


class Conversation(Base):
    """Diary conversation session"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)  # 대화가 속한 날짜
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.active, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntry", back_populates="conversation")


class Message(Base):
    """Individual message in conversation"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


class DiaryEntry(Base):
    """Generated diary entry"""

    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    entry_date = Column(Date, nullable=False, index=True)
    length_type = Column(Enum(DiaryLengthType), nullable=False)

    # AI 분석 결과
    mood = Column(String(50), nullable=True)  # 감정 분석 결과 (긍정적/부정적/중립/복합)
    summary = Column(String(500), nullable=True)  # 일기 요약

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="diary_entries")
    conversation = relationship("Conversation", back_populates="diary_entries")
