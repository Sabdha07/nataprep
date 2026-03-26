"""
Celery task definitions — wrappers around agents for async execution.
Each task creates its own DB session (sync wrapper pattern for Celery).
"""
import asyncio
from app.tasks.celery_app import celery_app
from app.db.base import AsyncSessionLocal
import structlog

log = structlog.get_logger()


def _run_sync(coro):
    """Run an async coroutine synchronously in a Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.scheduled_tasks.run_update_agent", bind=True, max_retries=2)
def run_update_agent(self):
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.agents.update_agent import UpdateAgent
            agent = UpdateAgent(db)
            return await agent.run()
    try:
        result = _run_sync(_run())
        log.info("update_agent_task_done", result=result)
        return result
    except Exception as exc:
        log.error("update_agent_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)


@celery_app.task(name="app.tasks.scheduled_tasks.run_syllabus_agent", bind=True, max_retries=2)
def run_syllabus_agent(self):
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.agents.syllabus_agent import SyllabusAgent
            agent = SyllabusAgent(db)
            return await agent.run()
    try:
        return _run_sync(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(name="app.tasks.scheduled_tasks.run_ingestion_agent", bind=True, max_retries=2)
def run_ingestion_agent(self, source: str = "web"):
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.agents.ingestion_agent import QuestionIngestionAgent
            agent = QuestionIngestionAgent(db)
            return await agent.run(source=source)
    try:
        return _run_sync(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=600)


@celery_app.task(
    name="app.tasks.scheduled_tasks.evaluate_drawing_submission",
    bind=True,
    max_retries=3,
    time_limit=120,
)
def evaluate_drawing_submission(self, submission_id: str):
    """Background drawing evaluation — triggered on upload."""
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.agents.drawing_eval_agent import DrawingEvaluationAgent
            agent = DrawingEvaluationAgent(db)
            return await agent.run(submission_id=submission_id)
    try:
        return _run_sync(_run())
    except Exception as exc:
        log.error("drawing_eval_failed", submission_id=submission_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.tasks.scheduled_tasks.generate_questions_for_concept")
def generate_questions_for_concept(concept_id: str, count: int = 5, difficulty: float = 0.5):
    async def _run():
        async with AsyncSessionLocal() as db:
            from app.agents.question_gen_agent import QuestionGenerationAgent
            agent = QuestionGenerationAgent(db)
            return await agent.run(concept_id=concept_id, count=count, difficulty=difficulty)
    return _run_sync(_run())
