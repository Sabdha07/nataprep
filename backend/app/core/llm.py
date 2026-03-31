"""
OpenAI API wrapper with retry logic, structured output helpers, and vision support.
Central LLM client used by all agents.

Public interface used by all agents:
  chat()             -> str
  chat_json()        -> Any
  vision_chat()      -> str
  vision_chat_json() -> Any
"""
import json
import base64
from pathlib import Path
from typing import Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
import structlog

log = structlog.get_logger()

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def chat(
    messages: list[dict],
    system: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """Send a chat request and return text response."""
    client = get_client()

    # Prepend system message if provided (OpenAI uses role="system" in messages list)
    full_messages: list[dict] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    response = await client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        messages=full_messages,  # type: ignore[arg-type]
    )
    return response.choices[0].message.content or ""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def chat_json(
    messages: list[dict],
    system: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
) -> Any:
    """
    Send a chat request expecting JSON response.
    Uses OpenAI's json_object response format when supported.
    """
    json_system = (
        system + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation outside JSON."
    ).strip()

    client = get_client()

    full_messages: list[dict] = [{"role": "system", "content": json_system}]
    full_messages.extend(messages)

    response = await client.chat.completions.create(
        model=model or settings.LLM_MODEL,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=full_messages,  # type: ignore[arg-type]
    )
    text = (response.choices[0].message.content or "").strip()

    # Strip markdown code fences if present (shouldn't happen with json_object, but belt-and-suspenders)
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    return json.loads(text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def vision_chat(
    image_path: str | None = None,
    image_base64: str | None = None,
    image_url: str | None = None,
    media_type: str = "image/jpeg",
    prompt: str = "",
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    """
    Send image + text prompt to GPT-4o Vision.
    Provide one of: image_path, image_base64, or image_url.
    """
    client = get_client()

    # Build image content block in OpenAI format
    if image_path:
        with open(image_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{data}", "detail": "high"},
        }
    elif image_base64:
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{image_base64}", "detail": "high"},
        }
    elif image_url:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_url, "detail": "high"},
        }
    else:
        raise ValueError("Provide one of image_path, image_base64, or image_url")

    full_messages: list[dict] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.append({
        "role": "user",
        "content": [
            image_content,
            {"type": "text", "text": prompt},
        ],
    })

    response = await client.chat.completions.create(
        model=model or settings.VISION_MODEL,
        max_tokens=max_tokens,
        messages=full_messages,  # type: ignore[arg-type]
    )
    return response.choices[0].message.content or ""


async def vision_chat_json(
    prompt: str,
    system: str = "",
    **kwargs,
) -> Any:
    """Vision chat expecting JSON response."""
    json_system = (
        system + "\n\nRespond with valid JSON only. No markdown fences."
    ).strip()
    text = await vision_chat(prompt=prompt, system=json_system, **kwargs)
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
    return json.loads(text)
