"""Pydantic data contracts for the multi-agent troubleshooting workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import IssueCategory, OSType, RiskLevel, SessionStatus, Severity


class DeviceMetadata(BaseModel):
    os: OSType = OSType.UNKNOWN
    expected_category: Optional[str] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    symptom_duration: Optional[str] = None
    recent_update: Optional[str] = None
    recent_driver_change: Optional[str] = None
    error_message: Optional[str] = None
    boot_status: Optional[str] = None
    overheating_symptoms: Optional[str] = None
    storage_symptoms: Optional[str] = None
    online_search_enabled: bool = False


class TriageResult(BaseModel):
    category: IssueCategory = IssueCategory.UNKNOWN
    severity: Severity = Severity.MEDIUM
    inferred_os: OSType = OSType.UNKNOWN
    likely_domain: str = "general"
    confidence: float = 0.0
    missing_fields: List[str] = Field(default_factory=list)
    rationale: str = ""


class Question(BaseModel):
    id: str
    text: str
    target_signal: str
    information_gain: float = 0.0


class QAPair(BaseModel):
    question_id: str
    question: str
    answer: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiagnosisCandidate(BaseModel):
    diagnosis_id: str
    title: str
    confidence: float
    category: IssueCategory
    supporting_evidence: List[str] = Field(default_factory=list)
    conflicting_evidence: List[str] = Field(default_factory=list)


class RemediationStep(BaseModel):
    step_no: int
    action: str
    command: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    rollback: Optional[str] = None
    checkpoint: Optional[str] = None
    requires_confirmation: bool = False
    blocked: bool = False
    block_reason: Optional[str] = None


class RemediationPlan(BaseModel):
    diagnosis_id: str
    risk_level: RiskLevel = RiskLevel.LOW
    warnings: List[str] = Field(default_factory=list)
    steps: List[RemediationStep] = Field(default_factory=list)
    escalation_advice: Optional[str] = None


class VerificationResult(BaseModel):
    resolved: bool
    confidence_delta: float = 0.0
    next_action: str
    notes: str = ""


class OnlineInsight(BaseModel):
    title: str
    url: str
    source: str
    summary: str
    relevance: float = 0.0


class SessionReport(BaseModel):
    session_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    issue_summary: str
    os: OSType
    diagnosis: List[DiagnosisCandidate] = Field(default_factory=list)
    online_insights: List[OnlineInsight] = Field(default_factory=list)
    fixes_attempted: List[str] = Field(default_factory=list)
    result: str
    escalation_advice: str


class TroubleshootingSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_issue: str
    metadata: DeviceMetadata = Field(default_factory=DeviceMetadata)
    triage: Optional[TriageResult] = None
    qa_history: List[QAPair] = Field(default_factory=list)
    asked_question_ids: List[str] = Field(default_factory=list)
    evidence: Dict[str, str] = Field(default_factory=dict)
    online_insights: List[OnlineInsight] = Field(default_factory=list)
    diagnoses: List[DiagnosisCandidate] = Field(default_factory=list)
    remediation: Optional[RemediationPlan] = None
    status: SessionStatus = SessionStatus.INTAKE
    loops: int = 0
    last_verification: Optional[VerificationResult] = None
    fixes_attempted: List[str] = Field(default_factory=list)
    escalation_advice: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_storage_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_storage_dict(cls, payload: Dict[str, Any]) -> "TroubleshootingSession":
        return cls.model_validate(payload)
