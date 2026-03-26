"""
Drawing Task Generation Agent
Generates diverse, NATA-quality drawing prompts with rubrics.
"""
import random
from app.agents.base_agent import BaseAgent
from app.db.models.drawing import DrawingTask, DrawingCategory, DrawingTaskSource
from app.core.llm import chat_json
import structlog

log = structlog.get_logger()

TASK_GEN_SYSTEM = """You are a NATA drawing task designer with 10+ years of experience.
You create drawing prompts that test architectural visualization, creativity, and spatial reasoning.

Good NATA drawing prompts:
- Are specific enough to guide but open enough for creativity
- Test architectural and spatial thinking
- Are achievable in 30-60 minutes with pencil/pen
- Range from simple (single building) to complex (street scenes, interior spaces)
- Can include: memory drawing, imagination, perspective, composition, observation tasks

Never create:
- Abstract art prompts (NATA tests architectural drawing, not fine art)
- Overly complex prompts requiring special knowledge
- Prompts requiring color (NATA drawings are typically line + shading)
"""

CATEGORY_EXAMPLES = {
    "imagination": [
        "A futuristic bus stop with solar panels and green walls",
        "A community library built into a hillside",
        "A floating restaurant above a river",
    ],
    "observation": [
        "Draw a street corner with a shop, tree, and signage",
        "Sketch an old Indian haveli entrance gateway",
        "Draw a bicycle parked against a wall with its shadow",
    ],
    "3d_visualization": [
        "Convert this floor plan description into a perspective drawing: L-shaped room, window on north wall, door on east",
        "Draw a 2x2x2 meter cube with a cylindrical tower on top",
        "Sketch a building with a triangular roof, arched entrance, and two floors",
    ],
    "memory_drawing": [
        "Draw the facade of a famous Indian monument from memory",
        "Sketch a traditional South Indian temple gopuram from memory",
        "Draw a typical Indian street market scene from memory",
    ],
    "composition": [
        "Create a composition showing the contrast between old and new architecture",
        "Design a garden with a central water feature and surrounding pathways",
        "Draw a street scene using the rule of thirds to create visual balance",
    ],
}

DEFAULT_RUBRIC = {
    "dimensions": [
        {"name": "perspective", "weight": 0.25, "description": "Correct vanishing points, spatial depth, 3D representation"},
        {"name": "proportion", "weight": 0.20, "description": "Relative scale and realistic measurements of elements"},
        {"name": "composition", "weight": 0.25, "description": "Layout, balance, focal point, framing"},
        {"name": "creativity", "weight": 0.15, "description": "Originality, expressiveness, unique interpretation"},
        {"name": "execution", "weight": 0.15, "description": "Line quality, shading, neatness, technique"},
    ]
}


class DrawingTaskAgent(BaseAgent):
    name = "drawing_task_agent"

    async def execute(
        self,
        count: int = 10,
        category: str | None = None,
        difficulty: float | None = None,
    ) -> dict:
        categories = list(CATEGORY_EXAMPLES.keys()) if not category else [category]
        created = []

        for i in range(count):
            cat = categories[i % len(categories)]
            diff = difficulty or round(random.uniform(0.2, 0.9), 2)
            try:
                task = await self._generate_task(cat, diff)
                saved = await self._save_task(task, cat, diff)
                created.append(str(saved.id))
            except Exception as e:
                log.warning("drawing_task_gen_failed", index=i, error=str(e))

        return {"requested": count, "created": len(created), "task_ids": created}

    async def _generate_task(self, category: str, difficulty: float) -> dict:
        examples = CATEGORY_EXAMPLES.get(category, CATEGORY_EXAMPLES["imagination"])
        examples_text = "\n".join(f"- {ex}" for ex in examples)

        diff_label = "simple" if difficulty < 0.4 else "moderate" if difficulty < 0.7 else "complex"

        prompt = f"""Generate 1 NATA drawing task.

Category: {category}
Difficulty: {difficulty:.1f} ({diff_label})
Target time: 30-60 minutes

Example prompts in this category:
{examples_text}

Return JSON:
{{
  "prompt": "The complete drawing task description (2-4 sentences, specific and clear)",
  "category": "{category}",
  "difficulty": {difficulty:.2f},
  "estimated_time_minutes": 45,
  "hints": ["Optional hint 1", "Optional hint 2"],
  "rubric_focus": ["Main skill 1", "Main skill 2"]
}}"""

        return await chat_json(
            messages=[{"role": "user", "content": prompt}],
            system=TASK_GEN_SYSTEM,
        )

    async def _save_task(self, data: dict, category: str, difficulty: float) -> DrawingTask:
        cat_map = {
            "imagination": DrawingCategory.imagination,
            "observation": DrawingCategory.observation,
            "3d_visualization": DrawingCategory.three_d_visualization,
            "memory_drawing": DrawingCategory.memory_drawing,
            "composition": DrawingCategory.composition,
        }

        task = DrawingTask(
            prompt=data["prompt"],
            category=cat_map.get(category, DrawingCategory.imagination),
            difficulty=data.get("difficulty", difficulty),
            rubric=DEFAULT_RUBRIC,
            source=DrawingTaskSource.generated,
            is_active=True,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
