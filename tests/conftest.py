"""Shared test fixtures for SystemDoctor AI."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from packages.shared_utils.knowledge_loader import KnowledgeBase


@pytest.fixture(scope="session")
def knowledge_base() -> KnowledgeBase:
    return KnowledgeBase.load(
        knowledge_dir=PROJECT_ROOT / "knowledge",
        foundry_dir=PROJECT_ROOT / ".foundry",
    )
