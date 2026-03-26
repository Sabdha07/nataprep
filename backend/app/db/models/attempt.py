import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, DateTime, Enum as SAEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class SessionMode(str, enum.Enum):
    concept = "concept"
    adaptive = "adaptive"
    mock_test = "mock_test"
    drawing = "drawing"
    mixed = "mixed"
    review = "review"


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class ErrorType(str, enum.Enum):
    conceptual = "conceptual"
    careless = "careless"
    time_pressure = "time_pressure"
    unknown = "unknown"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mode: Mapped[SessionMode] = mapped_column(SAEnum(SessionMode), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    config: Mapped[dict | None] = mapped_column(JSONB)
    # config format: {"concept_ids": [...], "difficulty_range": [0.3, 0.7], ...}
    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.active)

    user = relationship("User", back_populates="sessions")
    attempts = relationship("QuestionAttempt", back_populates="session", cascade="all, delete-orphan")
    drawing_submissions = relationship("DrawingSubmission", back_populates="session")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("practice_sessions.id"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    selected_option_id: Mapped[str | None] = mapped_column(String(10))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer)
    confidence_level: Mapped[int | None] = mapped_column(Integer)  # 1-5
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="attempts")
    session = relationship("PracticeSession", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")
    mistake = relationship("MistakeLog", back_populates="attempt", uselist=False)


class MistakeLog(Base):
    __tablename__ = "mistake_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("question_attempts.id"), nullable=False)
    error_type: Mapped[ErrorType] = mapped_column(SAEnum(ErrorType), default=ErrorType.unknown)
    concept_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="mistakes")
    question = relationship("Question", back_populates="mistakes")
    attempt = relationship("QuestionAttempt", back_populates="mistake")
