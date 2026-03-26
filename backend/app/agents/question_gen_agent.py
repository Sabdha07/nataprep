"""
AI Question Generation Agent
Generates new NATA-quality questions for any concept using Claude.
"""
import json
from uuid import UUID
from sqlalchemy import select
from app.agents.base_agent import BaseAgent
from app.db.models.concept import Concept
from app.db.models.question import Question, QuestionConcept, QuestionSource
from app.core.llm import chat_json
import structlog

log = structlog.get_logger()

GENERATION_SYSTEM_PROMPT = """You are an expert NATA (National Aptitude Test in Architecture) question creator.
You have 15+ years of experience crafting high-quality aptitude questions.

Your questions must:
1. Match the EXACT difficulty and style of real NATA questions
2. Have 4 clearly distinct options (A, B, C, D)
3. Have ONE unambiguously correct answer
4. Include a detailed explanation that teaches the concept
5. Be original — no repetition of common examples
6. For visual/spatial questions, describe the scenario precisely in text

NATA question categories and style:
- Mathematics: precise numerical problems, geometry, algebra
- Visual Reasoning: clear spatial descriptions, mirror images, pattern completions
- Architecture GK: factual questions about architects, buildings, movements
- General Aptitude: logical sequences, analogies

Difficulty scale:
- 0.2-0.4: Basic recall / straightforward application
- 0.4-0.6: Moderate — requires understanding
- 0.6-0.8: Hard — requires analysis and application
- 0.8-1.0: Very hard — requires synthesis, multi-step reasoning
"""


class QuestionGenerationAgent(BaseAgent):
    name = "question_generation_agent"

    async def execute(
        self,
        concept_id: str | None = None,
        count: int = 5,
        difficulty: float = 0.5,
        existing_question_texts: list[str] | None = None,
    ) -> dict:
        concept = None
        if concept_id:
            result = await self.db.execute(select(Concept).where(Concept.id == UUID(concept_id)))
            concept = result.scalar_one_or_none()

        questions_created = []
        for i in range(count):
            try:
                question_data = await self._generate_question(
                    concept=concept,
                    difficulty=difficulty,
                    existing_texts=existing_question_texts or [],
                )
                saved = await self._save_question(question_data, concept)
                questions_created.append(str(saved.id))
            except Exception as e:
                log.warning("question_gen_failed", index=i, error=str(e))

        return {
            "concept_id": concept_id,
            "requested": count,
            "created": len(questions_created),
            "question_ids": questions_created,
        }

    async def _generate_question(
        self,
        concept: Concept | None,
        difficulty: float,
        existing_texts: list[str],
    ) -> dict:
        concept_context = ""
        if concept:
            concept_context = f"""
Target Concept: {concept.name}
Category: {concept.category.value}
Description: {concept.description or 'Standard NATA concept'}
"""

        existing_context = ""
        if existing_texts:
            sample = existing_texts[:5]
            existing_context = f"""
Avoid creating questions similar to these existing ones:
{chr(10).join(f'- {t[:100]}...' for t in sample)}
"""

        difficulty_label = (
            "easy" if difficulty < 0.4
            else "medium" if difficulty < 0.6
            else "hard" if difficulty < 0.8
            else "very hard"
        )

        prompt = f"""Generate 1 NATA aptitude question with difficulty {difficulty:.1f} ({difficulty_label}).

{concept_context}
{existing_context}

Return a JSON object with this EXACT structure:
{{
  "text": "The full question text",
  "options": [
    {{"id": "A", "text": "Option text", "is_correct": false}},
    {{"id": "B", "text": "Option text", "is_correct": true}},
    {{"id": "C", "text": "Option text", "is_correct": false}},
    {{"id": "D", "text": "Option text", "is_correct": false}}
  ],
  "correct_option_id": "B",
  "explanation": "Detailed step-by-step explanation of why B is correct and why others are wrong",
  "difficulty": {difficulty:.2f},
  "question_type": "mcq",
  "tags": ["relevant", "tags"],
  "time_limit_seconds": 90
}}"""

        return await chat_json(
            messages=[{"role": "user", "content": prompt}],
            system=GENERATION_SYSTEM_PROMPT,
            temperature=0.8,
        )

    async def _save_question(self, data: dict, concept: Concept | None) -> Question:
        question = Question(
            text=data["text"],
            options=data["options"],
            correct_option_id=data["correct_option_id"],
            explanation=data["explanation"],
            difficulty=data["difficulty"],
            question_type=data.get("question_type", "mcq"),
            tags=data.get("tags", []),
            time_limit_seconds=data.get("time_limit_seconds", 90),
            source=QuestionSource.generated,
            is_verified=False,
        )
        self.db.add(question)
        await self.db.flush()

        if concept:
            mapping = QuestionConcept(
                question_id=question.id,
                concept_id=concept.id,
                relevance_score=1.0,
            )
            self.db.add(mapping)

        await self.db.commit()
        await self.db.refresh(question)
        return question
