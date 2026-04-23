from packages.schemas import (
    DiagnosisCandidate,
    DeviceMetadata,
    IssueCategory,
    OnlineInsight,
    OSType,
    TroubleshootingSession,
)
from packages.shared_utils.report_generator import build_session_report, report_to_markdown


def test_report_generation_contains_core_sections() -> None:
    session = TroubleshootingSession(
        user_issue="Wi-Fi disconnects repeatedly",
        metadata=DeviceMetadata(os=OSType.LINUX),
    )
    session.diagnoses = [
        DiagnosisCandidate(
            diagnosis_id="wifi_adapter_or_stack_issue",
            title="Wi-Fi adapter or stack issue",
            confidence=0.67,
            category=IssueCategory.NETWORK,
            supporting_evidence=["Intermittent disconnect"],
            conflicting_evidence=[],
        )
    ]
    session.online_insights = [
        OnlineInsight(
            title="Vendor bulletin for Wi-Fi adapter instability",
            url="https://support.microsoft.com/topic/example",
            source="support.microsoft.com",
            summary="Known issue after update with mitigation steps.",
            relevance=0.82,
        )
    ]

    report = build_session_report(session)
    markdown = report_to_markdown(report)

    assert "SystemDoctor AI Session Report" in markdown
    assert "Top Diagnoses" in markdown
    assert "Online Insights" in markdown
    assert "Wi-Fi adapter or stack issue" in markdown
