"""
Fix question-concept mappings in the existing database.

The original seed script mapped ALL questions to the first root concept in each
category (e.g. all math questions → Algebra). This script re-assigns each
question to the most specific concept based on its tags.

Run: python -m scripts.fix_question_concepts
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, delete
from app.db.base import AsyncSessionLocal
from app.db.models.question import Question, QuestionConcept
from app.db.models.concept import Concept

# Same mapping as in seed_questions.py
CATEGORY_TAG_CONCEPT = {
    "mathematics": {
        "quadratic": "Quadratic Equations",
        "linear equations": "Linear Equations",
        "coordinate geometry": "Coordinate Geometry",
        "trigonometry": "Trigonometry",
        "mensuration": "Mensuration",
        "area": "Mensuration",
        "statistics": "Statistics & Probability",
        "probability": "Statistics & Probability",
        "hcf lcm": "Number Systems",
        "surds indices": "Number Systems",
        "number theory": "Number Systems",
        "3d geometry": "3D Geometry",
        "volume": "3D Geometry",
        "surface area": "3D Geometry",
        "geometry": "2D Geometry",
        "triangles": "2D Geometry",
        "circles": "2D Geometry",
        "polygons": "2D Geometry",
        "symmetry": "2D Geometry",
        "algebra": "Algebra",
    },
    "visual_reasoning": {
        "3d visualization": "3D Visualization",
        "nets": "3D Visualization",
        "cube": "3D Visualization",
        "dice": "3D Visualization",
        "mirror images": "Mirror & Water Images",
        "water images": "Mirror & Water Images",
        "counting figures": "Embedded Figures",
        "embedded figures": "Embedded Figures",
        "symmetry": "Embedded Figures",
        "pattern recognition": "Pattern Recognition",
        "analogy": "Pattern Recognition",
        "classification": "Pattern Recognition",
        "directions": "Embedded Figures",
        "distance": "Embedded Figures",
    },
    "general_aptitude": {
        "syllogisms": "Syllogisms",
        "logical reasoning": "Logical Reasoning",
        "coding decoding": "Logical Reasoning",
        "clocks": "Logical Reasoning",
        "age problems": "Logical Reasoning",
        "analogy": "Analogies",
        "series": "Series Completion",
        "alphabet": "Series Completion",
        "patterns": "Series Completion",
        "pipes cisterns": "Series Completion",
        "work problems": "Series Completion",
        "speed distance time": "Series Completion",
        "profit loss": "Series Completion",
        "simple interest": "Series Completion",
        "ratio proportion": "Series Completion",
        "directions": "Spatial Reasoning",
        "distance": "Spatial Reasoning",
    },
    "architecture_gk": {
        "famous architects": "Famous Architects",
        "indian architecture": "Indian Architecture",
        "mughal architecture": "Indian Architecture",
        "mughal": "Indian Architecture",
        "dravidian": "Indian Architecture",
        "architectural movements": "Architectural Movements",
        "modernism": "Architectural Movements",
        "brutalism": "Architectural Movements",
        "vernacular architecture": "Vernacular Architecture",
        "vernacular": "Vernacular Architecture",
        "sustainable design": "Sustainable Design",
        "green building": "Sustainable Design",
        "climate": "Sustainable Design",
        "building materials": "Building Materials",
        "structures": "Building Materials",
        "urban planning": "Urban Planning & Cities",
    },
}


def resolve_concept_name(tags: list, category: str) -> str | None:
    cat_map = CATEGORY_TAG_CONCEPT.get(category, {})
    tag_set = {t.lower() for t in (tags or [])}
    # Iterate map in definition order (most specific entries listed first)
    for map_tag, concept_name in cat_map.items():
        if map_tag in tag_set:
            return concept_name
    return None


async def fix():
    async with AsyncSessionLocal() as db:
        # Load all concepts into a name → object map
        all_concepts = await db.execute(select(Concept).where(Concept.is_active == True))
        concept_name_map = {c.name: c for c in all_concepts.scalars().all()}
        print(f"Loaded {len(concept_name_map)} concepts")

        # Load root concepts per category as fallback
        root_concepts: dict[str, Concept] = {}
        for cat in ["mathematics", "visual_reasoning", "general_aptitude", "architecture_gk"]:
            result = await db.execute(
                select(Concept).where(
                    Concept.category == cat,
                    Concept.parent_id.is_(None),
                    Concept.is_active == True,
                ).limit(1)
            )
            c = result.scalar_one_or_none()
            if c:
                root_concepts[cat] = c

        # Load all questions
        all_qs = await db.execute(select(Question).where(Question.is_active == True))
        questions = all_qs.scalars().all()
        print(f"Found {len(questions)} questions to re-map")

        # Clear all existing question_concept mappings
        await db.execute(delete(QuestionConcept))
        await db.flush()
        print("Cleared existing question_concept mappings")

        remapped = 0
        fallback_used = 0
        concept_counts: dict[str, int] = {}

        for q in questions:
            tags = q.tags or []
            # Infer category from existing tag patterns or use a known approach
            # Since Question model doesn't store category directly, derive from tags
            # by trying all categories
            category = _infer_category(tags, concept_name_map)
            if category is None:
                # Try to figure out from concept mapping context
                # Use the question's tags to guess category
                category = _guess_category_from_tags(tags)

            concept = None
            if category:
                concept_name = resolve_concept_name(tags, category)
                if concept_name and concept_name in concept_name_map:
                    concept = concept_name_map[concept_name]

            if concept is None and category and category in root_concepts:
                concept = root_concepts[category]
                fallback_used += 1

            if concept is None:
                # Last resort: first active concept
                concept = list(concept_name_map.values())[0]
                fallback_used += 1

            if concept:
                mapping = QuestionConcept(
                    question_id=q.id,
                    concept_id=concept.id,
                    relevance_score=1.0,
                )
                db.add(mapping)
                concept_counts[concept.name] = concept_counts.get(concept.name, 0) + 1
                remapped += 1

        await db.commit()

        print(f"\nRe-mapped {remapped} questions ({fallback_used} used fallback)")
        print("\nDistribution by concept:")
        for name, count in sorted(concept_counts.items(), key=lambda x: -x[1]):
            print(f"  {name:<35} {count:>3} questions")


def _infer_category(tags: list, concept_name_map: dict) -> str | None:
    """Infer the question category by checking which category's tag map gives a hit."""
    for cat in ["mathematics", "visual_reasoning", "general_aptitude", "architecture_gk"]:
        cat_map = CATEGORY_TAG_CONCEPT.get(cat, {})
        for tag in tags:
            if tag.lower() in cat_map:
                return cat
    return None


def _guess_category_from_tags(tags: list) -> str | None:
    """Fallback: guess category from tag keywords."""
    tag_str = " ".join(t.lower() for t in tags)
    if any(k in tag_str for k in ["algebra", "geometry", "trigonometry", "calculus", "statistics", "mensuration", "number"]):
        return "mathematics"
    if any(k in tag_str for k in ["3d visualization", "mirror", "pattern", "counting", "analogy", "directions", "embedded"]):
        return "visual_reasoning"
    if any(k in tag_str for k in ["syllogism", "coding", "series", "reasoning", "profit", "speed", "ratio", "clock", "age"]):
        return "general_aptitude"
    if any(k in tag_str for k in ["architect", "building", "indian architecture", "mughal", "sustainable", "urban", "vernacular"]):
        return "architecture_gk"
    return None


if __name__ == "__main__":
    asyncio.run(fix())
