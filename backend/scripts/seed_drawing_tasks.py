"""
Seed initial drawing tasks for the platform.
Run: python -m scripts.seed_drawing_tasks
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.base import AsyncSessionLocal
from app.db.models.drawing import DrawingTask, DrawingCategory, DrawingTaskSource
from sqlalchemy import select, func

DEFAULT_RUBRIC = {
    "dimensions": [
        {"name": "perspective", "weight": 0.25, "description": "Correct vanishing points, spatial depth, 3D representation"},
        {"name": "proportion", "weight": 0.20, "description": "Relative scale and realistic measurements of elements"},
        {"name": "composition", "weight": 0.25, "description": "Layout, balance, focal point, framing"},
        {"name": "creativity", "weight": 0.15, "description": "Originality, expressiveness, unique interpretation"},
        {"name": "execution", "weight": 0.15, "description": "Line quality, shading, neatness, technique"},
    ]
}

DRAWING_TASKS = [
    # Imagination Tasks
    {
        "prompt": "Draw a small café nestled inside a hollow banyan tree. Show the entrance arch formed by the tree roots, seating arrangement visible through the opening, and dappled light through the canopy above. Use 2-point perspective.",
        "category": DrawingCategory.imagination, "difficulty": 0.6,
    },
    {
        "prompt": "Imagine a rooftop garden on a 5-storey urban apartment building. Draw the scene showing raised planting beds, a seating pergola, water feature, and the city skyline visible in the background. Apply correct perspective.",
        "category": DrawingCategory.imagination, "difficulty": 0.65,
    },
    {
        "prompt": "Design and draw a bus stop shelter that integrates solar panels on its roof and a vertical green wall on its back panel. Show it along a city street with surroundings.",
        "category": DrawingCategory.imagination, "difficulty": 0.5,
    },
    {
        "prompt": "Draw a small community library built into a hillside. The entrance is at ground level and the reading room appears to emerge from the slope. Show natural light coming through skylights.",
        "category": DrawingCategory.imagination, "difficulty": 0.7,
    },
    # Observation Tasks
    {
        "prompt": "Draw a typical Indian street corner showing: a peepal tree, a small tea stall with its counter and stacked cups, a bicycle leaning against the stall, and a signboard overhead. Pay attention to proportion and shadow.",
        "category": DrawingCategory.observation, "difficulty": 0.55,
    },
    {
        "prompt": "Sketch a traditional Indian step-well (baoli) as seen from a top-down 45° angle. Show the geometric stone steps descending to the water level, with decorative arched niches on the walls.",
        "category": DrawingCategory.observation, "difficulty": 0.65,
    },
    # 3D Visualization Tasks
    {
        "prompt": "A room is described as follows: 6m × 4m floor plan, 3m high ceiling, one window (1.2m × 1.5m) centred on the north wall, one door (1m × 2.1m) on the east wall near the corner. Draw this room in 2-point perspective from a corner view.",
        "category": DrawingCategory.three_d_visualization, "difficulty": 0.6,
    },
    {
        "prompt": "Draw the following solid shape in 3D: A rectangular box (4×2×2 units) with a triangular prism roof on top (ridge height 1.5 units above the box). Show it from a 3/4 perspective view with visible depth.",
        "category": DrawingCategory.three_d_visualization, "difficulty": 0.5,
    },
    {
        "prompt": "Show the unfolding of a cube. Draw a cross-shaped net of a cube (one of the 11 valid nets) with all 6 faces labelled and then draw the 3D cube it folds into beside it.",
        "category": DrawingCategory.three_d_visualization, "difficulty": 0.45,
    },
    # Memory Drawing Tasks
    {
        "prompt": "Draw the front façade of the India Gate, New Delhi, from memory. Show the archway, inscriptions area, and the eternal flame beneath. Focus on proportions and symmetry.",
        "category": DrawingCategory.memory_drawing, "difficulty": 0.55,
    },
    {
        "prompt": "Sketch the exterior of a typical Rajasthani haveli entrance from memory. Include the ornate carved archway (torana), lattice jali screens on upper floors, and the wooden carved door.",
        "category": DrawingCategory.memory_drawing, "difficulty": 0.6,
    },
    # Composition Tasks
    {
        "prompt": "Create a composition contrasting old and new: on the left, sketch a crumbling heritage building; on the right, a sleek glass tower. Connect them with a bridge in the middle. Use the rule of thirds for balance.",
        "category": DrawingCategory.composition, "difficulty": 0.65,
    },
    {
        "prompt": "Design a composition showing four seasons in four quadrants of a square frame. Each quadrant should show the same park bench, but surrounded by appropriate seasonal elements. Ensure visual unity across all four sections.",
        "category": DrawingCategory.composition, "difficulty": 0.7,
    },
    {
        "prompt": "Draw a street scene where the road leads from the foreground into the distance (1-point perspective). Place two trees on either side creating a natural frame, with a small structure or fountain at the vanishing point.",
        "category": DrawingCategory.composition, "difficulty": 0.4,
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        count_result = await db.execute(select(func.count(DrawingTask.id)))
        count = count_result.scalar()
        if count >= 10:
            print(f"Drawing tasks already seeded ({count} found). Skipping.")
            return

        print(f"Seeding {len(DRAWING_TASKS)} drawing tasks...")
        for t in DRAWING_TASKS:
            task = DrawingTask(
                prompt=t["prompt"],
                category=t["category"],
                difficulty=t["difficulty"],
                rubric=DEFAULT_RUBRIC,
                source=DrawingTaskSource.manual,
                is_active=True,
            )
            db.add(task)

        await db.commit()
        print(f"Done! Seeded {len(DRAWING_TASKS)} drawing tasks.")


if __name__ == "__main__":
    asyncio.run(seed())
