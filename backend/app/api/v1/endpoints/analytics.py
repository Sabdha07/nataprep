from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.db.models.user import User
from app.agents.analytics_agent import AnalyticsAgent
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db)
    return await agent.generate_dashboard(current_user.id)


@router.get("/weak-areas")
async def get_weak_areas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db)
    dashboard = await agent.generate_dashboard(current_user.id)
    return {
        "weak_areas": dashboard["weak_areas"],
        "recommended_priority": dashboard["weak_areas"][:3] if dashboard["weak_areas"] else [],
    }


@router.get("/predictions")
async def get_predictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db)
    dashboard = await agent.generate_dashboard(current_user.id)
    return dashboard["predicted_score"]


@router.get("/progress")
async def get_progress(
    days: int = 14,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db)
    progress = await agent._get_progress_trend(current_user.id, days=days)
    return {"progress": progress, "period_days": days}
