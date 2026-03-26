from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any


class SessionCreate(BaseModel):
    mode: str  # concept | adaptive | mock_test | mixed | review
    config: dict | None = None
    # config examples:
    #   concept mode: {"concept_ids": ["uuid1", "uuid2"], "difficulty_range": [0.3, 0.7]}
    #   mock_test: {"question_count": 100, "time_limit_minutes": 90}
    #   adaptive: {"max_questions": 50}


class SessionOut(BaseModel):
    id: UUID
    user_id: UUID
    mode: str
    started_at: datetime
    ended_at: datetime | None
    total_questions: int
    correct_count: int
    score: float
    status: str
    config: dict | None

    model_config = {"from_attributes": True}


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_option_id: str
    time_taken_seconds: int
    confidence_level: int | None = None


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_option_id: str
    explanation: str
    mastery_update: dict | None  # {"concept_id": uuid, "old_mastery": 0.4, "new_mastery": 0.5}
    next_question_id: UUID | None  # pre-fetched for speed


class AttemptOut(BaseModel):
    id: UUID
    question_id: UUID
    selected_option_id: str | None
    is_correct: bool | None
    time_taken_seconds: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
