from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.base import get_db
from app.db.models.user import User
from app.db.models.concept import Concept
from app.db.models.mastery import UserMastery
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.get("")
async def list_concepts(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Concept).where(Concept.is_active == True)
    if category:
        query = query.where(Concept.category == category)
    result = await db.execute(query.order_by(Concept.category, Concept.name))
    concepts = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "category": c.category.value,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "difficulty_base": c.difficulty_base,
            "syllabus_weight": c.syllabus_weight,
        }
        for c in concepts
    ]


@router.get("/{concept_id}/mastery")
async def get_concept_mastery(
    concept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserMastery).where(
            UserMastery.user_id == current_user.id,
            UserMastery.concept_id == concept_id,
        )
    )
    mastery = result.scalar_one_or_none()

    if not mastery:
        return {
            "concept_id": str(concept_id),
            "mastery_score": 0.0,
            "attempt_count": 0,
            "correct_count": 0,
            "streak": 0,
        }

    return {
        "concept_id": str(mastery.concept_id),
        "mastery_score": mastery.mastery_score,
        "attempt_count": mastery.attempt_count,
        "correct_count": mastery.correct_count,
        "streak": mastery.streak,
        "last_attempted_at": mastery.last_attempted_at.isoformat() if mastery.last_attempted_at else None,
        "next_review_at": mastery.next_review_at.isoformat() if mastery.next_review_at else None,
    }
