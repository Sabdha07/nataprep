"""
Update & Monitoring Agent
Runs daily to ensure the platform never becomes stale.
Checks health of all data and triggers sub-agents as needed.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func

from app.agents.base_agent import BaseAgent
from app.db.models.concept import Concept
from app.db.models.question import Question, QuestionConcept
from app.db.models.drawing import DrawingTask
from app.db.models.system import SyllabusVersion
from app.agents.question_gen_agent import QuestionGenerationAgent
from app.agents.drawing_task_agent import DrawingTaskAgent
from app.agents.syllabus_agent import SyllabusAgent
import structlog

log = structlog.get_logger()

# Minimum questions per concept before triggering generation
MIN_QUESTIONS_PER_CONCEPT = 15
# Minimum active drawing tasks
MIN_DRAWING_TASKS = 30
# Days before re-checking syllabus
SYLLABUS_CHECK_INTERVAL_DAYS = 7


class UpdateAgent(BaseAgent):
    name = "update_agent"

    async def execute(self, **kwargs) -> dict:
        report = {
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "actions": [],
            "warnings": [],
        }

        # 1. Check syllabus freshness
        await self._check_syllabus(report)

        # 2. Check question bank coverage per concept
        await self._check_question_coverage(report)

        # 3. Check drawing task pool
        await self._check_drawing_tasks(report)

        log.info("update_agent_complete", report=report)
        return report

    async def _check_syllabus(self, report: dict):
        result = await self.db.execute(
            select(SyllabusVersion)
            .where(SyllabusVersion.is_current == True)
            .limit(1)
        )
        current = result.scalar_one_or_none()

        if not current:
            report["actions"].append("No syllabus found — triggering syllabus scrape")
            agent = SyllabusAgent(self.db)
            summary = await agent.run()
            report["actions"].append(f"Syllabus agent: {summary}")
            return

        days_since = (datetime.now(timezone.utc) - current.scraped_at).days
        if days_since >= SYLLABUS_CHECK_INTERVAL_DAYS:
            report["actions"].append(f"Syllabus is {days_since} days old — re-checking")
            agent = SyllabusAgent(self.db)
            summary = await agent.run()
            report["actions"].append(f"Syllabus update: {summary.get('status')}")
        else:
            report["actions"].append(f"Syllabus OK (checked {days_since}d ago)")

    async def _check_question_coverage(self, report: dict):
        concepts_result = await self.db.execute(
            select(Concept).where(Concept.is_active == True)
        )
        concepts = concepts_result.scalars().all()

        low_coverage = []
        for concept in concepts:
            count_result = await self.db.execute(
                select(func.count(Question.id))
                .join(QuestionConcept, Question.id == QuestionConcept.question_id)
                .where(
                    QuestionConcept.concept_id == concept.id,
                    Question.is_active == True,
                )
            )
            count = count_result.scalar() or 0
            if count < MIN_QUESTIONS_PER_CONCEPT:
                low_coverage.append((concept, count))

        if low_coverage:
            report["warnings"].append(
                f"{len(low_coverage)} concepts have < {MIN_QUESTIONS_PER_CONCEPT} questions"
            )
            # Generate questions for the most depleted concept
            most_depleted = sorted(low_coverage, key=lambda x: x[1])[:3]
            for concept, count in most_depleted:
                needed = MIN_QUESTIONS_PER_CONCEPT - count
                gen_agent = QuestionGenerationAgent(self.db)
                summary = await gen_agent.run(
                    concept_id=str(concept.id),
                    count=min(needed, 5),  # cap per run
                    difficulty=concept.difficulty_base,
                )
                report["actions"].append(
                    f"Generated {summary.get('created', 0)} questions for '{concept.name}'"
                )
        else:
            report["actions"].append("Question bank coverage OK")

    async def _check_drawing_tasks(self, report: dict):
        count_result = await self.db.execute(
            select(func.count(DrawingTask.id)).where(DrawingTask.is_active == True)
        )
        count = count_result.scalar() or 0

        if count < MIN_DRAWING_TASKS:
            needed = MIN_DRAWING_TASKS - count
            report["warnings"].append(f"Only {count} drawing tasks — generating {needed} more")
            agent = DrawingTaskAgent(self.db)
            summary = await agent.run(count=needed)
            report["actions"].append(f"Drawing task agent: created {summary.get('created', 0)}")
        else:
            report["actions"].append(f"Drawing tasks OK ({count} available)")
