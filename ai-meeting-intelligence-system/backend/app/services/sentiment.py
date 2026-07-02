from __future__ import annotations

import re


POS = {"great", "good", "happy", "love", "excellent", "awesome", "win", "success", "thanks"}
NEG = {"bad", "sad", "hate", "terrible", "awful", "bug", "issue", "problem", "blocked"}


def simple_sentiment(text: str) -> dict[str, float | str]:
    tokens = re.findall(r"[a-z']+", text.lower())
    pos = sum(1 for t in tokens if t in POS)
    neg = sum(1 for t in tokens if t in NEG)
    total = max(len(tokens), 1)
    score = (pos - neg) / max(pos + neg, 1)
    label = "neutral"
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    return {"label": label, "score": float(score), "pos_ratio": pos / total, "neg_ratio": neg / total}


def analyze_sentiment(transcript: str) -> dict[str, str | float]:
    """
    Lightweight lexicon sentiment analyzer.

    Output:
    - label: positive | neutral | negative
    - score: float in [-1, 1] (higher = more positive)
    - explanation: short human-readable reason
    """
    s = simple_sentiment(transcript or "")
    label = str(s["label"])
    score = float(s["score"])
    pos_ratio = float(s["pos_ratio"])
    neg_ratio = float(s["neg_ratio"])

    explanation = (
        f"Detected slightly more positive than negative language (pos_ratio={pos_ratio:.3f}, neg_ratio={neg_ratio:.3f})."
        if label == "positive"
        else f"Detected slightly more negative than positive language (neg_ratio={neg_ratio:.3f}, pos_ratio={pos_ratio:.3f})."
        if label == "negative"
        else f"Balanced language overall (pos_ratio={pos_ratio:.3f}, neg_ratio={neg_ratio:.3f})."
    )

    return {"label": label, "score": score, "explanation": explanation}

