"""Base contracts for specialist agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from packages.schemas import TroubleshootingSession


@dataclass
class SpecialistSignal:
    diagnosis_boosts: Dict[str, float] = field(default_factory=dict)
    supporting_evidence: List[str] = field(default_factory=list)
    conflicting_evidence: List[str] = field(default_factory=list)


class BaseSpecialistAgent:
    agent_id: str = "base_specialist"

    def analyze(self, session: TroubleshootingSession) -> SpecialistSignal:
        raise NotImplementedError

    @staticmethod
    def _session_text(session: TroubleshootingSession) -> str:
        answers = " ".join([item.answer for item in session.qa_history])
        return f"{session.user_issue} {answers}".lower()
