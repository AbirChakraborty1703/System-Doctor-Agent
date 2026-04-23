"""Verification and loop control for troubleshooting outcomes."""

from __future__ import annotations

from packages.schemas import SessionStatus, TroubleshootingSession, VerificationResult
from packages.shared_utils.text_utils import classify_evidence_state, is_affirmative


class VerificationAgent:
    """Determines whether troubleshooting can end, continue, or escalate."""

    def __init__(self, max_loops: int = 2) -> None:
        self.max_loops = max(1, max_loops)

    def verify(self, session: TroubleshootingSession, feedback: str) -> VerificationResult:
        feedback_state = classify_evidence_state(feedback)
        has_unresolved_marker = "unresolved" in feedback.lower() or "still" in feedback.lower()
        hazard_present = self._hazard_detected(session)

        if feedback_state == "affirmative" and not has_unresolved_marker:
            session.status = SessionStatus.RESOLVED
            return VerificationResult(
                resolved=True,
                confidence_delta=0.1,
                next_action="close_session",
                notes="User confirmed resolution.",
            )

        if hazard_present:
            session.status = SessionStatus.ESCALATED
            session.escalation_advice = (
                "Hardware hazard indicators remain present. Escalate immediately to certified technician."
            )
            return VerificationResult(
                resolved=False,
                confidence_delta=-0.12,
                next_action="escalate",
                notes="Hazard signal triggered immediate escalation.",
            )

        session.loops += 1
        if session.loops >= self.max_loops:
            session.status = SessionStatus.ESCALATED
            session.escalation_advice = (
                "Issue remains unresolved after multiple remediation attempts. "
                "Escalate to certified technician or service center."
            )
            return VerificationResult(
                resolved=False,
                confidence_delta=-0.1,
                next_action="escalate",
                notes="Escalation triggered after repeated unresolved outcome.",
            )

        session.status = SessionStatus.QUESTIONING
        return VerificationResult(
            resolved=False,
            confidence_delta=-0.05,
            next_action="refine_and_retry",
            notes="Collect additional evidence and run another diagnosis cycle.",
        )

    @staticmethod
    def _hazard_detected(session: TroubleshootingSession) -> bool:
        evidence_values = [
            session.evidence.get("hazard_signal", ""),
            session.evidence.get("electrical_hazard_signal", ""),
        ]
        return any(is_affirmative(value) for value in evidence_values if value)
