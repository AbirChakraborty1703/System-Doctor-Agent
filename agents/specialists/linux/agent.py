"""Linux specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.schemas import OSType
from packages.shared_utils.text_utils import contains_any


class LinuxSpecialistAgent(BaseSpecialistAgent):
    agent_id = "linux"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if session.metadata.os not in {OSType.LINUX, OSType.UNKNOWN}:
            return signal

        if contains_any(text, ["systemctl", "service failed", "dependency failed", "daemon"]):
            signal.diagnosis_boosts["linux_service_dependency_failure"] = 0.38
            signal.supporting_evidence.append("Linux service failure signature found.")

        if contains_any(text, ["wifi", "network manager", "dns", "adapter"]):
            signal.diagnosis_boosts["wifi_adapter_or_stack_issue"] = 0.22
            signal.supporting_evidence.append("Linux network stack issue indicators found.")

        return signal
