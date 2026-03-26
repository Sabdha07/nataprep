from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any


class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool | None = None  # hidden from student


class QuestionOut(BaseModel):
    id: UUID
    text: str
    options: list[dict]  # options without is_correct exposed
    image_url: str | None
    difficulty: float
    question_type: str
    time_limit_seconds: int
    tags: list[str] | None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        # Strip is_correct from options before sending to students
        if self.options:
            self.options = [
                {"id": o["id"], "text": o["text"]}
                for o in self.options
            ]


class QuestionWithAnswerOut(QuestionOut):
    """Full question including answer — for admin and post-session review."""
    correct_option_id: str
    explanation: str
    source: str
    is_verified: bool


class QuestionCreate(BaseModel):
    text: str
    options: list[QuestionOption]
    correct_option_id: str
    explanation: str
    difficulty: float
    question_type: str = "mcq"
    tags: list[str] | None = None
    image_url: str | None = None
    time_limit_seconds: int = 90
    concept_ids: list[UUID] | None = None


class AnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_id: str
    time_taken_seconds: int
    confidence_level: int | None = None  # 1-5
