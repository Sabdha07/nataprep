"""
Question deduplication utilities.
Phase 1: Simple text-based similarity (Jaccard).
Phase 2: Qdrant vector embeddings for semantic dedup.
"""
import re
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two strings."""
    tokens_a = set(normalize(a).split())
    tokens_b = set(normalize(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def is_duplicate_text(new_text: str, existing_texts: list[str], threshold: float = 0.75) -> bool:
    """
    Returns True if new_text is too similar to any existing text.
    Uses Jaccard similarity. O(n) scan — fine for <10k questions.
    For larger banks, use vector search (Qdrant).
    """
    normalized_new = normalize(new_text)
    for existing in existing_texts:
        sim = jaccard_similarity(normalized_new, normalize(existing))
        if sim >= threshold:
            return True
    return False


def sequence_similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio — good for near-exact matches."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()
