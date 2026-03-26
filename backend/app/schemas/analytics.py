from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ConceptMasteryOut(BaseModel):
    concept_id: UUID
    concept_name: str
    category: str
    mastery_score: float
    attempt_count: int
    accuracy: float
    next_review_at: datetime | None


class WeakAreaOut(BaseModel):
    concept_id: UUID
    concept_name: str
    category: str
    mastery_score: float
    accuracy: float
    recommended_action: str
    priority: str  # high | medium | low


class ProgressPoint(BaseModel):
    date: str
    accuracy: float
    questions_attempted: int
    avg_difficulty: float


class PredictedScore(BaseModel):
    aptitude_score: float   # out of 120
    drawing_score: float    # out of 80 (estimated)
    total_score: float
    confidence: str         # low | medium | high
    breakdown: dict         # category-wise


class DashboardOut(BaseModel):
    user_id: UUID
    overall_mastery: float
    total_questions_attempted: int
    total_correct: int
    overall_accuracy: float
    study_streak_days: int
    weak_areas: list[WeakAreaOut]
    strong_areas: list[ConceptMasteryOut]
    recent_progress: list[ProgressPoint]
    predicted_score: PredictedScore
    insights: list[str]  # AI-generated natural language insights
    last_updated: datetime
