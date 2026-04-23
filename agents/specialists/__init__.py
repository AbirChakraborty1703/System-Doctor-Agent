"""Specialist agent registry."""

from .base import BaseSpecialistAgent, SpecialistSignal
from .bios_boot.agent import BiosBootSpecialistAgent
from .hardware.agent import HardwareSpecialistAgent
from .linux.agent import LinuxSpecialistAgent
from .macos.agent import MacOSSpecialistAgent
from .software.agent import SoftwareSpecialistAgent
from .update_driver.agent import UpdateDriverSpecialistAgent
from .windows.agent import WindowsSpecialistAgent


def build_specialists() -> list[BaseSpecialistAgent]:
    return [
        HardwareSpecialistAgent(),
        SoftwareSpecialistAgent(),
        WindowsSpecialistAgent(),
        MacOSSpecialistAgent(),
        LinuxSpecialistAgent(),
        BiosBootSpecialistAgent(),
        UpdateDriverSpecialistAgent(),
    ]


__all__ = [
    "BaseSpecialistAgent",
    "SpecialistSignal",
    "build_specialists",
]
