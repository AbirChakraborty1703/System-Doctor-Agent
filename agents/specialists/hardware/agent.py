"""Hardware specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.shared_utils.text_utils import contains_any


class HardwareSpecialistAgent(BaseSpecialistAgent):
    agent_id = "hardware"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if contains_any(text, ["overheat", "fan", "thermal", "hot"]):
            signal.diagnosis_boosts["overheating_thermal_throttle"] = 0.35
            signal.supporting_evidence.append("Thermal symptoms detected.")
        if contains_any(text, ["no display", "black screen", "beep"]):
            signal.diagnosis_boosts["no_display_gpu_or_ram_fault"] = 0.34
            signal.supporting_evidence.append("Display path failure indicators found.")
        if contains_any(text, ["random restart", "power", "shutdown"]):
            signal.diagnosis_boosts["random_restart_power_or_driver_instability"] = 0.30
            signal.supporting_evidence.append("Power instability or restart pattern observed.")

        return signal
