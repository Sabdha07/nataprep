"""
Adaptive Learning Agent
Core intelligence: selects the optimal next question for each student.
Uses mastery scores, concept dependencies, and spaced repetition.
"""
import math
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.concept import Concept, ConceptDependency
from app.db.models.question import Question, QuestionConcept
from app.db.models.mastery import UserMastery
from app.db.models.attempt import QuestionAttempt, MistakeLog
import structlog

log = structlog.get_logger()

# SM-2 spaced repetition intervals (days)
REVIEW_INTERVALS = {
    (0.0, 0.4): 1,
    (0.4, 0.6): 3,
    (0.6, 0.8): 7,
    (0.8, 1.01): 14,
}


def get_review_interval(mastery: float) -> int:
    for (low, high), days in REVIEW_INTERVALS.items():
        if low <= mastery < high:
            return days
    return 14


def update_mastery_score(
    current_mastery: float,
    is_correct: bool,
    question_difficulty: float,
    time_taken: int,
    time_limit: int,
) -> float:
    """
    ELO-inspired mastery update.
    Returns new mastery score clamped to [0.0, 1.0].
    """
    K = 0.3  # learning rate
    # Expected probability of correct answer given mastery vs difficulty
    expected = 1.0 / (1.0 + 10 ** ((question_difficulty - current_mastery) / 0.4))
    actual = 1.0 if is_correct else 0.0

    # Time factor: penalize very slow answers slightly, reward fast correct ones
    if time_limit > 0 and time_taken is not None:
        time_ratio = time_taken / time_limit
        time_factor = max(0.5, min(1.2, 1.5 - time_ratio))
    else:
        time_factor = 1.0

    delta = K * (actual - expected) * time_factor
    new_mastery = current_mastery + delta
    return max(0.0, min(1.0, new_mastery))


class AdaptiveAgent:
    """
    Stateless adaptive selection engine.
    Used by practice service on every "next question" request.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_next_question(
        self,
        user_id: UUID,
        session_config: dict | None = None,
        exclude_question_ids: list[UUID] | None = None,
    ) -> Question | None:
        """Select the optimal next question for the user."""
        config = session_config or {}
        allowed_concept_ids = config.get("concept_ids")

        # Step 1: Get all active concepts
        concept_query = select(Concept).where(Concept.is_active == True)
        if allowed_concept_ids:
            concept_query = concept_query.where(Concept.id.in_(allowed_concept_ids))
        concepts_result = await self.db.execute(concept_query)
        concepts = concepts_result.scalars().all()

        if not concepts:
            return None

        # Step 2: Get user mastery for all concepts
        mastery_result = await self.db.execute(
            select(UserMastery).where(
                UserMastery.user_id == user_id,
                UserMastery.concept_id.in_([c.id for c in concepts]),
            )
        )
        mastery_map = {m.concept_id: m for m in mastery_result.scalars().all()}

        # Step 3: Score each concept for selection priority
        concept_scores = []
        now = datetime.now(timezone.utc)

        for concept in concepts:
            mastery = mastery_map.get(concept.id)
            mastery_score = mastery.mastery_score if mastery else 0.0
            last_attempted = mastery.last_attempted_at if mastery else None
            next_review = mastery.next_review_at if mastery else None

            # Priority components
            weakness_priority = 1.0 - mastery_score  # weak areas first

            # Urgency: overdue for review
            if next_review and next_review.tzinfo is None:
                next_review = next_review.replace(tzinfo=timezone.utc)
            if next_review and next_review <= now:
                days_overdue = (now - next_review).days + 1
                review_urgency = min(1.0, days_overdue / 7.0)
            elif last_attempted is None:
                review_urgency = 1.0  # never attempted = highest urgency
            else:
                review_urgency = 0.0

            # Combined selection score
            priority = (weakness_priority * 0.6) + (review_urgency * 0.4)
            concept_scores.append((concept, priority, mastery_score))

        # Step 4: Sort and pick top concept
        concept_scores.sort(key=lambda x: x[1], reverse=True)
        target_concept, _, target_mastery = concept_scores[0]

        # Step 5: Target difficulty = mastery + 0.1 (zone of proximal development)
        target_difficulty = min(0.95, target_mastery + 0.1)
        difficulty_range = (
            max(0.0, target_difficulty - 0.15),
            min(1.0, target_difficulty + 0.15),
        )

        # Step 6: Find best matching question
        exclude_ids = exclude_question_ids or []

        question_query = (
            select(Question)
            .join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .where(
                QuestionConcept.concept_id == target_concept.id,
                Question.is_active == True,
                Question.difficulty.between(difficulty_range[0], difficulty_range[1]),
            )
        )

        if exclude_ids:
            question_query = question_query.where(Question.id.notin_(exclude_ids))

        # Also exclude recently answered questions (last 50)
        recent_result = await self.db.execute(
            select(QuestionAttempt.question_id)
            .where(QuestionAttempt.user_id == user_id)
            .order_by(QuestionAttempt.created_at.desc())
            .limit(50)
        )
        recent_ids = [r[0] for r in recent_result.all()]
        if recent_ids:
            question_query = question_query.where(Question.id.notin_(recent_ids))

        questions_result = await self.db.execute(question_query.limit(10))
        candidates = questions_result.scalars().all()

        all_exclude = list(set(exclude_ids) | set(recent_ids))

        if not candidates:
            # Fallback 1: any question for this concept (still apply exclusions)
            fallback_query = (
                select(Question)
                .join(QuestionConcept, Question.id == QuestionConcept.question_id)
                .where(
                    QuestionConcept.concept_id == target_concept.id,
                    Question.is_active == True,
                )
            )
            if all_exclude:
                fallback_query = fallback_query.where(Question.id.notin_(all_exclude))
            fb_result = await self.db.execute(fallback_query.limit(5))
            candidates = fb_result.scalars().all()

        if not candidates:
            # Fallback 2: try next best concepts (same session constraints)
            for concept, _, _ in concept_scores[1:5]:
                q2 = (
                    select(Question)
                    .join(QuestionConcept, Question.id == QuestionConcept.question_id)
                    .where(
                        QuestionConcept.concept_id == concept.id,
                        Question.is_active == True,
                    )
                )
                if all_exclude:
                    q2 = q2.where(Question.id.notin_(all_exclude))
                r2 = await self.db.execute(q2.limit(5))
                candidates = r2.scalars().all()
                if candidates:
                    break

        if not candidates:
            # Fallback 3: any active question not in session exclude_ids (allow recent repeats)
            q3 = select(Question).where(Question.is_active == True)
            if exclude_ids:
                q3 = q3.where(Question.id.notin_(exclude_ids))
            r3 = await self.db.execute(q3.limit(5))
            candidates = r3.scalars().all()

        if not candidates:
            return None

        # Pick closest difficulty match
        candidates.sort(key=lambda q: abs(q.difficulty - target_difficulty))
        return candidates[0]

    async def process_answer(
        self,
        user_id: UUID,
        question_id: UUID,
        is_correct: bool,
        time_taken_seconds: int,
    ) -> dict:
        """
        Update mastery scores after an answer is submitted.
        Returns mastery delta for response.
        """
        # Get question and its concepts
        q_result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = q_result.scalar_one_or_none()
        if not question:
            return {}

        concept_result = await self.db.execute(
            select(QuestionConcept).where(QuestionConcept.question_id == question_id)
        )
        concept_mappings = concept_result.scalars().all()

        updates = []
        for mapping in concept_mappings:
            mastery = await self._get_or_create_mastery(user_id, mapping.concept_id)
            old_score = mastery.mastery_score

            new_score = update_mastery_score(
                current_mastery=old_score,
                is_correct=is_correct,
                question_difficulty=question.difficulty,
                time_taken=time_taken_seconds,
                time_limit=question.time_limit_seconds,
            )

            mastery.mastery_score = new_score
            mastery.attempt_count += 1
            if is_correct:
                mastery.correct_count += 1
                mastery.streak += 1
            else:
                mastery.streak = 0

            mastery.last_attempted_at = datetime.now(timezone.utc)
            interval_days = get_review_interval(new_score)
            mastery.next_review_at = datetime.now(timezone.utc) + timedelta(days=interval_days)

            await self.db.commit()
            updates.append({
                "concept_id": str(mapping.concept_id),
                "old_mastery": round(old_score, 3),
                "new_mastery": round(new_score, 3),
                "delta": round(new_score - old_score, 3),
            })

        return {"mastery_updates": updates}

    async def _get_or_create_mastery(self, user_id: UUID, concept_id: UUID) -> UserMastery:
        result = await self.db.execute(
            select(UserMastery).where(
                UserMastery.user_id == user_id,
                UserMastery.concept_id == concept_id,
            )
        )
        mastery = result.scalar_one_or_none()
        if not mastery:
            mastery = UserMastery(
                user_id=user_id,
                concept_id=concept_id,
                mastery_score=0.0,
            )
            self.db.add(mastery)
            await self.db.flush()
        return mastery
