import json
import logging
import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

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


def _build_chain():
    chain = []
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    grok_key = os.getenv("GROK_API_KEY", "")
    claude_key = os.getenv("ANTHROPIC_API_KEY", "")

    if gemini_key:
        for model in ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]:
            chain.append(Provider(model, "gemini", model, gemini_key))
    if grok_key:
        chain.append(Provider("grok-3-mini-fast", "grok", "grok-3-mini-fast", grok_key))
    if claude_key:
        chain.append(Provider("claude-sonnet", "claude", os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), claude_key))

    return chain


FALLBACK_CHAIN = _build_chain()


async def _call_gemini(p, system, user):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{p.model}:generateContent?key={p.api_key}"
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post(url, json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1024},
        })
    if r.status_code != 200:
        raise LLMClientError(f"Gemini {p.model}: HTTP {r.status_code}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _call_grok(p, system, user):
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post("https://api.x.ai/v1/chat/completions", headers={
            "Authorization": f"Bearer {p.api_key}", "Content-Type": "application/json",
        }, json={
            "model": p.model, "temperature": 0.0, "max_tokens": 1024,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        })
    if r.status_code != 200:
        raise LLMClientError(f"Grok: HTTP {r.status_code}")
    return r.json()["choices"][0]["message"]["content"]


async def _call_claude(p, system, user):
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post("https://api.anthropic.com/v1/messages", headers={
            "x-api-key": p.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json",
        }, json={
            "model": p.model, "max_tokens": 1024, "system": system,
            "messages": [{"role": "user", "content": user}],
        })
    if r.status_code != 200:
        raise LLMClientError(f"Claude: HTTP {r.status_code}")
    return r.json()["content"][0]["text"]


_CALLERS = {"gemini": _call_gemini, "grok": _call_grok, "claude": _call_claude}


def _parse_score(raw):
    text = raw.strip()
    if "```" in text:
        text = re.sub(r"```\w*\n?", "", text).strip()
    match = re.search(r"\{[^{}]+\}", text)
    if match:
        json_str = match.group(0).replace("'", '"')
        try:
            obj = json.loads(json_str)
            score = obj.get("score")
            if isinstance(score, (int, float)) and 1 <= score <= 5:
                return {"score": float(score), "reason": str(obj.get("reason", "")), "model": ""}
        except json.JSONDecodeError:
            pass
    match = re.search(r'"?score"?\s*[:=]\s*(\d(?:\.\d)?)', text)
    if match:
        score = float(match.group(1))
        if 1 <= score <= 5:
            return {"score": score, "reason": "", "model": ""}
    raise ValueError(f"Cannot extract score from: {text[:120]}")


async def get_score(system_prompt, user_prompt, **kwargs):
    if not FALLBACK_CHAIN:
        raise LLMClientError("No API keys configured. Set at least one of: GEMINI_API_KEY, GROK_API_KEY, ANTHROPIC_API_KEY")
    errors = []
    for p in FALLBACK_CHAIN:
        try:
            raw = await _CALLERS[p.provider](p, system_prompt, user_prompt)
            result = _parse_score(raw)
            result["model"] = p.name
            return result
        except Exception as e:
            logger.warning(f"Fallback — {p.name}: {e}")
            errors.append(f"{p.name}: {e}")
    raise LLMClientError("All providers failed:\n" + "\n".join(f"  - {e}" for e in errors))