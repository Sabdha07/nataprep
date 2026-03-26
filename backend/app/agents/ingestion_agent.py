"""
Question Ingestion Agent
Scrapes previous year NATA papers, question banks, and architecture GK sources.
Cleans, tags, deduplicates, and stores questions.
"""
from sqlalchemy import select
import httpx
from bs4 import BeautifulSoup

from app.agents.base_agent import BaseAgent
from app.db.models.question import Question, QuestionConcept, QuestionSource
from app.db.models.concept import Concept
from app.core.llm import chat_json
import structlog

log = structlog.get_logger()

TAG_SYSTEM = """You are an expert NATA exam question analyst.
Given a raw question, output a structured JSON with:
{
  "text": "Clean question text (fix formatting)",
  "options": [
    {"id": "A", "text": "Option text", "is_correct": false},
    {"id": "B", "text": "Option text", "is_correct": true},
    {"id": "C", "text": "Option text", "is_correct": false},
    {"id": "D", "text": "Option text", "is_correct": false}
  ],
  "correct_option_id": "B",
  "explanation": "Clear explanation of why the answer is correct",
  "difficulty": 0.5,
  "question_type": "mcq",
  "category": "mathematics|physics|general_aptitude|architecture_gk|visual_reasoning",
  "tags": ["tag1", "tag2"],
  "time_limit_seconds": 90
}
Difficulty: 0.2=easy, 0.5=medium, 0.8=hard.
If you cannot reliably determine the correct answer, set "quality": "low".
"""

# Sample sources (expand with real sources in production)
SAMPLE_QUESTIONS_RAW = [
    {
        "raw": """Q: What is the angle sum of all interior angles of a hexagon?
A) 540°  B) 720°  C) 900°  D) 360°  Answer: B""",
        "source_ref": "NATA Sample Paper",
    },
    {
        "raw": """Q: The famous Indian architect who designed the Vidhan Bhavan in Bhopal is:
A) Charles Correa  B) Laurie Baker  C) B.V. Doshi  D) Raj Rewal  Answer: A""",
        "source_ref": "Architecture GK Bank",
    },
    {
        "raw": """Q: In a series: 2, 6, 12, 20, 30, ?, what is the next number?
A) 40  B) 42  C) 44  D) 45  Answer: B""",
        "source_ref": "Aptitude Question Bank",
    },
    {
        "raw": """Q: Which of the following is NOT a sustainable building certification?
A) LEED  B) GRIHA  C) BREEAM  D) HVAC  Answer: D""",
        "source_ref": "Architecture GK Bank",
    },
    {
        "raw": """Q: The mirror image of the letter 'b' is:
A) d  B) q  C) p  D) b  Answer: A""",
        "source_ref": "Visual Reasoning Bank",
    },
]


class QuestionIngestionAgent(BaseAgent):
    name = "question_ingestion_agent"

    async def execute(self, source: str = "sample", **kwargs) -> dict:
        """
        source: "sample" | "web" | "file:<path>"
        """
        if source == "sample":
            raw_questions = SAMPLE_QUESTIONS_RAW
        elif source == "web":
            raw_questions = await self._scrape_web_sources()
        else:
            raw_questions = SAMPLE_QUESTIONS_RAW  # fallback

        ingested = 0
        skipped = 0
        failed = 0

        for raw_q in raw_questions:
            try:
                structured = await self._tag_and_structure(raw_q["raw"])
                if not structured or structured.get("quality") == "low":
                    skipped += 1
                    continue

                is_dup = await self._is_duplicate(structured["text"])
                if is_dup:
                    skipped += 1
                    continue

                await self._save_question(structured, raw_q.get("source_ref"))
                ingested += 1
            except Exception as e:
                log.warning("ingestion_item_failed", error=str(e))
                failed += 1

        return {
            "source": source,
            "processed": len(raw_questions),
            "ingested": ingested,
            "skipped_duplicates_or_low_quality": skipped,
            "failed": failed,
        }

    async def _scrape_web_sources(self) -> list[dict]:
        """Scrape open question banks. Extend with real URLs in production."""
        results = []
        # Placeholder — in production add real scraping targets
        return results

    async def _tag_and_structure(self, raw_text: str) -> dict | None:
        return await chat_json(
            messages=[{"role": "user", "content": f"Structure this NATA question:\n\n{raw_text}"}],
            system=TAG_SYSTEM,
            temperature=0.2,
        )

    async def _is_duplicate(self, text: str) -> bool:
        """
        Simple text-based duplicate check.
        In Phase 2 this will use Qdrant vector similarity.
        """
        # Normalize and check first 100 chars
        normalized = text.lower().strip()[:100]
        result = await self.db.execute(
            select(Question).where(
                Question.text.ilike(f"%{normalized[:50]}%"),
                Question.is_active == True,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _save_question(self, data: dict, source_ref: str | None) -> Question:
        question = Question(
            text=data["text"],
            options=data["options"],
            correct_option_id=data["correct_option_id"],
            explanation=data.get("explanation", ""),
            difficulty=data.get("difficulty", 0.5),
            question_type=data.get("question_type", "mcq"),
            tags=data.get("tags", []),
            time_limit_seconds=data.get("time_limit_seconds", 90),
            source=QuestionSource.scraped,
            source_ref=source_ref,
            is_verified=False,
        )
        self.db.add(question)
        await self.db.flush()

        # Auto-link to concept
        category = data.get("category")
        if category:
            cat_result = await self.db.execute(
                select(Concept).where(
                    Concept.category == category,
                    Concept.parent_id.is_(None),  # top-level concept
                    Concept.is_active == True,
                ).limit(1)
            )
            concept = cat_result.scalar_one_or_none()
            if concept:
                mapping = QuestionConcept(
                    question_id=question.id,
                    concept_id=concept.id,
                    relevance_score=0.8,
                )
                self.db.add(mapping)

        await self.db.commit()
        return question
