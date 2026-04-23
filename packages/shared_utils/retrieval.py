"""Simple local retrieval helpers for evidence matching."""

from __future__ import annotations

import re
from typing import Iterable, List


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    normalized = normalize_text(text)
    hits: List[str] = []
    for keyword in keywords:
        key = keyword.lower().strip()
        if key and key in normalized:
            hits.append(keyword)
    return hits
