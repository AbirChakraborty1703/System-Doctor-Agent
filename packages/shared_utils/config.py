"""Application configuration with environment variable support."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Keep runtime-provided variables higher priority than local overrides.
load_dotenv(override=False)


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    knowledge_dir: Path
    foundry_dir: Path
    db_path: Path

    llm_provider: str
    openai_api_key: str
    openai_model: str
    gemini_api_key: str
    gemini_model: str

    max_questions: int
    min_confidence_to_stop_questions: float
    max_verification_loops: int
    online_search_enabled_default: bool
    online_search_timeout_seconds: int
    online_search_max_results: int
    online_search_trusted_domains: tuple[str, ...]


def _to_bool(raw_value: str, default: bool = False) -> bool:
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _to_int(raw_value: str | None, default: int, *, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        value = int((raw_value or "").strip())
    except (TypeError, ValueError):
        value = default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _to_float(
    raw_value: str | None,
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    try:
        value = float((raw_value or "").strip())
    except (TypeError, ValueError):
        value = default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    project_root = Path(__file__).resolve().parents[2]
    trusted_domains_raw = os.getenv(
        "ONLINE_SEARCH_TRUSTED_DOMAINS",
        "support.microsoft.com,learn.microsoft.com,apple.com,support.apple.com,"
        "ubuntu.com,help.ubuntu.com,debian.org,archlinux.org,docs.kernel.org,intel.com,nvidia.com,amd.com",
    )
    trusted_domains = tuple(
        item.strip().lower()
        for item in trusted_domains_raw.split(",")
        if item.strip()
    )

    return AppConfig(
        project_root=project_root,
        knowledge_dir=project_root / "knowledge",
        foundry_dir=project_root / ".foundry",
        db_path=project_root / "apps" / "streamlit" / "session_store.db",
        llm_provider=os.getenv("LLM_PROVIDER", "fallback").strip().lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        max_questions=_to_int(os.getenv("MAX_QUESTIONS"), 6, minimum=1, maximum=20),
        min_confidence_to_stop_questions=_to_float(
            os.getenv("MIN_CONFIDENCE_TO_STOP_QUESTIONS"),
            0.72,
            minimum=0.1,
            maximum=0.99,
        ),
        max_verification_loops=_to_int(
            os.getenv("MAX_VERIFICATION_LOOPS"),
            2,
            minimum=1,
            maximum=10,
        ),
        online_search_enabled_default=_to_bool(
            os.getenv("ONLINE_SEARCH_ENABLED", "false"),
            default=False,
        ),
        online_search_timeout_seconds=_to_int(
            os.getenv("ONLINE_SEARCH_TIMEOUT_SECONDS"),
            4,
            minimum=1,
            maximum=30,
        ),
        online_search_max_results=_to_int(
            os.getenv("ONLINE_SEARCH_MAX_RESULTS"),
            4,
            minimum=1,
            maximum=20,
        ),
        online_search_trusted_domains=trusted_domains,
    )
