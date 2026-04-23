from agents.orchestrator import OrchestratorAgent
from packages.schemas import DeviceMetadata, OSType


def test_end_to_end_report_export() -> None:
    orchestrator = OrchestratorAgent()
    session = orchestrator.start_session(
        "Wi-Fi disconnects every few minutes on Linux after a package update.",
        DeviceMetadata(os=OSType.LINUX, recent_update="kernel and network-manager"),
    )

    for _ in range(3):
        session = orchestrator.load_session(session.session_id) or session
        question = orchestrator.next_question(session)
        if not question:
            break
        orchestrator.submit_answer(session, question, "yes")

    session = orchestrator.load_session(session.session_id) or session
    session = orchestrator.run_diagnosis(session)
    session = orchestrator.build_remediation(session)
    report_md = orchestrator.export_report_markdown(session)

    assert "SystemDoctor AI Session Report" in report_md
    assert "Top Diagnoses" in report_md
