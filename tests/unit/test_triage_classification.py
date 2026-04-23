from agents.triage import TriageAgent
from packages.schemas import DeviceMetadata, IssueCategory, OSType, Severity


def test_triage_classifies_update_driver_issue() -> None:
    agent = TriageAgent()
    metadata = DeviceMetadata(os=OSType.WINDOWS)
    result = agent.classify(
        "After Windows update and new GPU driver install my laptop restarts randomly.",
        metadata,
    )

    assert result.category in {IssueCategory.UPDATE_DRIVER, IssueCategory.HARDWARE}
    assert result.severity in {Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}
    assert result.inferred_os == OSType.WINDOWS
