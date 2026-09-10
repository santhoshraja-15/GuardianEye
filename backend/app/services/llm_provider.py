"""
LLM Provider Abstraction

Assistant -> Intent/Context Layer -> Event Data/Analytics Layer -> LLM Provider -> Grounded Response

The provider's only job is turning already-computed, already-verified facts
into readable prose. It is never given the ability to decide what the facts
are — every prompt embeds the exact numbers the analytics layer computed
and instructs the model to narrate them, not recompute or invent them. If
a provider call fails, is unconfigured, or times out, callers always get a
deterministic templated string back instead — the app never blocks on, or
depends on, an external API being reachable.

Provider selection is driven by settings.LLM_PROVIDER + whichever API key
is present; with no key configured (the shipped .env default) this is a
no-network no-op, which is exactly today's "mock" behavior.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger

REQUEST_TIMEOUT_SECONDS = 6.0


class LLMProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def narrate(self, question: str, grounded_facts: Dict[str, Any]) -> Optional[str]:
        """Return a natural-language narration of `grounded_facts`, or None to let the
        caller fall back to its own deterministic template (used on any failure)."""
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """No network call. Callers already build a correct deterministic answer from
    grounded_facts on their own — this provider deliberately returns None every time
    so that path is always what demo/dev environments see, with zero external
    dependency and zero latency."""

    name = "mock"

    def narrate(self, question: str, grounded_facts: Dict[str, Any]) -> Optional[str]:
        return None


def _build_prompt(question: str, grounded_facts: Dict[str, Any]) -> str:
    facts_json = json.dumps(grounded_facts, default=str, indent=2)
    return (
        "You are GuardianEye's warehouse safety copilot. Rewrite the VERIFIED_FACTS "
        "below into 2-4 short, plain-English sentences answering the supervisor's "
        "question. Rules:\n"
        "- Use ONLY the numbers, names, and labels present in VERIFIED_FACTS.\n"
        "- Never invent, estimate, or adjust a count, percentage, timestamp, zone, "
        "or behaviour that is not literally present in VERIFIED_FACTS.\n"
        "- If VERIFIED_FACTS indicates no data is available, say so plainly instead "
        "of guessing.\n"
        "- Do not add a greeting or sign-off. Output only the answer text.\n\n"
        f"SUPERVISOR QUESTION: {question}\n\n"
        f"VERIFIED_FACTS:\n{facts_json}"
    )


class GeminiLLMProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    def narrate(self, question: str, grounded_facts: Dict[str, Any]) -> Optional[str]:
        prompt = _build_prompt(question, grounded_facts)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 220},
        }
        try:
            resp = httpx.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip() or None
        except Exception as exc:  # network, auth, quota, shape — any of these fall back safely
            logger.warning(f"Gemini LLM narration failed, falling back to template: {exc}")
            return None


class OpenAILLMProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def narrate(self, question: str, grounded_facts: Dict[str, Any]) -> Optional[str]:
        prompt = _build_prompt(question, grounded_facts)
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 220,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return text.strip() or None
        except Exception as exc:
            logger.warning(f"OpenAI LLM narration failed, falling back to template: {exc}")
            return None


def get_llm_provider() -> LLMProvider:
    """Resolve the configured provider. Any missing key or unrecognized provider
    name safely degrades to the mock (template-only) provider — never raises."""
    provider = (settings.LLM_PROVIDER or "mock").strip().lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY)
    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAILLMProvider(api_key=settings.OPENAI_API_KEY)
    return MockLLMProvider()
