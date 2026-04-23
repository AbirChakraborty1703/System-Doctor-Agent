from agents.question_engine import QuestionEngineAgent
from packages.schemas import (
    DeviceMetadata,
    IssueCategory,
    OSType,
    QAPair,
    SessionStatus,
    Severity,
    TriageResult,
    TroubleshootingSession,
)


def test_question_engine_returns_high_value_question() -> None:
    session = TroubleshootingSession(
        user_issue="System restarts after update",
        metadata=DeviceMetadata(os=OSType.WINDOWS),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.8,
            missing_fields=[],
            rationale="",
        ),
        status=SessionStatus.QUESTIONING,
    )

    engine = QuestionEngineAgent(max_questions=6)
    question = engine.next_question(session)

    assert question is not None
    assert question.id == "upd_1"


def test_question_engine_stops_after_threshold() -> None:
    session = TroubleshootingSession(
        user_issue="System restarts after update",
        metadata=DeviceMetadata(os=OSType.WINDOWS),
        triage=TriageResult(
            category=IssueCategory.UPDATE_DRIVER,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.8,
            missing_fields=[],
            rationale="",
        ),
        status=SessionStatus.QUESTIONING,
    )
    session.qa_history = [
        QAPair(question_id="q1", question="q", answer="a"),
        QAPair(question_id="q2", question="q", answer="a"),
    ]
    session.evidence = {
        "update_timeline": "yes",
        "driver_timeline": "yes",
        "safe_mode_behavior": "better",
    }

    engine = QuestionEngineAgent(max_questions=6)
    question = engine.next_question(session)

    assert question is None
    assert session.status == SessionStatus.DIAGNOSIS_READY


def test_question_engine_keeps_asking_with_conflicting_evidence() -> None:
    session = TroubleshootingSession(
        user_issue="System restarts after update",
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
        status=SessionStatus.QUESTIONING,
    )
    session.qa_history = [
        QAPair(question_id="q1", question="q", answer="yes"),
        QAPair(question_id="q2", question="q", answer="no"),
    ]
    session.evidence = {
        "update_timeline": "yes",
        "driver_timeline": "no",
    }

    engine = QuestionEngineAgent(max_questions=6)
    question = engine.next_question(session)

    assert question is not None
    assert session.status == SessionStatus.QUESTIONING


def test_question_engine_prioritizes_hardware_hazard_signal() -> None:
    session = TroubleshootingSession(
        user_issue="Laptop smells hot and battery area is overheating.",
        metadata=DeviceMetadata(os=OSType.WINDOWS),
        triage=TriageResult(
            category=IssueCategory.HARDWARE,
            severity=Severity.HIGH,
            inferred_os=OSType.WINDOWS,
            likely_domain="hardware",
            confidence=0.84,
            missing_fields=[],
            rationale="",
        ),
        status=SessionStatus.QUESTIONING,
    )

    engine = QuestionEngineAgent(max_questions=8)
    question = engine.next_question(session)

    assert question is not None
    assert question.id in {"hw_5", "g_4"}


def test_question_engine_uses_triage_inferred_os_when_metadata_unknown() -> None:
    session = TroubleshootingSession(
        user_issue="Windows reliability issue with critical event logs.",
        metadata=DeviceMetadata(os=OSType.UNKNOWN),
        triage=TriageResult(
            category=IssueCategory.UNKNOWN,
            severity=Severity.MEDIUM,
            inferred_os=OSType.WINDOWS,
            likely_domain="software",
            confidence=0.7,
            missing_fields=[],
            rationale="",
        ),
        status=SessionStatus.QUESTIONING,
    )

    engine = QuestionEngineAgent(max_questions=6)
    question = engine.next_question(session)

    assert question is not None
    assert question.id.startswith("win_")
