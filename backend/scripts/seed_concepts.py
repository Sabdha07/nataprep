"""
Seed the concept graph for NATA 2026 syllabus.
Run: python -m scripts.seed_concepts
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.base import AsyncSessionLocal
from app.db.models.concept import Concept, ConceptCategory, DrawingSkill, SkillCategory

CONCEPTS = [
    # Mathematics
    {"name": "Algebra", "category": "mathematics", "description": "Linear equations, quadratics, polynomials", "parent": None, "weight": 1.2, "difficulty": 0.5},
    {"name": "Linear Equations", "category": "mathematics", "description": "Single and simultaneous linear equations", "parent": "Algebra", "weight": 1.0, "difficulty": 0.3},
    {"name": "Quadratic Equations", "category": "mathematics", "description": "Roots, discriminant, factoring", "parent": "Algebra", "weight": 1.0, "difficulty": 0.5},
    {"name": "Geometry", "category": "mathematics", "description": "2D and 3D geometric concepts", "parent": None, "weight": 1.5, "difficulty": 0.5},
    {"name": "2D Geometry", "category": "mathematics", "description": "Lines, triangles, circles, polygons", "parent": "Geometry", "weight": 1.2, "difficulty": 0.4},
    {"name": "3D Geometry", "category": "mathematics", "description": "Solids, volumes, surface areas", "parent": "Geometry", "weight": 1.2, "difficulty": 0.6},
    {"name": "Coordinate Geometry", "category": "mathematics", "description": "Points, lines, circles in coordinate plane", "parent": "Geometry", "weight": 1.0, "difficulty": 0.55},
    {"name": "Trigonometry", "category": "mathematics", "description": "Ratios, identities, applications", "parent": None, "weight": 1.0, "difficulty": 0.55},
    {"name": "Statistics & Probability", "category": "mathematics", "description": "Mean, median, mode, basic probability", "parent": None, "weight": 0.8, "difficulty": 0.4},
    {"name": "Number Systems", "category": "mathematics", "description": "HCF, LCM, surds, indices", "parent": None, "weight": 0.9, "difficulty": 0.4},
    {"name": "Mensuration", "category": "mathematics", "description": "Areas, volumes of standard shapes", "parent": None, "weight": 1.3, "difficulty": 0.45},
    # Visual Reasoning
    {"name": "Pattern Recognition", "category": "visual_reasoning", "description": "Number and figure series, matrix patterns", "parent": None, "weight": 1.3, "difficulty": 0.5},
    {"name": "Mirror & Water Images", "category": "visual_reasoning", "description": "Reflection and inversion of figures", "parent": None, "weight": 1.0, "difficulty": 0.45},
    {"name": "Embedded Figures", "category": "visual_reasoning", "description": "Finding hidden figures within complex shapes", "parent": None, "weight": 0.9, "difficulty": 0.55},
    {"name": "3D Visualization", "category": "visual_reasoning", "description": "Cube folding, dice, 3D rotation", "parent": None, "weight": 1.4, "difficulty": 0.65},
    {"name": "Paper Folding & Cutting", "category": "visual_reasoning", "description": "Punch holes and unfolding paper", "parent": None, "weight": 1.0, "difficulty": 0.6},
    # General Aptitude
    {"name": "Logical Reasoning", "category": "general_aptitude", "description": "Deductive and inductive reasoning", "parent": None, "weight": 1.0, "difficulty": 0.5},
    {"name": "Analogies", "category": "general_aptitude", "description": "Word and figure analogies", "parent": "Logical Reasoning", "weight": 0.9, "difficulty": 0.4},
    {"name": "Syllogisms", "category": "general_aptitude", "description": "Deductive logic, Venn diagrams", "parent": "Logical Reasoning", "weight": 0.9, "difficulty": 0.55},
    {"name": "Series Completion", "category": "general_aptitude", "description": "Number and alphabet series", "parent": None, "weight": 1.1, "difficulty": 0.45},
    {"name": "Spatial Reasoning", "category": "general_aptitude", "description": "Mental rotation, spatial orientation", "parent": None, "weight": 1.2, "difficulty": 0.6},
    # Architecture GK
    {"name": "Famous Architects", "category": "architecture_gk", "description": "Indian and international architects and their works", "parent": None, "weight": 1.2, "difficulty": 0.4},
    {"name": "Indian Architecture", "category": "architecture_gk", "description": "Mughal, Dravidian, Colonial, Modern Indian architecture", "parent": None, "weight": 1.3, "difficulty": 0.45},
    {"name": "Architectural Movements", "category": "architecture_gk", "description": "Modernism, Brutalism, Post-modernism, Green architecture", "parent": None, "weight": 1.0, "difficulty": 0.5},
    {"name": "Vernacular Architecture", "category": "architecture_gk", "description": "Regional and traditional building forms of India", "parent": None, "weight": 0.9, "difficulty": 0.45},
    {"name": "Sustainable Design", "category": "architecture_gk", "description": "Green building, LEED, passive design, biophilic design", "parent": None, "weight": 0.9, "difficulty": 0.5},
    {"name": "Building Materials", "category": "architecture_gk", "description": "Properties and uses of concrete, steel, glass, timber, etc.", "parent": None, "weight": 1.0, "difficulty": 0.4},
    {"name": "Urban Planning & Cities", "category": "architecture_gk", "description": "Smart cities, planned cities, famous urban projects", "parent": None, "weight": 0.8, "difficulty": 0.5},
    # Physics
    {"name": "Optics & Light", "category": "physics", "description": "Reflection, refraction, shadows, color", "parent": None, "weight": 0.8, "difficulty": 0.5},
    {"name": "Forces & Structures", "category": "physics", "description": "Load, stress, support reactions, basic structural concepts", "parent": None, "weight": 0.9, "difficulty": 0.55},
]

DRAWING_SKILLS = [
    {"name": "Perspective Drawing", "category": "perspective", "parent": None, "description": "One-point, two-point, and three-point perspective techniques"},
    {"name": "1-Point Perspective", "category": "perspective", "parent": "Perspective Drawing", "description": "Single vanishing point perspective"},
    {"name": "2-Point Perspective", "category": "perspective", "parent": "Perspective Drawing", "description": "Two vanishing point perspective for exterior views"},
    {"name": "3-Point Perspective", "category": "perspective", "parent": "Perspective Drawing", "description": "Three vanishing point for dramatic bird/worm eye views"},
    {"name": "Composition", "category": "composition", "parent": None, "description": "Layout, balance, framing, and visual hierarchy"},
    {"name": "Rule of Thirds", "category": "composition", "parent": "Composition", "description": "Using the rule of thirds grid for balance"},
    {"name": "Balance & Symmetry", "category": "composition", "parent": "Composition", "description": "Symmetrical and asymmetrical balance"},
    {"name": "Proportion & Scale", "category": "proportion", "parent": None, "description": "Relative sizes of elements, human scale"},
    {"name": "Shading & Texture", "category": "shading", "parent": None, "description": "Hatching, cross-hatching, tone rendering"},
    {"name": "Memory Drawing", "category": "creativity", "parent": None, "description": "Drawing from memory with accuracy and detail"},
    {"name": "Imagination Drawing", "category": "creativity", "parent": None, "description": "Creative interpretation of given themes"},
    {"name": "Observation Drawing", "category": "observation", "parent": None, "description": "Drawing from direct observation with accuracy"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        count_result = await db.execute(select(func.count(Concept.id)))
        count = count_result.scalar()
        if count > 0:
            print(f"Concepts already seeded ({count} found). Skipping.")
            return

        print("Seeding concepts...")
        concept_map = {}

        for data in CONCEPTS:
            parent_id = None
            if data["parent"] and data["parent"] in concept_map:
                parent_id = concept_map[data["parent"]]

            concept = Concept(
                name=data["name"],
                category=ConceptCategory(data["category"]),
                description=data.get("description"),
                parent_id=parent_id,
                syllabus_weight=data.get("weight", 1.0),
                difficulty_base=data.get("difficulty", 0.5),
            )
            db.add(concept)
            await db.flush()
            concept_map[data["name"]] = concept.id

        print("Seeding drawing skills...")
        skill_map = {}

        for data in DRAWING_SKILLS:
            parent_id = None
            if data.get("parent") and data["parent"] in skill_map:
                parent_id = skill_map[data["parent"]]

            skill = DrawingSkill(
                name=data["name"],
                category=SkillCategory(data["category"]),
                description=data.get("description"),
                parent_id=parent_id,
            )
            db.add(skill)
            await db.flush()
            skill_map[data["name"]] = skill.id

        await db.commit()
        print(f"Done! Seeded {len(CONCEPTS)} concepts and {len(DRAWING_SKILLS)} drawing skills.")


if __name__ == "__main__":
    asyncio.run(seed())
