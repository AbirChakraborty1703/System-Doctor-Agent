"""Software specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.shared_utils.text_utils import contains_any


class SoftwareSpecialistAgent(BaseSpecialistAgent):
    agent_id = "software"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if contains_any(text, ["app crash", "application crash", "exception", "stopped working"]):
            signal.diagnosis_boosts["macos_app_crash_extension_conflict"] = 0.20
            signal.diagnosis_boosts["windows_driver_regression"] = 0.15
            signal.supporting_evidence.append("Application crash signatures present.")

        if contains_any(text, ["service failed", "dependency", "systemctl", "daemon"]):
            signal.diagnosis_boosts["linux_service_dependency_failure"] = 0.30
            signal.supporting_evidence.append("Service dependency failure pattern found.")

        return signal
