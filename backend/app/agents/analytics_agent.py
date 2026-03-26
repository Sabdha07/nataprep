"""
Analytics Agent
Generates dashboard insights, predicted scores, and weak area analysis.
Caches results in Redis for fast dashboard loads.
"""
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.concept import Concept
from app.db.models.question import Question, QuestionConcept
from app.db.models.attempt import QuestionAttempt, PracticeSession
from app.db.models.mastery import UserMastery
from app.core.llm import chat
import structlog

log = structlog.get_logger()

INSIGHT_SYSTEM = """You are an expert learning analytics system for NATA exam preparation.
Generate 3-5 short, actionable insights based on student performance data.
Each insight should be 1 sentence, specific, and motivating.
Mix positive observations with improvement tips.
Be direct — no fluff."""


class AnalyticsAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_dashboard(self, user_id: UUID) -> dict:
        """Generate full dashboard data for a user."""

        # 1. Overall stats
        stats = await self._get_overall_stats(user_id)

        # 2. Concept mastery breakdown
        mastery_data = await self._get_concept_mastery(user_id)

        # 3. Identify weak and strong areas
        weak_areas = [m for m in mastery_data if m["mastery_score"] < 0.5][:5]
        strong_areas = [m for m in mastery_data if m["mastery_score"] >= 0.7][:3]

        # Sort
        weak_areas.sort(key=lambda x: x["mastery_score"])
        strong_areas.sort(key=lambda x: x["mastery_score"], reverse=True)

        # 4. Progress over last 14 days
        progress = await self._get_progress_trend(user_id, days=14)

        # 5. Predicted score
        predicted = self._predict_score(mastery_data, stats)

        # 6. AI insights
        insights = await self._generate_insights(stats, weak_areas, predicted)

        return {
            "user_id": str(user_id),
            "overall_mastery": stats["overall_mastery"],
            "total_questions_attempted": stats["total_attempted"],
            "total_correct": stats["total_correct"],
            "overall_accuracy": stats["accuracy"],
            "study_streak_days": stats["streak"],
            "weak_areas": self._format_weak_areas(weak_areas),
            "strong_areas": strong_areas,
            "recent_progress": progress,
            "predicted_score": predicted,
            "insights": insights,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_overall_stats(self, user_id: UUID) -> dict:
        # Total attempts
        total_result = await self.db.execute(
            select(func.count(QuestionAttempt.id))
            .where(QuestionAttempt.user_id == user_id)
        )
        total = total_result.scalar() or 0

        correct_result = await self.db.execute(
            select(func.count(QuestionAttempt.id))
            .where(QuestionAttempt.user_id == user_id, QuestionAttempt.is_correct == True)
        )
        correct = correct_result.scalar() or 0

        # Overall mastery average
        mastery_result = await self.db.execute(
            select(func.avg(UserMastery.mastery_score)).where(
                UserMastery.user_id == user_id,
                UserMastery.concept_id.isnot(None),
            )
        )
        avg_mastery = mastery_result.scalar() or 0.0

        # Study streak (consecutive days with attempts)
        streak = await self._calculate_streak(user_id)

        return {
            "total_attempted": total,
            "total_correct": correct,
            "accuracy": round(correct / total, 3) if total > 0 else 0.0,
            "overall_mastery": round(float(avg_mastery), 3),
            "streak": streak,
        }

    async def _calculate_streak(self, user_id: UUID) -> int:
        """Count consecutive days with at least one attempt."""
        result = await self.db.execute(
            select(func.date(QuestionAttempt.created_at).label("day"))
            .where(QuestionAttempt.user_id == user_id)
            .group_by(func.date(QuestionAttempt.created_at))
            .order_by(func.date(QuestionAttempt.created_at).desc())
            .limit(60)
        )
        days = [r[0] for r in result.all()]
        if not days:
            return 0

        streak = 0
        today = datetime.now(timezone.utc).date()
        current = today
        for day in days:
            if hasattr(day, 'date'):
                day = day.date()
            if day == current or day == current - timedelta(days=1):
                streak += 1
                current = day
            else:
                break
        return streak

    async def _get_concept_mastery(self, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(UserMastery, Concept)
            .join(Concept, UserMastery.concept_id == Concept.id)
            .where(
                UserMastery.user_id == user_id,
                UserMastery.concept_id.isnot(None),
            )
            .order_by(UserMastery.mastery_score)
        )
        rows = result.all()

        return [
            {
                "concept_id": str(mastery.concept_id),
                "concept_name": concept.name,
                "category": concept.category.value,
                "mastery_score": round(mastery.mastery_score, 3),
                "attempt_count": mastery.attempt_count,
                "accuracy": round(mastery.correct_count / mastery.attempt_count, 3)
                    if mastery.attempt_count > 0 else 0.0,
                "next_review_at": mastery.next_review_at.isoformat() if mastery.next_review_at else None,
            }
            for mastery, concept in rows
        ]

    async def _get_progress_trend(self, user_id: UUID, days: int = 14) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        from sqlalchemy import case, Integer as SAInteger
        result = await self.db.execute(
            select(
                func.date(QuestionAttempt.created_at).label("day"),
                func.count(QuestionAttempt.id).label("total"),
                func.sum(
                    case((QuestionAttempt.is_correct == True, 1), else_=0)
                ).label("correct"),
                func.avg(Question.difficulty).label("avg_difficulty"),
            )
            .join(Question, QuestionAttempt.question_id == Question.id)
            .where(
                QuestionAttempt.user_id == user_id,
                QuestionAttempt.created_at >= since,
            )
            .group_by(func.date(QuestionAttempt.created_at))
            .order_by(func.date(QuestionAttempt.created_at))
        )

        return [
            {
                "date": str(row[0]),
                "questions_attempted": row[1],
                "accuracy": round((row[2] or 0) / row[1], 3) if row[1] > 0 else 0.0,
                "avg_difficulty": round(float(row[3] or 0), 3),
            }
            for row in result.all()
        ]

    def _predict_score(self, mastery_data: list[dict], stats: dict) -> dict:
        """
        Predict NATA aptitude score (out of 120).
        Based on weighted mastery scores across categories.
        """
        # NATA category weights for aptitude (120 marks total)
        category_weights = {
            "mathematics": 0.35,
            "general_aptitude": 0.30,
            "visual_reasoning": 0.20,
            "architecture_gk": 0.10,
            "physics": 0.05,
        }

        category_mastery = {}
        for item in mastery_data:
            cat = item["category"]
            if cat not in category_mastery:
                category_mastery[cat] = []
            category_mastery[cat].append(item["mastery_score"])

        category_avg = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_mastery.items()
        }

        weighted_mastery = sum(
            category_avg.get(cat, 0.3) * weight
            for cat, weight in category_weights.items()
        )

        aptitude_score = round(weighted_mastery * 120, 1)

        # Confidence based on data volume
        total = stats["total_attempted"]
        confidence = "low" if total < 50 else "medium" if total < 200 else "high"

        return {
            "aptitude_score": aptitude_score,
            "drawing_score": 0,  # requires drawing attempts
            "total_score": aptitude_score,
            "confidence": confidence,
            "breakdown": {cat: round(avg * 100, 1) for cat, avg in category_avg.items()},
        }

    def _format_weak_areas(self, weak_areas: list[dict]) -> list[dict]:
        formatted = []
        for area in weak_areas:
            mastery = area["mastery_score"]
            if mastery < 0.2:
                action = f"Start from basics — complete concept review for {area['concept_name']}"
                priority = "high"
            elif mastery < 0.4:
                action = f"Practice 20+ questions on {area['concept_name']} with explanations"
                priority = "high"
            else:
                action = f"Review mistakes and attempt harder {area['concept_name']} questions"
                priority = "medium"

            formatted.append({**area, "recommended_action": action, "priority": priority})
        return formatted

    async def _generate_insights(
        self,
        stats: dict,
        weak_areas: list[dict],
        predicted: dict,
    ) -> list[str]:
        if stats["total_attempted"] < 5:
            return [
                "Start your preparation journey — attempt at least 20 questions to unlock personalized insights.",
                "Use Adaptive Mode for the most efficient learning path.",
            ]

        weak_names = ", ".join(a["concept_name"] for a in weak_areas[:3]) if weak_areas else "none identified yet"
        prompt = f"""Student performance data:
- Total questions attempted: {stats['total_attempted']}
- Overall accuracy: {stats['accuracy']:.1%}
- Overall mastery: {stats['overall_mastery']:.1%}
- Study streak: {stats['streak']} days
- Weak areas: {weak_names}
- Predicted NATA aptitude score: {predicted['aptitude_score']}/120

Generate 4 short, specific, actionable insights (one per line). No numbering, no bullets."""

        response = await chat(
            messages=[{"role": "user", "content": prompt}],
            system=INSIGHT_SYSTEM,
            temperature=0.7,
        )

        lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
        return lines[:5]
