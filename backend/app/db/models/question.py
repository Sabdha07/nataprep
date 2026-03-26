import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, Integer, ForeignKey, DateTime, Enum as SAEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class QuestionSource(str, enum.Enum):
    scraped = "scraped"
    generated = "generated"
    manual = "manual"


class QuestionType(str, enum.Enum):
    mcq = "mcq"       # single correct
    msq = "msq"       # multiple correct
    numerical = "numerical"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # options format: [{"id": "A", "text": "...", "is_correct": true}, ...]
    correct_option_id: Mapped[str] = mapped_column(String(10), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    source: Mapped[QuestionSource] = mapped_column(SAEnum(QuestionSource), default=QuestionSource.manual)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list | None] = mapped_column(ARRAY(String))
    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType), default=QuestionType.mcq)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=90)
    embedding_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    concept_mappings = relationship("QuestionConcept", back_populates="question", cascade="all, delete-orphan")
    attempts = relationship("QuestionAttempt", back_populates="question")
    mistakes = relationship("MistakeLog", back_populates="question")


class QuestionConcept(Base):
    __tablename__ = "question_concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)

    question = relationship("Question", back_populates="concept_mappings")
    concept = relationship("Concept", back_populates="question_mappings")
