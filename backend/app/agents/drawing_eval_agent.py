"""
Drawing Evaluation Agent
Uses Claude Vision to evaluate student drawing submissions like a NATA examiner.
"""
from uuid import UUID
from sqlalchemy import select
from app.agents.base_agent import BaseAgent
from app.db.models.drawing import DrawingSubmission, DrawingEvaluation, DrawingTask, SubmissionStatus
from app.core.llm import vision_chat_json
from app.core.config import settings
import structlog

log = structlog.get_logger()

EVALUATOR_SYSTEM = """You are a senior NATA (National Aptitude Test in Architecture) drawing examiner with 15 years of experience.
You evaluate student architectural drawings with precision, fairness, and constructive insight.

Your evaluations must be:
- SPECIFIC: Reference exact elements in the drawing
- EDUCATIONAL: Each suggestion must be actionable
- CALIBRATED: Use the full scoring range (not just 50-80)
- HONEST: Poor work should score low; excellent work should score high

You understand that NATA drawing tests:
- Perspective accuracy and spatial understanding
- Compositional skills and visual balance
- Creative interpretation of the prompt
- Proportion and scale relationships
- Line quality and execution technique
"""


def _build_eval_prompt(task_prompt: str, rubric: dict) -> str:
    dimensions = rubric.get("dimensions", [
        {"name": "perspective", "weight": 0.25, "description": "Correct vanishing points, spatial depth, 3D representation"},
        {"name": "proportion", "weight": 0.20, "description": "Relative scale and realistic measurements of elements"},
        {"name": "composition", "weight": 0.25, "description": "Layout, balance, focal point, framing"},
        {"name": "creativity", "weight": 0.15, "description": "Originality, expressiveness, unique interpretation"},
        {"name": "execution", "weight": 0.15, "description": "Line quality, shading, neatness, technique"},
    ])

    dims_text = "\n".join(
        f'  - "{d["name"]}" (weight {d["weight"]:.0%}): {d["description"]}'
        for d in dimensions
    )

    dim_names = [d["name"] for d in dimensions]
    example_obj = {
        name: {
            "score": 75,
            "observations": "Specific observations about this dimension",
            "suggestion": "One concrete improvement action"
        }
        for name in dim_names
    }

    return f"""Evaluate this architectural drawing submission for the NATA prompt:
"{task_prompt}"

Score each dimension from 0 to 100:
{dims_text}

Respond with this EXACT JSON structure:
{{
  "dimension_scores": {example_obj},
  "total_score": 75.0,
  "feedback": "2-3 sentence overall assessment of the drawing",
  "improvement_suggestions": [
    {{"skill": "perspective", "suggestion": "Specific actionable improvement", "priority": "high"}},
    {{"skill": "composition", "suggestion": "Specific actionable improvement", "priority": "medium"}}
  ],
  "strength_summary": "What the student did well",
  "weakness_summary": "Primary areas needing work"
}}

total_score = weighted average of dimension scores using the weights above."""


class DrawingEvaluationAgent(BaseAgent):
    name = "drawing_evaluation_agent"

    async def execute(self, submission_id: str, **kwargs) -> dict:
        result = await self.db.execute(
            select(DrawingSubmission).where(DrawingSubmission.id == UUID(submission_id))
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        task_result = await self.db.execute(
            select(DrawingTask).where(DrawingTask.id == submission.task_id)
        )
        task = task_result.scalar_one()

        evaluation_data = await self._evaluate_drawing(
            image_url=submission.image_url,
            task_prompt=task.prompt,
            rubric=task.rubric,
        )

        evaluation = await self._save_evaluation(submission, evaluation_data)

        # Update submission status
        submission.status = SubmissionStatus.evaluated
        await self.db.commit()

        return {
            "submission_id": submission_id,
            "evaluation_id": str(evaluation.id),
            "total_score": evaluation.total_score,
        }

    async def _evaluate_drawing(
        self,
        image_url: str,
        task_prompt: str,
        rubric: dict,
    ) -> dict:
        prompt = _build_eval_prompt(task_prompt, rubric)

        # Determine image source type
        is_local = image_url.startswith("/") or image_url.startswith("./") or "localhost" in image_url

        if is_local:
            # Local upload path
            data = await vision_chat_json(
                prompt=prompt,
                system=EVALUATOR_SYSTEM,
                image_path=image_url,
                media_type="image/jpeg",
            )
        else:
            data = await vision_chat_json(
                prompt=prompt,
                system=EVALUATOR_SYSTEM,
                image_url=image_url,
            )

        return data

    async def _save_evaluation(
        self,
        submission: DrawingSubmission,
        data: dict,
    ) -> DrawingEvaluation:
        evaluation = DrawingEvaluation(
            submission_id=submission.id,
            total_score=data["total_score"],
            dimension_scores=data["dimension_scores"],
            feedback=data["feedback"],
            improvement_suggestions=data.get("improvement_suggestions", []),
            raw_model_response=data,
            model_version=settings.LLM_MODEL,
        )
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation
