"""Shared chat-completions client. Never log keys, payloads with keys, or raw env values."""
from __future__ import annotations

from typing import Any

import httpx

from . import config


class LlmError(RuntimeError):
    pass


def complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 700,
    temperature: float = 0.3,
    timeout: float = 45.0,
) -> str:
    if not config.LLM_AVAILABLE:
        raise LlmError("No model is configured.")
    scheme = (config.LLM_AUTH_SCHEME or "Api-Key").strip()
    headers = {
        "Authorization": f"{scheme} {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    url = f"{config.LLM_BASE_URL}/chat/completions"
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("Model response was unusable.") from exc


def complete_vision(
    system: str,
    user: str,
    image_b64: str,
    mime: str = "image/png",
    *,
    max_tokens: int = 700,
    timeout: float = 60.0,
) -> str:
    if not config.LLM_AVAILABLE:
        raise LlmError("No model is configured.")
    model = config.VISION_MODEL or config.LLM_MODEL
    scheme = (config.LLM_AUTH_SCHEME or "Api-Key").strip()
    headers = {
        "Authorization": f"{scheme} {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
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
    url = f"{config.LLM_BASE_URL}/chat/completions"
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError("Vision model response was unusable.") from exc
