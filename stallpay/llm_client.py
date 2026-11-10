"""Shared chat-completions client. Never log keys, payloads with keys, or raw env values."""
from __future__ import annotations

from typing import Any

import httpx

from . import config
from .limits import LlmCapped, consume


class LlmError(RuntimeError):
    pass


def _clamped_max_tokens(requested: int) -> int:
    ceiling = max(1, int(config.LLM_MAX_TOKENS))
    return max(1, min(int(requested), ceiling))


def _input_chars(*parts: str) -> int:
    return sum(len(part or "") for part in parts)


def _reserve(input_chars: int) -> None:
    if not consume(input_chars):
        raise LlmCapped("Model usage cap reached.")


def _auth_headers() -> dict[str, str]:
    scheme = (config.LLM_AUTH_SCHEME or "Api-Key").strip()
    return {
        "Authorization": f"{scheme} {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }


def _post_completion(body: dict[str, Any], timeout: float) -> str:
    url = f"{config.LLM_BASE_URL}/chat/completions"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=_auth_headers(), json=body)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise LlmError("Model timed out.") from exc
    except httpx.HTTPError as exc:
        raise LlmError("Model request failed.") from exc
    try:
        choice = data["choices"][0]
        content = (choice.get("message") or {}).get("content")
        finish = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("Model response was unusable.") from exc
    if content is None or not str(content).strip():
        # Reasoning models can spend the whole token budget before any visible text.
        if finish == "length":
            raise LlmError("Model response was empty after the token budget.")
        raise LlmError("Model response was unusable.")
    return str(content)


def complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 1000,
    temperature: float = 0.3,
    timeout: float = 45.0,
) -> str:
    if not config.LLM_AVAILABLE:
        raise LlmError("No model is configured.")
    _reserve(_input_chars(system, user))
    max_tokens = _clamped_max_tokens(max_tokens)
    body = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _post_completion(body, timeout)


def complete_vision(
    system: str,
    user: str,
    image_b64: str,
    mime: str = "image/png",
    *,
    max_tokens: int = 1000,
    timeout: float = 60.0,
) -> str:
    if not config.LLM_AVAILABLE:
        raise LlmError("No model is configured.")
    # Count only the text prompt. Image bytes are already size-limited at upload.
    _reserve(_input_chars(system, user))
    max_tokens = _clamped_max_tokens(max_tokens)
    model = config.VISION_MODEL or config.LLM_MODEL
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{image_b64}"},
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    return _post_completion(body, timeout)
