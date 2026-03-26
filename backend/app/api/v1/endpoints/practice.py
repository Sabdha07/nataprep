from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone
from app.db.base import get_db
from app.db.models.user import User
from app.db.models.question import Question
from app.db.models.attempt import PracticeSession, QuestionAttempt, MistakeLog, SessionStatus, ErrorType
from app.agents.adaptive_agent import AdaptiveAgent
from app.schemas.practice import SessionCreate, SessionOut, SubmitAnswerRequest, SubmitAnswerResponse
from app.schemas.question import QuestionOut
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/sessions", response_model=SessionOut)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = PracticeSession(
        user_id=current_user.id,
        mode=body.mode,
        config=body.config,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionOut.model_validate(session)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.user_id == current_user.id)
        .order_by(PracticeSession.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [SessionOut.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut.model_validate(session)


@router.get("/next-question", response_model=QuestionOut)
async def get_next_question(
    session_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the next adaptive question for the user."""
    config = None
    exclude_ids = []

    if session_id:
        sess_result = await db.execute(
            select(PracticeSession).where(
                PracticeSession.id == session_id,
                PracticeSession.user_id == current_user.id,
            )
        )
        session = sess_result.scalar_one_or_none()
        if session:
            config = session.config
            # Exclude already attempted in this session
            attempts_result = await db.execute(
                select(QuestionAttempt.question_id).where(
                    QuestionAttempt.session_id == session_id
                )
            )
            exclude_ids = [r[0] for r in attempts_result.all()]

    agent = AdaptiveAgent(db)
    question = await agent.get_next_question(
        user_id=current_user.id,
        session_config=config,
        exclude_question_ids=exclude_ids,
    )

    if not question:
        raise HTTPException(status_code=404, detail="No questions available. Generate more questions first.")

    return QuestionOut.model_validate(question)


@router.post("/sessions/{session_id}/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: UUID,
    body: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate session
    sess_result = await db.execute(
        select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == current_user.id,
            PracticeSession.status == SessionStatus.active,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Get question
    q_result = await db.execute(
        select(Question).where(Question.id == body.question_id)
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = body.selected_option_id == question.correct_option_id

    # Record attempt
    attempt = QuestionAttempt(
        user_id=current_user.id,
        session_id=session_id,
        question_id=body.question_id,
        selected_option_id=body.selected_option_id,
        is_correct=is_correct,
        time_taken_seconds=body.time_taken_seconds,
        confidence_level=body.confidence_level,
    )
    db.add(attempt)
    await db.flush()

    # Log mistake
    if not is_correct:
        from app.db.models.question import QuestionConcept
        concepts_result = await db.execute(
            select(QuestionConcept.concept_id).where(
                QuestionConcept.question_id == body.question_id
            )
        )
        concept_ids = [r[0] for r in concepts_result.all()]
        mistake = MistakeLog(
            user_id=current_user.id,
            question_id=body.question_id,
            attempt_id=attempt.id,
            error_type=ErrorType.unknown,
            concept_ids=concept_ids,
        )
        db.add(mistake)

    # Update session stats
    session.total_questions += 1
    if is_correct:
        session.correct_count += 1
    session.score = session.correct_count / session.total_questions if session.total_questions > 0 else 0.0

    # Update mastery via adaptive agent
    agent = AdaptiveAgent(db)
    mastery_result = await agent.process_answer(
        user_id=current_user.id,
        question_id=body.question_id,
        is_correct=is_correct,
        time_taken_seconds=body.time_taken_seconds,
    )

    await db.commit()

    # Pre-fetch next question hint
    next_q = await agent.get_next_question(
        user_id=current_user.id,
        session_config=session.config,
        exclude_question_ids=[body.question_id],
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_option_id=question.correct_option_id,
        explanation=question.explanation,
        mastery_update=mastery_result.get("mastery_updates", [{}])[0] if mastery_result else None,
        next_question_id=next_q.id if next_q else None,
    )


@router.post("/sessions/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess_result = await db.execute(
        select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == current_user.id,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SessionStatus.completed
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return SessionOut.model_validate(session)
