"""Anthropic SDK wrapper with structured output and model routing."""

import json
import logging
import os

import anthropic
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import MODEL_MAP, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_structured(
    stage: str,
    system: str,
    user_message: str,
    output_model: type[BaseModel],
    max_tokens: int = 4096,
) -> BaseModel:
    """Call Claude with structured output. Returns a validated Pydantic model instance."""
    client = get_client()
    model = MODEL_MAP.get(stage, MODEL_MAP["chat"])

    logger.info(f"LLM call: stage={stage}, model={model}, output={output_model.__name__}")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse response text as JSON into the Pydantic model
    text = response.content[0].text
    # Try to extract JSON from the response
    try:
        # Handle case where model wraps in ```json blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        result = output_model.model_validate_json(text)
    except Exception:
        # Fallback: try parsing as regular JSON
        data = json.loads(text)
        result = output_model.model_validate(data)

    logger.info(f"LLM response parsed: {output_model.__name__}")
    return result


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_text(
    stage: str,
    system: str,
    user_message: str,
    max_tokens: int = 4096,
) -> str:
    """Call Claude and return raw text response."""
    client = get_client()
    model = MODEL_MAP.get(stage, MODEL_MAP["chat"])

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


def call_chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    max_tokens: int = 4096,
) -> anthropic.types.Message:
    """Call Claude with tool_use for the Q&A chat agent."""
    client = get_client()
    model = MODEL_MAP.get("chat", MODEL_MAP["chat"])

    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        tools=tools,
    )
