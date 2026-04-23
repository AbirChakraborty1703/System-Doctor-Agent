"""BIOS and boot chain specialist heuristics."""

from __future__ import annotations

from agents.specialists.base import BaseSpecialistAgent, SpecialistSignal
from packages.shared_utils.text_utils import contains_any


class BiosBootSpecialistAgent(BaseSpecialistAgent):
    agent_id = "bios_boot"

    def analyze(self, session) -> SpecialistSignal:
        text = self._session_text(session)
        signal = SpecialistSignal()

        if contains_any(text, ["bios", "uefi", "post", "boot loop", "bootloader", "grub"]):
            signal.diagnosis_boosts["windows_boot_loop_firmware"] = 0.28
            signal.diagnosis_boosts["no_display_gpu_or_ram_fault"] = 0.18
            signal.supporting_evidence.append("Firmware or startup chain indicators found.")

        return signal
