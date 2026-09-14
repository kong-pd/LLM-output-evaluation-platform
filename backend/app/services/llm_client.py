import json
import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    pass


@dataclass
class Provider:
    name: str
    provider: str
    model: str
    api_key: str


def _build_chain() -> list[Provider]:
    chain: list[Provider] = []
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    grok_key = os.getenv("GROK_API_KEY", "")
    claude_key = os.getenv("ANTHROPIC_API_KEY", "")

    if gemini_key:
        for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            chain.append(Provider(name=model, provider="gemini", model=model, api_key=gemini_key))
    if grok_key:
        chain.append(Provider(name="grok-3-mini-fast", provider="grok", model="grok-3-mini-fast", api_key=grok_key))
    if claude_key:
        chain.append(Provider(
            name="claude-sonnet", provider="claude",
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), api_key=claude_key,
        ))
    return chain


FALLBACK_CHAIN = _build_chain()


async def _call_gemini(p: Provider, system: str, user: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{p.model}:generateContent?key={p.api_key}"
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post(url, json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 256},
        })
    if r.status_code != 200:
        raise LLMClientError(f"Gemini {p.model} returned {r.status_code}: {r.text[:200]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _call_grok(p: Provider, system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post("https://api.x.ai/v1/chat/completions", headers={
            "Authorization": f"Bearer {p.api_key}", "Content-Type": "application/json",
        }, json={
            "model": p.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.0, "max_tokens": 256,
        })
    if r.status_code != 200:
        raise LLMClientError(f"Grok returned {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"].strip()


async def _call_claude(p: Provider, system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post("https://api.anthropic.com/v1/messages", headers={
            "x-api-key": p.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json",
        }, json={
            "model": p.model, "max_tokens": 256, "system": system,
            "messages": [{"role": "user", "content": user}],
        })
    if r.status_code != 200:
        raise LLMClientError(f"Claude returned {r.status_code}: {r.text[:200]}")
    return r.json()["content"][0]["text"].strip()


_CALLERS = {"gemini": _call_gemini, "grok": _call_grok, "claude": _call_claude}


def _parse_score(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    result = json.loads(text)
    score = result.get("score")
    if not isinstance(score, (int, float)) or score < 1 or score > 5:
        raise ValueError(f"Score out of range: {score}")
    return {"score": float(score), "reason": result.get("reason", ""), "model": ""}


async def get_score(system_prompt: str, user_prompt: str, **kwargs) -> dict:
    if not FALLBACK_CHAIN:
        raise LLMClientError(
            "No API keys configured. Set at least one of: GEMINI_API_KEY, GROK_API_KEY, ANTHROPIC_API_KEY"
        )
    errors: list[str] = []
    for provider in FALLBACK_CHAIN:
        try:
            raw = await _CALLERS[provider.provider](provider, system_prompt, user_prompt)
            result = _parse_score(raw)
            result["model"] = provider.name
            return result
        except Exception as e:
            logger.warning(f"Fallback — {provider.name}: {e}")
            errors.append(f"{provider.name}: {e}")
    raise LLMClientError("All providers failed:\n" + "\n".join(f"  - {e}" for e in errors))
