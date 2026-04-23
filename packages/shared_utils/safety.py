"""Safety guardrails for remediation planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from packages.schemas import RemediationPlan, RemediationStep, RiskLevel


DESTRUCTIVE_PATTERNS = [
    "rm -rf",
    "rm -rf /",
    "mkfs",
    "fdisk",
    "gdisk",
    "parted mklabel",
    "parted mkpart",
    "diskpart clean",
    "format ",
    "dd if=",
    "del /f /s",
    "diskutil erase",
    "diskutil partitiondisk",
    "bcdboot",
    "bcdedit /set",
    "bootrec /fixmbr",
    "bootrec /fixboot",
    "grub-install",
    "parted",
    "reagentc /disable",
    "efibootmgr -b",
    "efibootmgr -o",
]

HIGH_RISK_PATTERNS = [
    "bcdedit",
    "firmware",
    "bios",
    "uefi",
    "bootloader",
    "partition",
    "gpt",
    "mbr",
    "diskutil",
    "chkdsk /f",
    "chkdsk /r",
    "nvram",
    "efibootmgr",
    "bootrec",
    "bcdboot",
    "registry",
    "regedit",
]

SAFE_MODE_FIRST_HINT = (
    "Prefer Safe Mode or Recovery environment before medium/high-risk system changes."
)


@dataclass
class SafetyDecision:
    risk: RiskLevel
    requires_confirmation: bool
    blocked: bool
    warning: str


class SafetyGuard:
    """Evaluates and enforces safety policy for suggested fix steps."""

    def evaluate(self, action: str, command: str, proposed_risk: RiskLevel) -> SafetyDecision:
        normalized = f"{action} {command}".lower()

        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern in normalized:
                return SafetyDecision(
                    risk=RiskLevel.CRITICAL,
                    requires_confirmation=True,
                    blocked=True,
                    warning=(
                        "Blocked destructive operation. Use expert-assisted recovery and full backup first."
                    ),
                )

        risk = proposed_risk
        warning = ""

        for pattern in HIGH_RISK_PATTERNS:
            if pattern in normalized:
                if risk in {RiskLevel.LOW, RiskLevel.MEDIUM}:
                    risk = RiskLevel.HIGH
                warning = "High-risk system operation. Confirm carefully and verify rollback path before execution."
                if any(
                    marker in normalized
                    for marker in {"bios", "uefi", "firmware", "bootloader", "partition", "mbr", "gpt"}
                ):
                    warning += " Firmware/boot/partition operations can cause boot failure; escalate if uncertain."
                break

        requires_confirmation = risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}
        return SafetyDecision(
            risk=risk,
            requires_confirmation=requires_confirmation,
            blocked=False,
            warning=warning,
        )

    def enforce_plan(self, plan: RemediationPlan) -> Tuple[RemediationPlan, List[str]]:
        warnings: List[str] = list(plan.warnings)
        updated_steps: List[RemediationStep] = []

        highest_risk = plan.risk_level
        risk_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }

        for step in plan.steps:
            decision = self.evaluate(step.action, step.command or "", step.risk_level)
            step.risk_level = decision.risk
            step.requires_confirmation = decision.requires_confirmation
            step.blocked = decision.blocked
            step.block_reason = decision.warning if decision.blocked else None

            if step.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and not step.rollback:
                warnings.append(
                    "High-risk step without explicit rollback. Add rollback guidance before execution."
                )

            if decision.warning:
                warnings.append(decision.warning)
            if risk_order[decision.risk] > risk_order[highest_risk]:
                highest_risk = decision.risk
            updated_steps.append(step)

        plan.steps = updated_steps
        if highest_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}:
            warnings.append(SAFE_MODE_FIRST_HINT)
        plan.warnings = sorted(set(warnings))
        plan.risk_level = highest_risk
        return plan, plan.warnings
