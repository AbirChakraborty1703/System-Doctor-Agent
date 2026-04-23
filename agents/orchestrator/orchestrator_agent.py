"""Orchestration service coordinating all troubleshooting agents."""

from __future__ import annotations

from typing import Optional

from agents.diagnosis_engine import DiagnosisEngineAgent
from agents.question_engine import QuestionEngineAgent
from agents.remediation_engine import RemediationEngineAgent
from agents.specialists import build_specialists
from agents.triage import TriageAgent
from agents.verification import VerificationAgent
from packages.schemas import (
    DeviceMetadata,
    IssueCategory,
    Question,
    SessionStatus,
    TroubleshootingSession,
    VerificationResult,
)
from packages.shared_utils.config import get_config
from packages.shared_utils.knowledge_loader import KnowledgeBase
from packages.shared_utils.llm_provider import LLMProvider
from packages.shared_utils.online_search import OnlineSearchClient
from packages.shared_utils.report_generator import build_session_report, report_to_markdown
from packages.shared_utils.storage import SessionStore


class OrchestratorAgent:
    """High-level workflow coordinator for end-to-end troubleshooting."""

    def __init__(self) -> None:
        self.config = get_config()
        self.knowledge = KnowledgeBase.load(
            knowledge_dir=self.config.knowledge_dir,
            foundry_dir=self.config.foundry_dir,
        )
        self.store = SessionStore(self.config.db_path)
        self.llm_provider = LLMProvider(self.config)
        self.online_search_client = OnlineSearchClient(self.config)

        self.triage_agent = TriageAgent()
        self.question_agent = QuestionEngineAgent(
            max_questions=self.config.max_questions,
            min_confidence_to_stop=self.config.min_confidence_to_stop_questions,
        )
        self.diagnosis_agent = DiagnosisEngineAgent(
            knowledge=self.knowledge,
            specialists=build_specialists(),
            llm_provider=self.llm_provider,
        )
        self.remediation_agent = RemediationEngineAgent(knowledge=self.knowledge)
        self.verification_agent = VerificationAgent(
            max_loops=self.config.max_verification_loops
        )

    def start_session(self, user_issue: str, metadata: DeviceMetadata) -> TroubleshootingSession:
        if self.config.online_search_enabled_default and not metadata.online_search_enabled:
            metadata.online_search_enabled = True

        session = TroubleshootingSession(user_issue=user_issue, metadata=metadata)
        session.triage = self.triage_agent.classify(user_issue, metadata)
        session.status = SessionStatus.QUESTIONING
        self.store.save(session)
        return session

    def load_session(self, session_id: str) -> Optional[TroubleshootingSession]:
        return self.store.get(session_id)

    def next_question(self, session: TroubleshootingSession) -> Optional[Question]:
        question = self.question_agent.next_question(session)
        self.store.save(session)
        return question

    def submit_answer(self, session: TroubleshootingSession, question: Question, answer: str) -> None:
        self.question_agent.record_answer(session, question, answer)
        self.store.save(session)

    def run_diagnosis(self, session: TroubleshootingSession) -> TroubleshootingSession:
        session.diagnoses = self.diagnosis_agent.diagnose(session)

        if self._should_enrich_with_online_search(session):
            insights = self.online_search_client.search(
                session,
                enabled=self._online_search_enabled(session),
            )
            if insights:
                session.online_insights = insights
                session.diagnoses = self.diagnosis_agent.diagnose(session)

        session.status = SessionStatus.REMEDIATION_READY
        self.store.save(session)
        return session

    def build_remediation(self, session: TroubleshootingSession) -> TroubleshootingSession:
        session.remediation = self.remediation_agent.generate(session)
        session.status = SessionStatus.VERIFYING
        self.store.save(session)
        return session

    def verify(self, session: TroubleshootingSession, feedback: str) -> VerificationResult:
        result = self.verification_agent.verify(session, feedback)
        session.last_verification = result
        self.store.save(session)
        return result

    def export_report_markdown(self, session: TroubleshootingSession) -> str:
        report = build_session_report(session)
        return report_to_markdown(report)

    def _online_search_enabled(self, session: TroubleshootingSession) -> bool:
        if session.metadata.online_search_enabled:
            return True
        return self.config.online_search_enabled_default

    def _should_enrich_with_online_search(self, session: TroubleshootingSession) -> bool:
        if not self._online_search_enabled(session):
            return False

        if session.online_insights and session.loops == 0:
            return False

        if session.metadata.recent_update or session.metadata.device_model:
            return True

        if not session.diagnoses:
            return True

        top_confidence = session.diagnoses[0].confidence
        if top_confidence < min(0.85, self.config.min_confidence_to_stop_questions + 0.08):
            return True

        if session.triage and session.triage.category in {
            IssueCategory.UPDATE_DRIVER,
            IssueCategory.BIOS_BOOT,
            IssueCategory.NETWORK,
            IssueCategory.OS_SPECIFIC,
        }:
            return True

        return False
