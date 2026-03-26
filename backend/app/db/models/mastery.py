import uuid
from datetime import datetime, timezone
from sqlalchemy import Float, Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class UserMastery(Base):
    __tablename__ = "user_mastery"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_mastery_user_concept"),
        UniqueConstraint("user_id", "skill_id", name="uq_mastery_user_skill"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    skill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("drawing_skills.id"))

    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    streak: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="mastery_scores")
    concept = relationship("Concept", back_populates="mastery_scores")
    skill = relationship("DrawingSkill", back_populates="mastery_scores")
