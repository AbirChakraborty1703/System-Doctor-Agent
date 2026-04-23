"""Windows specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.schemas import OSType
from packages.shared_utils.text_utils import contains_any


class WindowsSpecialistAgent(BaseSpecialistAgent):
    agent_id = "windows"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if session.metadata.os not in {OSType.WINDOWS, OSType.UNKNOWN}:
            return signal

        if contains_any(text, ["bsod", "blue screen", "boot loop", "startup repair"]):
            signal.diagnosis_boosts["windows_boot_loop_firmware"] = 0.34
            signal.supporting_evidence.append("Windows boot chain symptoms found.")

        if contains_any(text, ["driver", "device manager", "after update", "rollback"]):
            signal.diagnosis_boosts["windows_driver_regression"] = 0.36
            signal.supporting_evidence.append("Windows driver regression signal detected.")

        if contains_any(text, ["slow startup", "high cpu", "task manager"]):
            signal.diagnosis_boosts["windows_performance_background_tasks"] = 0.26
            signal.supporting_evidence.append("Windows performance degradation evidence found.")

        return signal
