from agents.diagnosis_engine import DiagnosisEngineAgent
from agents.specialists import build_specialists
from packages.schemas import DeviceMetadata, IssueCategory, OSType, Severity, TriageResult, TroubleshootingSession
from packages.shared_utils.knowledge_loader import KnowledgeBase


def test_diagnosis_returns_top_three(knowledge_base) -> None:
    session = TroubleshootingSession(
        user_issue="After Windows update and driver install, I have random restarts and occasional black screen.",
        metadata=DeviceMetadata(os=OSType.WINDOWS, recent_update="Yesterday cumulative update"),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.81,
            missing_fields=[],
            rationale="",
        ),
    )
    session.evidence["update_timeline"] = "yes"
    session.evidence["driver_timeline"] = "yes"

    engine = DiagnosisEngineAgent(knowledge=knowledge_base, specialists=build_specialists())
    ranked = engine.diagnose(session)

    assert len(ranked) == 3
    assert ranked[0].confidence >= ranked[1].confidence
    assert ranked[0].diagnosis_id in {
        "windows_driver_regression",
        "random_restart_power_or_driver_instability",
        "windows_boot_loop_firmware",
    }


def test_diagnosis_boosts_windows_update_error_code_pattern(knowledge_base) -> None:
    session = TroubleshootingSession(
        user_issue="Windows update fails with 0x800f0922 during restart phase.",
        metadata=DeviceMetadata(
            os=OSType.WINDOWS,
            recent_update="KB cumulative patch",
            error_message="0x800f0922",
        ),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.86,
            missing_fields=[],
            rationale="",
        ),
    )
    session.evidence["update_timeline"] = "yes"
    session.evidence["update_failure_phase"] = "restart"
    session.evidence["update_error_code"] = "0x800f0922"

    engine = DiagnosisEngineAgent(knowledge=knowledge_base, specialists=build_specialists())
    ranked = engine.diagnose(session)

    top_ids = [item.diagnosis_id for item in ranked]
    assert "windows_update_install_failure" in top_ids


def test_diagnosis_filters_unknown_mapping_ids() -> None:
    knowledge = KnowledgeBase(
        mappings={
            "symptom-to-diagnosis.yaml": {
                "mapping": {
                    "windows_update_error_code": [
                        "driver_regression",
                        "windows_update_install_failure",
                    ]
                }
            }
        }
    )
    session = TroubleshootingSession(
        user_issue="Windows update error code 0x800f0922 after patch.",
        metadata=DeviceMetadata(os=OSType.WINDOWS, error_message="0x800f0922"),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.8,
            missing_fields=[],
            rationale="",
        ),
    )

    engine = DiagnosisEngineAgent(knowledge=knowledge, specialists=[])
    ranked = engine.diagnose(session)

    assert "driver_regression" not in [item.diagnosis_id for item in ranked]
    assert "windows_update_install_failure" in [item.diagnosis_id for item in ranked]


def test_diagnosis_uses_boolean_decision_tree_branches(knowledge_base) -> None:
    session = TroubleshootingSession(
        user_issue="Windows issue began right after a driver update.",
        metadata=DeviceMetadata(os=OSType.WINDOWS),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.82,
            missing_fields=[],
            rationale="",
        ),
    )
    session.evidence["update_timeline"] = "yes"
    session.evidence["safe_mode_behavior"] = "yes, safe mode is stable"

    engine = DiagnosisEngineAgent(knowledge=knowledge_base, specialists=build_specialists())
    ranked = engine.diagnose(session)

    assert ranked[0].diagnosis_id == "windows_driver_regression"
    assert any("Decision tree path matched" in item for item in ranked[0].supporting_evidence)
