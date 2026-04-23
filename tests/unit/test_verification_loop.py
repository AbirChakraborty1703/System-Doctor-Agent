from agents.verification import VerificationAgent
from packages.schemas import TroubleshootingSession


def test_verification_escalates_after_retries() -> None:
    agent = VerificationAgent()
    session = TroubleshootingSession(user_issue="Still failing")

    first = agent.verify(session, "No, still unresolved")
    assert not first.resolved
    assert first.next_action == "refine_and_retry"

    second = agent.verify(session, "No, still unresolved")
    assert not second.resolved
    assert second.next_action == "escalate"
    assert session.escalation_advice
