from __future__ import annotations

import json
import re
from typing import Any

from app.services.llm import llm, summarize


def _heuristic_action_items(transcript: str, max_items: int = 10) -> list[dict[str, Any]]:
    """
    Minimal fallback when no LLM is configured.
    Looks for lines that start with common action markers.
    """
    items: list[dict[str, Any]] = []
    for line in transcript.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(action item|ai|todo|next steps?)\b[:\-]?\s*", s, flags=re.I):
            task = re.sub(r"^(action item|ai|todo|next steps?)\b[:\-]?\s*", "", s, flags=re.I).strip()
            if task:
                items.append({"task": task, "assigned_to": None, "deadline": None})
        if len(items) >= max_items:
            break
    return items


async def generate_meeting_insights(transcript: str) -> dict[str, Any]:
    """
    Returns structured JSON:
    {
      "summary": "...",
      "action_items": [ { "task": "...", "assigned_to": "...", "deadline": "..." } ]
    }
    """
    t = (transcript or "").strip()
    if not t:
        return {"summary": "", "action_items": []}

    # If no provider configured, return deterministic fallback.
    raw_probe = await llm.chat(system="Return JSON {}", user="{}", json_mode=True)
    if not raw_probe:
        return {"summary": "", "action_items": _heuristic_action_items(t)}

    system = (
        "You are a meeting analyst. Produce STRICT JSON with keys: "
        "summary (string), action_items (array). Each action item must have: "
        "task (string), assigned_to (string or null), deadline (string or null). "
        "Deadlines should be ISO date when possible (YYYY-MM-DD) or a short phrase like 'next Friday'. "
        "Do not include any other keys."
    )
    user = f"Transcript:\n\n{t}"
    raw = (await llm.chat(system=system, user=user, json_mode=True)).strip()

    if not raw:
        # Fall back to summary-only if the provider failed on JSON mode.
        s = (await summarize(t)).strip()
        return {"summary": s, "action_items": _heuristic_action_items(t)}

    try:
        obj = json.loads(raw)
    except Exception:
        s = (await summarize(t)).strip()
        return {"summary": s, "action_items": _heuristic_action_items(t)}

    summary_text = obj.get("summary") if isinstance(obj, dict) else None
    if not isinstance(summary_text, str):
        summary_text = (await summarize(t)).strip()

    items = obj.get("action_items") if isinstance(obj, dict) else None
    norm_items: list[dict[str, Any]] = []
    if isinstance(items, list):
        for it in items:
            if not isinstance(it, dict):
                continue
            task = it.get("task")
            if not isinstance(task, str) or not task.strip():
                continue
            assigned_to = it.get("assigned_to")
            if assigned_to is not None and not isinstance(assigned_to, str):
                assigned_to = None
            deadline = it.get("deadline")
            if deadline is not None and not isinstance(deadline, str):
                deadline = None
            norm_items.append({"task": task.strip(), "assigned_to": assigned_to, "deadline": deadline})

    return {"summary": summary_text.strip(), "action_items": norm_items}

