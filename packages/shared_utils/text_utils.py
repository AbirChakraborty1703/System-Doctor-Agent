"""Text helpers used by triage and diagnosis heuristics."""

from __future__ import annotations

import re
from typing import List


AFFIRMATIVE_MARKERS = {
    "yes",
    "y",
    "true",
    "present",
    "detected",
    "working",
    "works",
    "resolved",
    "fixed",
    "improved",
    "better",
    "stable",
    "high",
    "available",
    "success",
}

NEGATIVE_MARKERS = {
    "no",
    "n",
    "false",
    "none",
    "absent",
    "failed",
    "fail",
    "worse",
    "never",
    "unresolved",
    "not",
    "cannot",
    "can't",
    "wont",
    "won't",
    "nope",
}

UNKNOWN_MARKERS = {
    "unknown",
    "unsure",
    "unclear",
    "n/a",
    "na",
    "not sure",
    "dont know",
    "don't know",
}


def tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return [tok for tok in cleaned.split() if tok]


def contains_any(text: str, words: List[str]) -> bool:
    normalized = text.lower()
    return any(word.lower() in normalized for word in words)


def classify_evidence_state(value: str) -> str:
    if not value:
        return "unknown"

    normalized = value.strip().lower()
    if not normalized:
        return "unknown"

    if normalized in UNKNOWN_MARKERS:
        return "unknown"

    tokens = set(tokenize(normalized))
    has_affirmative = bool(tokens.intersection(AFFIRMATIVE_MARKERS))
    has_negative = bool(tokens.intersection(NEGATIVE_MARKERS))

    if "not sure" in normalized or "don't know" in normalized or "dont know" in normalized:
        return "unknown"

    if has_affirmative and not has_negative:
        return "affirmative"
    if has_negative and not has_affirmative:
        return "negative"
    if has_affirmative and has_negative:
        return "unknown"
    return "unknown"


def is_affirmative(value: str) -> bool:
    return classify_evidence_state(value) == "affirmative"


def is_negative(value: str) -> bool:
    return classify_evidence_state(value) == "negative"
