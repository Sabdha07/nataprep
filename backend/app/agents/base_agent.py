"""
Base agent class. All agents inherit from this.
Provides logging, run tracking, and error handling.
"""
import uuid
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.system import AgentRun, AgentStatus
import structlog

log = structlog.get_logger()


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._run_record: AgentRun | None = None

    async def run(self, **kwargs) -> dict:
        """Execute agent with run tracking."""
        run = AgentRun(agent_name=self.name, status=AgentStatus.running)
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        self._run_record = run

        log.info("agent_started", agent=self.name, run_id=str(run.id))
        try:
            summary = await self.execute(**kwargs)
            run.status = AgentStatus.completed
            run.completed_at = datetime.now(timezone.utc)
            run.summary = summary
            await self.db.commit()
            log.info("agent_completed", agent=self.name, run_id=str(run.id), summary=summary)
            return summary
        except Exception as e:
            run.status = AgentStatus.failed
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = str(e)
            await self.db.commit()
            log.error("agent_failed", agent=self.name, run_id=str(run.id), error=str(e))
            raise

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """Implement agent logic here. Return summary dict."""
        ...
