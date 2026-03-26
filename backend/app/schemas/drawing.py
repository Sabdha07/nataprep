from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DrawingRubricDimension(BaseModel):
    name: str
    weight: float
    description: str


class DrawingTaskOut(BaseModel):
    id: UUID
    prompt: str
    category: str
    difficulty: float
    rubric: dict
    reference_image_url: str | None

    model_config = {"from_attributes": True}


class DrawingSubmissionCreate(BaseModel):
    task_id: UUID
    session_id: UUID | None = None
    time_taken_seconds: int | None = None


class DrawingDimensionScore(BaseModel):
    score: float
    observations: str
    suggestion: str


class DrawingEvaluationOut(BaseModel):
    id: UUID
    submission_id: UUID
    total_score: float
    dimension_scores: dict[str, DrawingDimensionScore]
    feedback: str
    improvement_suggestions: list[dict] | None
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class DrawingSubmissionOut(BaseModel):
    id: UUID
    task_id: UUID
    image_url: str
    submitted_at: datetime
    status: str
    time_taken_seconds: int | None
    evaluation: DrawingEvaluationOut | None

    model_config = {"from_attributes": True}
