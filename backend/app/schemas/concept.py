from pydantic import BaseModel
from uuid import UUID


class ConceptOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    category: str
    parent_id: UUID | None
    difficulty_base: float
    syllabus_weight: float

    model_config = {"from_attributes": True}
