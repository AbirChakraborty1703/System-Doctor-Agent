"""Update and driver specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.shared_utils.text_utils import contains_any


class UpdateDriverSpecialistAgent(BaseSpecialistAgent):
    agent_id = "update_driver"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if contains_any(text, ["after update", "driver update", "rollback", "patch"]):
            signal.diagnosis_boosts["windows_driver_regression"] = 0.4
            signal.diagnosis_boosts["random_restart_power_or_driver_instability"] = 0.22
            signal.supporting_evidence.append("Update/driver regression pattern detected.")

        return signal
