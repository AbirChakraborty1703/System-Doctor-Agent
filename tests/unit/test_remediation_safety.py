from agents.remediation_engine import RemediationEngineAgent
from packages.schemas import (
    DeviceMetadata,
    DiagnosisCandidate,
    IssueCategory,
    OSType,
    RiskLevel,
    TroubleshootingSession,
)
from packages.shared_utils.safety import SafetyGuard


def test_remediation_plan_has_safety_controls(knowledge_base) -> None:
    session = TroubleshootingSession(
        user_issue="No display after BIOS update",
        metadata=DeviceMetadata(os=OSType.WINDOWS, boot_status="No display"),
    )
    session.diagnoses = [
        DiagnosisCandidate(
            diagnosis_id="no_display_gpu_or_ram_fault",
            title="No display due to GPU or RAM fault",
            confidence=0.74,
            category=IssueCategory.HARDWARE,
            supporting_evidence=["No display"],
            conflicting_evidence=[],
        )
    ]

    engine = RemediationEngineAgent(knowledge=knowledge_base)
    plan = engine.generate(session)

    assert plan.steps
    assert plan.risk_level.value in {"medium", "high", "critical"}
    assert any(step.requires_confirmation or step.blocked for step in plan.steps)


def test_safety_guard_blocks_destructive_boot_commands() -> None:
    guard = SafetyGuard()
    decision = guard.evaluate(
        action="Repair boot path",
        command="bootrec /fixmbr",
        proposed_risk=RiskLevel.MEDIUM,
    )

    assert decision.blocked is True
    assert decision.risk.value == "critical"
