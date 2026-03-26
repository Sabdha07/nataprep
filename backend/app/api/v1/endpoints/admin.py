from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.base import get_db
from app.db.models.user import User
from app.db.models.question import Question
from app.db.models.drawing import DrawingTask
from app.db.models.system import AgentRun
from app.db.models.attempt import QuestionAttempt
from app.agents.question_gen_agent import QuestionGenerationAgent
from app.agents.drawing_task_agent import DrawingTaskAgent
from app.api.v1.deps import get_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    q_count = await db.execute(select(func.count(Question.id)).where(Question.is_active == True))
    dt_count = await db.execute(select(func.count(DrawingTask.id)).where(DrawingTask.is_active == True))
    u_count = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    a_count = await db.execute(select(func.count(QuestionAttempt.id)))

    return {
        "questions": q_count.scalar(),
        "drawing_tasks": dt_count.scalar(),
        "users": u_count.scalar(),
        "total_attempts": a_count.scalar(),
    }


@router.post("/agents/generate-questions")
async def trigger_question_generation(
    concept_id: str | None = None,
    count: int = 10,
    difficulty: float = 0.5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    agent = QuestionGenerationAgent(db)
    result = await agent.run(concept_id=concept_id, count=count, difficulty=difficulty)
    return result


@router.post("/agents/generate-drawing-tasks")
async def trigger_drawing_task_generation(
    count: int = 10,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    agent = DrawingTaskAgent(db)
    result = await agent.run(count=count, category=category)
    return result


@router.get("/agents/runs")
async def get_agent_runs(
    limit: int = 50,
    agent_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
    if agent_name:
        query = query.where(AgentRun.agent_name == agent_name)
    result = await db.execute(query)
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "agent_name": r.agent_name,
            "status": r.status.value,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "summary": r.summary,
            "error_message": r.error_message,
        }
        for r in runs
    ]
