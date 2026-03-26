import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.db.base import get_db
from app.db.models.user import User
from app.db.models.drawing import DrawingTask, DrawingSubmission, DrawingEvaluation, SubmissionStatus
from app.agents.drawing_eval_agent import DrawingEvaluationAgent
from app.agents.adaptive_agent import AdaptiveAgent
from app.schemas.drawing import DrawingTaskOut, DrawingSubmissionOut, DrawingEvaluationOut
from app.api.v1.deps import get_current_user
from app.core.config import settings
import aiofiles

router = APIRouter(prefix="/drawing", tags=["drawing"])


@router.get("/tasks", response_model=list[DrawingTaskOut])
async def list_tasks(
    category: str | None = None,
    difficulty_min: float = 0.0,
    difficulty_max: float = 1.0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(DrawingTask).where(
        DrawingTask.is_active == True,
        DrawingTask.difficulty.between(difficulty_min, difficulty_max),
    )
    if category:
        query = query.where(DrawingTask.category == category)
    result = await db.execute(query.limit(limit))
    return [DrawingTaskOut.model_validate(t) for t in result.scalars().all()]


@router.get("/tasks/next", response_model=DrawingTaskOut)
async def get_next_task(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get adaptive next drawing task (least practiced skill area)."""
    # Simple: get task not recently submitted
    recent_result = await db.execute(
        select(DrawingSubmission.task_id)
        .where(DrawingSubmission.user_id == current_user.id)
        .order_by(DrawingSubmission.submitted_at.desc())
        .limit(10)
    )
    recent_ids = [r[0] for r in recent_result.all()]

    query = select(DrawingTask).where(DrawingTask.is_active == True)
    if recent_ids:
        query = query.where(DrawingTask.id.notin_(recent_ids))

    result = await db.execute(query.order_by(DrawingTask.difficulty).limit(1))
    task = result.scalar_one_or_none()

    if not task:
        # Fallback to any task
        result = await db.execute(select(DrawingTask).where(DrawingTask.is_active == True).limit(1))
        task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="No drawing tasks available")

    return DrawingTaskOut.model_validate(task)


@router.post("/submit", response_model=DrawingSubmissionOut)
async def submit_drawing(
    task_id: UUID = Form(...),
    session_id: UUID | None = Form(None),
    time_taken_seconds: int | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WebP images accepted")

    # Validate file size
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create submission
    submission = DrawingSubmission(
        user_id=current_user.id,
        task_id=task_id,
        session_id=session_id,
        image_url=file_path,
        time_taken_seconds=time_taken_seconds,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Trigger evaluation (synchronous for now; use Celery in production)
    try:
        agent = DrawingEvaluationAgent(db)
        await agent.run(submission_id=str(submission.id))
    except Exception as e:
        # Don't fail submission if evaluation fails
        submission.status = SubmissionStatus.failed
        await db.commit()

    # Re-query with evaluation relationship loaded (async SQLAlchemy can't lazy-load)
    final_result = await db.execute(
        select(DrawingSubmission)
        .options(selectinload(DrawingSubmission.evaluation))
        .where(DrawingSubmission.id == submission.id)
    )
    return DrawingSubmissionOut.model_validate(final_result.scalar_one())


@router.get("/submissions", response_model=list[DrawingSubmissionOut])
async def list_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    result = await db.execute(
        select(DrawingSubmission)
        .where(DrawingSubmission.user_id == current_user.id)
        .order_by(DrawingSubmission.submitted_at.desc())
        .limit(limit)
    )
    return [DrawingSubmissionOut.model_validate(s) for s in result.scalars().all()]


@router.get("/submissions/{submission_id}/evaluation", response_model=DrawingEvaluationOut)
async def get_evaluation(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_result = await db.execute(
        select(DrawingSubmission).where(
            DrawingSubmission.id == submission_id,
            DrawingSubmission.user_id == current_user.id,
        )
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    eval_result = await db.execute(
        select(DrawingEvaluation).where(DrawingEvaluation.submission_id == submission_id)
    )
    evaluation = eval_result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not ready yet")

    return DrawingEvaluationOut.model_validate(evaluation)
