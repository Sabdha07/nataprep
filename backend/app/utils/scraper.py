"""
Scraping utilities shared across agents.
Handles rate limiting, retries, and HTML cleaning.
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()

DEFAULT_HEADERS = {
    "User-Agent": "NATAPrep-Research-Bot/1.0 (Educational Platform)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def fetch_page(url: str, timeout: int = 20) -> str | None:
    """Fetch a URL and return clean text content."""
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)


async def fetch_pages_batch(urls: list[str], delay: float = 1.0) -> list[tuple[str, str | None]]:
    """Fetch multiple pages with polite delay between requests."""
    results = []
    for url in urls:
        try:
            text = await fetch_page(url)
            results.append((url, text))
        except Exception as e:
            log.warning("fetch_failed", url=url, error=str(e))
            results.append((url, None))
        await asyncio.sleep(delay)
    return results


def extract_questions_from_text(text: str) -> list[str]:
    """
    Heuristic extraction of Q&A blocks from raw text.
    Returns list of raw question strings for further processing.
    """
    import re
    # Match patterns like "Q1.", "Question 1:", "1.", followed by content
    patterns = [
        r"(?:Q\.?\s*\d+\.?|Question\s+\d+[:.)\s]|\d+\.\s)(.{20,500}?)(?=(?:Q\.?\s*\d+|Question\s+\d+|\d+\.\s)|$)",
    ]
    questions = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        questions.extend([m.strip() for m in matches if len(m.strip()) > 30])
    return questions[:50]  # cap to avoid processing too many at once
