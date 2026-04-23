from agents.orchestrator import OrchestratorAgent
from packages.schemas import DeviceMetadata, OSType, OnlineInsight


def test_orchestrator_full_cycle() -> None:
    orchestrator = OrchestratorAgent()
    session = orchestrator.start_session(
        "After a Windows update my system restarts and sometimes shows black screen.",
        DeviceMetadata(
            os=OSType.WINDOWS,
            recent_update="KB-last-night",
            recent_driver_change="GPU update",
            boot_status="intermittent black screen",
        ),
    )

    # Collect a few answers in the adaptive loop.
    for _ in range(4):
        session = orchestrator.load_session(session.session_id) or session
        question = orchestrator.next_question(session)
        if not question:
            break
        orchestrator.submit_answer(session, question, "yes")

    session = orchestrator.load_session(session.session_id) or session
    session = orchestrator.run_diagnosis(session)
    session = orchestrator.build_remediation(session)

    assert session.diagnoses
    assert session.remediation is not None
    assert session.remediation.steps


def test_orchestrator_online_insight_enrichment(monkeypatch) -> None:
    orchestrator = OrchestratorAgent()

    def fake_search(session, enabled):
        if not enabled:
            return []
        return [
            OnlineInsight(
                title="Known issue bulletin",
                url="https://support.microsoft.com/topic/example",
                source="support.microsoft.com",
                summary="Recent update known issue and mitigation.",
                relevance=0.8,
            )
        ]

    monkeypatch.setattr(orchestrator.online_search_client, "search", fake_search)

    session = orchestrator.start_session(
        "After Windows update KB123, black screen appears after login.",
        DeviceMetadata(
            os=OSType.WINDOWS,
            recent_update="KB123",
            online_search_enabled=True,
        ),
    )

    for _ in range(4):
        session = orchestrator.load_session(session.session_id) or session
        question = orchestrator.next_question(session)
        if not question:
            break
        orchestrator.submit_answer(session, question, "yes")

    session = orchestrator.load_session(session.session_id) or session
    session = orchestrator.run_diagnosis(session)

    assert session.online_insights
    assert session.online_insights[0].source == "support.microsoft.com"
