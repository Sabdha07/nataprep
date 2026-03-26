from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.base import get_db
from app.db.models.user import User
from app.db.models.question import Question, QuestionConcept
from app.db.models.concept import Concept
from app.schemas.question import QuestionOut, QuestionWithAnswerOut, QuestionCreate
from app.api.v1.deps import get_current_user, get_admin_user

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    concept_id: UUID | None = None,
    difficulty_min: float = Query(0.0, ge=0.0, le=1.0),
    difficulty_max: float = Query(1.0, ge=0.0, le=1.0),
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Question).where(Question.is_active == True)

    if concept_id:
        query = (
            query.join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .where(QuestionConcept.concept_id == concept_id)
        )

    query = query.where(
        Question.difficulty.between(difficulty_min, difficulty_max)
    ).offset(offset).limit(limit)

    result = await db.execute(query)
    return [QuestionOut.model_validate(q) for q in result.scalars().all()]


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Question).where(Question.id == question_id, Question.is_active == True))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionOut.model_validate(question)


@router.get("/{question_id}/full", response_model=QuestionWithAnswerOut)
async def get_question_full(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),  # admin only
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionWithAnswerOut.model_validate(question)


@router.post("", response_model=QuestionWithAnswerOut, status_code=201)
async def create_question(
    body: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    from app.db.models.question import QuestionSource, QuestionType
    question = Question(
        text=body.text,
        options=[o.model_dump() for o in body.options],
        correct_option_id=body.correct_option_id,
        explanation=body.explanation,
        difficulty=body.difficulty,
        question_type=body.question_type,
        tags=body.tags,
        image_url=body.image_url,
        time_limit_seconds=body.time_limit_seconds,
        source=QuestionSource.manual,
        is_verified=True,
    )
    db.add(question)
    await db.flush()

    if body.concept_ids:
        for cid in body.concept_ids:
            mapping = QuestionConcept(question_id=question.id, concept_id=cid)
            db.add(mapping)

    await db.commit()
    await db.refresh(question)
    return QuestionWithAnswerOut.model_validate(question)


@router.post("/{question_id}/verify")
async def verify_question(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.is_verified = True
    await db.commit()
    return {"message": "Question verified", "question_id": str(question_id)}
