from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings


class LlmClient:
    def __init__(self) -> None:
        self._openai = httpx.AsyncClient(
            base_url=str(settings.llm_base_url).rstrip("/"),
            timeout=60,
        )
        self._gemini = httpx.AsyncClient(timeout=60)

    async def close(self) -> None:
        await self._openai.aclose()
        await self._gemini.aclose()

    async def chat(self, *, system: str, user: str, json_mode: bool = False) -> str:
        if settings.llm_api_key:
            return await self._chat_openai(system=system, user=user, json_mode=json_mode)
        if settings.gemini_api_key:
            return await self._chat_gemini(system=system, user=user, json_mode=json_mode)
        return ""

    async def _chat_openai(self, *, system: str, user: str, json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        r = await self._openai.post("/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

    async def _chat_gemini(self, *, system: str, user: str, json_mode: bool) -> str:
        # Google Generative Language API (Gemini) REST
        # We avoid storing keys; key is provided via env at runtime.
        model = settings.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        prompt = user
        if json_mode:
            prompt = (
                user
                + "\n\nReturn ONLY valid JSON. Do not wrap it in markdown. No trailing commentary."
            )

        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        r = await self._gemini.post(url, params={"key": settings.gemini_api_key}, json=payload)
        r.raise_for_status()
        data = r.json()
        # Response: candidates[].content.parts[].text
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        content = (candidates[0].get("content") or {}).get("parts") or []
        texts = [p.get("text") for p in content if isinstance(p, dict) and p.get("text")]
        return "\n".join(texts).strip()


llm = LlmClient()


async def summarize(transcript: str, *, speaker_attributed: bool = False) -> str:
    system = "You summarize meeting transcripts into concise bullet points."
    if speaker_attributed:
        system += (
            " Lines are prefixed with speaker names; attribute ideas and decisions to the right person when clear."
        )
    user = f"Summarize this meeting transcript:\n\n{transcript}"
    return (await llm.chat(system=system, user=user)).strip()


def heuristic_key_points_from_transcript(transcript: str) -> list[str]:
    """Deterministic key points when LLM is unavailable."""
    return _heuristic_key_points(transcript)


def heuristic_summary_fallback(transcript: str, max_chars: int = 2000) -> str:
    """
    Used when no LLM is configured or all LLM calls failed — still show something useful.
    """
    t = (transcript or "").strip()
    if not t:
        return ""
    pts = _heuristic_key_points(t, max_points=12)
    if pts:
        return "\n".join(f"- {p}" for p in pts)
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 3].rstrip() + "…"


def _heuristic_key_points(text: str, max_points: int = 7) -> list[str]:
    """
    Deterministic fallback when no LLM is configured or JSON parsing fails.
    Tries to extract bullet-ish lines; otherwise uses short sentences.
    """
    t = (text or "").strip()
    if not t:
        return []

    points: list[str] = []
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.lstrip("-•* \t").strip()
        if not s:
            continue
        points.append(s)
        if len(points) >= max_points:
            return points

    # If it's a single paragraph, split into short-ish sentences.
    import re

    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
    for s in sentences[:max_points]:
        points.append(s)
    return points[:max_points]


async def extract_key_points(transcript: str, *, speaker_attributed: bool = False) -> list[str]:
    system = (
        "Extract the most important meeting points for quick understanding. "
        "Return STRICT JSON with key 'points' (array of short strings). "
        "No other keys."
    )
    if speaker_attributed:
        system += " The transcript labels speakers per line; you may mention who raised a point when helpful."
    user = f"Transcript:\n\n{transcript}"
    raw = (await llm.chat(system=system, user=user, json_mode=True)).strip()
    if not raw:
        return _heuristic_key_points(transcript)
    try:
        obj = json.loads(raw)
        pts = obj.get("points")
        if isinstance(pts, list):
            out: list[str] = []
            for p in pts:
                if isinstance(p, str) and p.strip():
                    out.append(p.strip())
            return out[:10]
    except Exception:
        return _heuristic_key_points(transcript)
    return _heuristic_key_points(transcript)


async def extract_action_items(transcript: str, *, speaker_attributed: bool = False) -> list[dict[str, Any]]:
    system = (
        "Extract action items from a meeting transcript. "
        "Return JSON with key 'items' (array). Each item: title, owner (optional), due_date (optional)."
    )
    if speaker_attributed:
        system += " Use speaker names from the transcript as owner hints when obvious."
    user = f"Transcript:\n\n{transcript}"
    raw = (await llm.chat(system=system, user=user, json_mode=True)).strip()
    if not raw:
        return []
    try:
        obj = json.loads(raw)
        items = obj.get("items", [])
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
    except Exception:
        return []
    return []


async def rag_answer(question: str, context_chunks: list[dict[str, Any]]) -> str:
    system = (
        "You answer questions using the provided context. "
        "If the answer is not in context, say you don't know."
    )
    ctx = "\n\n".join(
        f"[{i+1}] meeting_id={c.get('meeting_id')} chunk={c.get('chunk')}"
        for i, c in enumerate(context_chunks)
    )
    user = f"Context:\n{ctx}\n\nQuestion: {question}"
    return (await llm.chat(system=system, user=user)).strip()

