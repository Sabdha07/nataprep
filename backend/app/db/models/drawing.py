import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, Integer, ForeignKey, DateTime, Enum as SAEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class DrawingCategory(str, enum.Enum):
    imagination = "imagination"
    observation = "observation"
    three_d_visualization = "3d_visualization"
    memory_drawing = "memory_drawing"
    composition = "composition"


class DrawingTaskSource(str, enum.Enum):
    generated = "generated"
    manual = "manual"
    past_paper = "past_paper"


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    evaluated = "evaluated"
    failed = "failed"


class DrawingTask(Base):
    __tablename__ = "drawing_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[DrawingCategory] = mapped_column(SAEnum(DrawingCategory), nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    skill_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    reference_image_url: Mapped[str | None] = mapped_column(String(500))
    rubric: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # rubric format: {"dimensions": [{"name": "perspective", "weight": 0.25, "description": "..."}]}
    source: Mapped[DrawingTaskSource] = mapped_column(SAEnum(DrawingTaskSource), default=DrawingTaskSource.generated)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    submissions = relationship("DrawingSubmission", back_populates="task")


class DrawingSubmission(Base):
    __tablename__ = "drawing_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("practice_sessions.id"))
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drawing_tasks.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[SubmissionStatus] = mapped_column(SAEnum(SubmissionStatus), default=SubmissionStatus.pending)

    user = relationship("User", back_populates="drawing_submissions")
    task = relationship("DrawingTask", back_populates="submissions")
    session = relationship("PracticeSession", back_populates="drawing_submissions")
    evaluation = relationship("DrawingEvaluation", back_populates="submission", uselist=False)


class DrawingEvaluation(Base):
    __tablename__ = "drawing_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drawing_submissions.id"), unique=True, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    dimension_scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # {"perspective": {"score": 80, "observations": "...", "suggestion": "..."}, ...}
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_suggestions: Mapped[list | None] = mapped_column(JSONB)
    # [{"skill": "perspective", "suggestion": "...", "priority": "high"}]
    raw_model_response: Mapped[dict | None] = mapped_column(JSONB)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    model_version: Mapped[str | None] = mapped_column(String(100))

    submission = relationship("DrawingSubmission", back_populates="evaluation")
