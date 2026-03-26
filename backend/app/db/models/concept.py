import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ConceptCategory(str, enum.Enum):
    mathematics = "mathematics"
    physics = "physics"
    general_aptitude = "general_aptitude"
    architecture_gk = "architecture_gk"
    visual_reasoning = "visual_reasoning"


class SkillCategory(str, enum.Enum):
    perspective = "perspective"
    composition = "composition"
    creativity = "creativity"
    proportion = "proportion"
    shading = "shading"
    observation = "observation"


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"))
    category: Mapped[ConceptCategory] = mapped_column(SAEnum(ConceptCategory), nullable=False)
    syllabus_weight: Mapped[float] = mapped_column(Float, default=1.0)
    difficulty_base: Mapped[float] = mapped_column(Float, default=0.5)
    embedding_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Self-referential
    parent = relationship("Concept", remote_side="Concept.id", back_populates="children")
    children = relationship("Concept", back_populates="parent")

    # Relationships
    question_mappings = relationship("QuestionConcept", back_populates="concept")
    mastery_scores = relationship("UserMastery", back_populates="concept")

    # Dependencies where this concept is a prerequisite
    as_prerequisite = relationship(
        "ConceptDependency",
        foreign_keys="ConceptDependency.prerequisite_id",
        back_populates="prerequisite",
    )
    # Dependencies where this concept depends on something
    as_dependent = relationship(
        "ConceptDependency",
        foreign_keys="ConceptDependency.dependent_id",
        back_populates="dependent",
    )


class ConceptDependency(Base):
    __tablename__ = "concept_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    dependent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=1.0)

    prerequisite = relationship("Concept", foreign_keys=[prerequisite_id], back_populates="as_prerequisite")
    dependent = relationship("Concept", foreign_keys=[dependent_id], back_populates="as_dependent")


class DrawingSkill(Base):
    __tablename__ = "drawing_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[SkillCategory] = mapped_column(SAEnum(SkillCategory), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("drawing_skills.id"))
    difficulty_base: Mapped[float] = mapped_column(Float, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent = relationship("DrawingSkill", remote_side="DrawingSkill.id", back_populates="children")
    children = relationship("DrawingSkill", back_populates="parent")
    mastery_scores = relationship("UserMastery", back_populates="skill")
