"""macOS specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.schemas import OSType
from packages.shared_utils.text_utils import contains_any


class MacOSSpecialistAgent(BaseSpecialistAgent):
    agent_id = "macos"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if session.metadata.os not in {OSType.MACOS, OSType.UNKNOWN}:
            return signal

        if contains_any(text, ["spinning beachball", "app crash", "not responding", "macos update"]):
            signal.diagnosis_boosts["macos_app_crash_extension_conflict"] = 0.34
            signal.supporting_evidence.append("macOS app crash indicators found.")

        return signal
