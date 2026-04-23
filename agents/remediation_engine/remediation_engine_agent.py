"""Remediation plan synthesis with built-in safety constraints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from packages.schemas import (
    OSType,
    RemediationPlan,
    RemediationStep,
    RiskLevel,
    TroubleshootingSession,
)
from packages.shared_utils.knowledge_loader import KnowledgeBase
from packages.shared_utils.safety import SafetyGuard
from packages.shared_utils.text_utils import is_affirmative


def _risk_from_str(value: str) -> RiskLevel:
    normalized = (value or "medium").strip().lower()
    if normalized == "low":
        return RiskLevel.LOW
    if normalized == "high":
        return RiskLevel.HIGH
    if normalized == "critical":
        return RiskLevel.CRITICAL
    return RiskLevel.MEDIUM


def _max_risk(left: RiskLevel, right: RiskLevel) -> RiskLevel:
    risk_order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    return left if risk_order[left] >= risk_order[right] else right


class RemediationEngineAgent:
    """Builds safe remediation steps for the most likely diagnosis."""

    def __init__(self, knowledge: KnowledgeBase, safety_guard: Optional[SafetyGuard] = None) -> None:
        self.knowledge = knowledge
        self.safety_guard = safety_guard or SafetyGuard()

    def generate(self, session: TroubleshootingSession) -> RemediationPlan:
        if not session.diagnoses:
            return RemediationPlan(
                diagnosis_id="no_diagnosis",
                risk_level=RiskLevel.MEDIUM,
                warnings=["No diagnosis available. Collect more evidence before applying fixes."],
                steps=[],
                escalation_advice="Gather additional logs and symptoms before remediation.",
            )

        primary = session.diagnoses[0]
        playbook_id = self.knowledge.map_diagnosis_to_playbook(primary.diagnosis_id)
        playbook = self.knowledge.get_playbook(playbook_id)
        os_name = self._effective_os(session).value

        if not playbook:
            plan = self._build_generic_plan(primary.diagnosis_id)
        else:
            plan = self._build_playbook_plan(primary.diagnosis_id, playbook, os_name)

        plan = self._ensure_safe_first(plan)
        plan = self._enforce_step_recovery_requirements(plan)

        plan, warnings = self.safety_guard.enforce_plan(plan)

        if primary.confidence < 0.42:
            warnings.append(
                "Diagnosis confidence is low. Validate evidence before applying medium/high-risk steps."
            )
            plan.escalation_advice = (
                "Low-confidence diagnosis. Collect logs, run non-destructive checks, and escalate if uncertainty remains."
            )

        hazard_signals = [
            session.evidence.get("hazard_signal", ""),
            session.evidence.get("electrical_hazard_signal", ""),
        ]
        if any(is_affirmative(item) for item in hazard_signals if item):
            plan.risk_level = RiskLevel.CRITICAL
            warnings.append(
                "Possible hardware safety hazard detected. Power off device and seek professional hardware service."
            )
            plan.escalation_advice = (
                "Potential electrical/thermal hazard. Do not continue risky steps; escalate immediately."
            )

        if not plan.escalation_advice:
            if plan.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
                plan.escalation_advice = (
                    "High-risk operations detected. Consider expert supervision before executing remaining steps."
                )
            else:
                plan.escalation_advice = (
                    "If the issue persists after all steps, escalate to technical support with this session report."
                )

        if warnings:
            plan.warnings = warnings

        return plan

    @staticmethod
    def _effective_os(session: TroubleshootingSession) -> OSType:
        if session.metadata.os != OSType.UNKNOWN:
            return session.metadata.os
        if session.triage and session.triage.inferred_os != OSType.UNKNOWN:
            return session.triage.inferred_os
        return OSType.UNKNOWN

    def _build_playbook_plan(self, diagnosis_id: str, playbook: Dict[str, Any], os_name: str) -> RemediationPlan:
        steps: List[RemediationStep] = []
        for idx, item in enumerate(playbook.get("steps", []), start=1):
            command = item.get("command")
            risk = _risk_from_str(str(item.get("risk", "medium")))
            if command:
                command_risk = _risk_from_str(self.knowledge.get_command_risk(os_name, str(command)))
                risk = _max_risk(risk, command_risk)

            steps.append(
                RemediationStep(
                    step_no=idx,
                    action=str(item.get("action", "Apply troubleshooting step")),
                    command=command,
                    risk_level=risk,
                    rollback=item.get("rollback"),
                    checkpoint=item.get("checkpoint"),
                )
            )

        return RemediationPlan(
            diagnosis_id=diagnosis_id,
            risk_level=_risk_from_str(str(playbook.get("risk_level", "medium"))),
            warnings=list(playbook.get("warnings", [])),
            steps=steps,
            escalation_advice=str(playbook.get("escalation_advice", "")),
        )

    def _build_generic_plan(self, diagnosis_id: str) -> RemediationPlan:
        return RemediationPlan(
            diagnosis_id=diagnosis_id,
            risk_level=RiskLevel.MEDIUM,
            warnings=["Using generic remediation because no specific playbook was found."],
            steps=[
                RemediationStep(
                    step_no=1,
                    action="Create a system restore point or backup relevant data before making changes.",
                    command=None,
                    risk_level=RiskLevel.LOW,
                    rollback="Restore from backup if needed.",
                    checkpoint="Backup completed successfully.",
                ),
                RemediationStep(
                    step_no=2,
                    action="Use Safe Mode or Recovery Mode to run first-line diagnostics.",
                    command=None,
                    risk_level=RiskLevel.MEDIUM,
                    rollback="Boot back into normal mode if no improvement.",
                    checkpoint="Core symptoms reproduced or mitigated in safe environment.",
                ),
                RemediationStep(
                    step_no=3,
                    action="Apply latest stable updates and reboot the system.",
                    command=None,
                    risk_level=RiskLevel.MEDIUM,
                    rollback="Uninstall problematic update if symptom worsens.",
                    checkpoint="Issue behavior changed after reboot.",
                ),
                RemediationStep(
                    step_no=4,
                    action="Re-check core logs and hardware health indicators.",
                    command=None,
                    risk_level=RiskLevel.LOW,
                    rollback=None,
                    checkpoint="Collected new evidence for second-pass diagnosis.",
                ),
            ],
            escalation_advice="If unresolved, escalate with logs and hardware diagnostics.",
        )

    def _ensure_safe_first(self, plan: RemediationPlan) -> RemediationPlan:
        if not plan.steps:
            return plan

        has_medium_or_higher = any(
            step.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}
            for step in plan.steps
        )
        if not has_medium_or_higher:
            return plan

        first_step = plan.steps[0]
        first_action = first_step.action.lower()
        if any(
            marker in first_action
            for marker in {"backup", "restore point", "snapshot", "recovery"}
        ):
            return plan

        preflight = RemediationStep(
            step_no=1,
            action="Create backup/restore point and verify recovery path before system changes.",
            command=None,
            risk_level=RiskLevel.LOW,
            rollback="Restore from backup or recovery image if needed.",
            checkpoint="Backup/restore checkpoint validated.",
        )
        shifted_steps: List[RemediationStep] = [preflight]
        for idx, step in enumerate(plan.steps, start=2):
            step.step_no = idx
            shifted_steps.append(step)
        plan.steps = shifted_steps
        return plan

    def _enforce_step_recovery_requirements(self, plan: RemediationPlan) -> RemediationPlan:
        warnings = list(plan.warnings)
        for step in plan.steps:
            if step.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}:
                step.requires_confirmation = True
                if not step.checkpoint:
                    step.checkpoint = "Validate observed outcome and confirm no regressions before continuing."
                    warnings.append(
                        f"Step {step.step_no} had no checkpoint; default checkpoint was added."
                    )
                if not step.rollback and step.risk_level == RiskLevel.MEDIUM:
                    step.rollback = (
                        "Stop this step and revert the changed setting/package if symptoms worsen."
                    )
                    warnings.append(
                        f"Step {step.step_no} had no rollback; conservative rollback guidance was added."
                    )
            if step.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and not step.rollback:
                step.blocked = True
                step.block_reason = "High-risk step is blocked until explicit rollback instructions are provided."
                warnings.append(
                    f"Step {step.step_no} blocked: high-risk step missing rollback guidance."
                )

        plan.warnings = sorted(set(warnings))
        return plan
