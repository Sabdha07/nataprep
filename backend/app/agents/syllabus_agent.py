"""
Syllabus Agent
Scrapes the official NATA syllabus, detects changes, and normalises
into a structured concept graph stored in the DB.
Runs periodically (weekly) via Celery Beat.
"""
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy import select
import httpx
from bs4 import BeautifulSoup

from app.agents.base_agent import BaseAgent
from app.db.models.concept import Concept, ConceptCategory
from app.db.models.system import SyllabusVersion
from app.core.llm import chat_json
import structlog

log = structlog.get_logger()

# Official NATA / COA sources to check
SYLLABUS_SOURCES = [
    "https://www.nata.in/",
    "https://www.nata.in/syllabus",
]

PARSE_SYSTEM = """You are an expert NATA exam analyst.
Given raw text scraped from the NATA official website, extract the structured syllabus.
Return a JSON object with this exact structure:
{
  "sections": [
    {
      "name": "Section name",
      "category": "mathematics|physics|general_aptitude|architecture_gk|visual_reasoning",
      "topics": [
        {"name": "Topic name", "description": "Brief description", "weight": 1.0}
      ]
    }
  ],
  "exam_pattern": {
    "total_marks": 120,
    "duration_minutes": 90,
    "question_types": ["mcq", "msq", "numerical"]
  }
}
If the page does not contain syllabus info, return {"sections": [], "exam_pattern": {}}."""


class SyllabusAgent(BaseAgent):
    name = "syllabus_agent"

    async def execute(self, force_update: bool = False, **kwargs) -> dict:
        raw_text = await self._scrape_syllabus()
        if not raw_text:
            return {"status": "scrape_failed", "concepts_updated": 0}

        content_hash = hashlib.sha256(raw_text.encode()).hexdigest()

        # Check if already processed this version
        existing = await self.db.execute(
            select(SyllabusVersion).where(SyllabusVersion.version_hash == content_hash)
        )
        if existing.scalar_one_or_none() and not force_update:
            log.info("syllabus_unchanged", hash=content_hash[:8])
            return {"status": "unchanged", "hash": content_hash[:8], "concepts_updated": 0}

        # Parse with LLM
        syllabus_data = await self._parse_syllabus(raw_text)
        if not syllabus_data.get("sections"):
            return {"status": "parse_failed", "concepts_updated": 0}

        # Compute diff from current version
        current = await self.db.execute(
            select(SyllabusVersion).where(SyllabusVersion.is_current == True).limit(1)
        )
        current_version = current.scalar_one_or_none()
        diff = self._compute_diff(
            current_version.content if current_version else {},
            syllabus_data,
        )

        # Store new version
        if current_version:
            current_version.is_current = False

        new_version = SyllabusVersion(
            version_hash=content_hash,
            content=syllabus_data,
            diff=diff,
            is_current=True,
        )
        self.db.add(new_version)
        await self.db.flush()

        # Upsert concepts into DB
        concepts_updated = await self._sync_concepts(syllabus_data)
        await self.db.commit()

        return {
            "status": "updated",
            "hash": content_hash[:8],
            "sections_found": len(syllabus_data.get("sections", [])),
            "concepts_updated": concepts_updated,
            "diff_summary": diff.get("summary", ""),
        }

    async def _scrape_syllabus(self) -> str | None:
        """Fetch syllabus text from NATA sources."""
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for url in SYLLABUS_SOURCES:
                try:
                    resp = await client.get(url, headers={"User-Agent": "NATAPrep-Bot/1.0"})
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        # Remove script/style
                        for tag in soup(["script", "style", "nav", "footer"]):
                            tag.decompose()
                        text = soup.get_text(separator="\n", strip=True)
                        if len(text) > 500:
                            log.info("syllabus_scraped", url=url, chars=len(text))
                            return text[:12000]  # cap context length
                except Exception as e:
                    log.warning("scrape_failed", url=url, error=str(e))

        # Fallback: use embedded baseline syllabus
        return self._get_baseline_syllabus()

    def _get_baseline_syllabus(self) -> str:
        """Hardcoded NATA 2026 syllabus baseline (always available)."""
        return """
NATA 2026 Syllabus

PART A - APTITUDE (120 marks)
1. Mathematics
   - Algebra: Linear equations, quadratic equations, polynomials, matrices
   - Geometry: 2D and 3D geometry, mensuration, coordinate geometry
   - Trigonometry: ratios, identities, heights and distances
   - Statistics & Probability: mean, median, mode, permutation, combination

2. General Aptitude
   - Visual Reasoning: pattern recognition, mirror images, 3D visualization
   - Logical Reasoning: analogies, series, syllogisms
   - Spatial Reasoning: mental rotation, paper folding

3. Architecture General Knowledge
   - Famous architects: Indian and international
   - Architectural styles and movements
   - Vernacular and regional architecture of India
   - Green and sustainable design
   - Building materials and construction

4. Physics (Applied)
   - Optics and light
   - Forces and structural concepts
   - Basic thermodynamics

PART B - DRAWING TEST
   - Perspective drawing (1-point, 2-point)
   - Composition and layout
   - Memory and imagination drawing
   - 3D visualization
   - Observation drawing
"""

    async def _parse_syllabus(self, raw_text: str) -> dict:
        return await chat_json(
            messages=[{
                "role": "user",
                "content": f"Parse this NATA syllabus text into structured JSON:\n\n{raw_text[:8000]}"
            }],
            system=PARSE_SYSTEM,
            temperature=0.1,
        )

    def _compute_diff(self, old: dict, new: dict) -> dict:
        """Simple diff — detect added/removed topics."""
        old_topics = set()
        new_topics = set()

        for section in old.get("sections", []):
            for topic in section.get("topics", []):
                old_topics.add(topic["name"])

        for section in new.get("sections", []):
            for topic in section.get("topics", []):
                new_topics.add(topic["name"])

        added = list(new_topics - old_topics)
        removed = list(old_topics - new_topics)

        return {
            "added_topics": added,
            "removed_topics": removed,
            "summary": f"+{len(added)} topics, -{len(removed)} topics" if (added or removed) else "No changes",
        }

    async def _sync_concepts(self, syllabus: dict) -> int:
        """Upsert concepts from parsed syllabus."""
        cat_map = {
            "mathematics": ConceptCategory.mathematics,
            "physics": ConceptCategory.physics,
            "general_aptitude": ConceptCategory.general_aptitude,
            "architecture_gk": ConceptCategory.architecture_gk,
            "visual_reasoning": ConceptCategory.visual_reasoning,
        }

        count = 0
        for section in syllabus.get("sections", []):
            cat = cat_map.get(section.get("category", "general_aptitude"), ConceptCategory.general_aptitude)

            for topic in section.get("topics", []):
                # Check existence by name + category
                existing = await self.db.execute(
                    select(Concept).where(
                        Concept.name == topic["name"],
                        Concept.category == cat,
                    )
                )
                concept = existing.scalar_one_or_none()

                if concept:
                    concept.description = topic.get("description", concept.description)
                    concept.syllabus_weight = topic.get("weight", concept.syllabus_weight)
                else:
                    concept = Concept(
                        name=topic["name"],
                        category=cat,
                        description=topic.get("description"),
                        syllabus_weight=topic.get("weight", 1.0),
                    )
                    self.db.add(concept)
                    count += 1

        await self.db.flush()
        return count
