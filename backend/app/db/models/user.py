import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    target_year: Mapped[int] = mapped_column(Integer, default=2026)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    mastery_scores = relationship("UserMastery", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("PracticeSession", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("QuestionAttempt", back_populates="user")
    drawing_submissions = relationship("DrawingSubmission", back_populates="user")
    mistakes = relationship("MistakeLog", back_populates="user")
