"""Adaptive question selection for evidence collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from packages.schemas import (
    IssueCategory,
    OSType,
    QAPair,
    Question,
    SessionStatus,
    TroubleshootingSession,
)
from packages.shared_utils.text_utils import classify_evidence_state


@dataclass(frozen=True)
class AdaptiveQuestion:
    question: Question
    os_scope: Set[OSType] = field(default_factory=set)
    required_signals: Set[str] = field(default_factory=set)
    blocked_signals: Set[str] = field(default_factory=set)
    trigger_keywords: Set[str] = field(default_factory=set)


class QuestionEngineAgent:
    """Selects the highest information-gain next question for the active session."""

    def __init__(self, max_questions: int = 8, min_confidence_to_stop: float = 0.72) -> None:
        self.max_questions = max_questions
        self.min_confidence_to_stop = min_confidence_to_stop

        self.question_bank: Dict[IssueCategory, List[AdaptiveQuestion]] = {
            IssueCategory.BIOS_BOOT: [
                self._q("bios_1", "Do you see the manufacturer logo before restart?", "logo_visibility", 0.95),
                self._q("bios_2", "Did this start after changing BIOS/UEFI settings?", "firmware_change", 0.92),
                self._q("bios_3", "Are there beep codes or LED blink patterns at startup?", "post_code", 0.9),
                self._q("bios_4", "Does an external monitor show output during startup?", "external_display_boot", 0.88),
                self._q(
                    "bios_5",
                    "Is the system disk detected in BIOS/UEFI storage list?",
                    "disk_detected_in_firmware",
                    0.89,
                    required_signals={"logo_visibility"},
                ),
                self._q(
                    "bios_6",
                    "Can the system enter recovery or safe mode at all?",
                    "recovery_entry_possible",
                    0.87,
                ),
            ],
            IssueCategory.UPDATE_DRIVER: [
                self._q("upd_1", "Did the issue begin right after an OS update?", "update_timeline", 0.97),
                self._q("upd_2", "Was any driver recently installed or auto-updated?", "driver_timeline", 0.96),
                self._q("upd_3", "Can you boot into safe mode without the issue?", "safe_mode_behavior", 0.92),
                self._q("upd_4", "Do you see a specific update or install error code?", "update_error_code", 0.91),
                self._q("upd_5", "At which phase does update fail (download/install/restart/login)?", "update_failure_phase", 0.89),
                self._q(
                    "upd_6",
                    "Did rollback or uninstalling the recent update improve stability?",
                    "rollback_effect",
                    0.9,
                    required_signals={"update_timeline"},
                ),
            ],
            IssueCategory.HARDWARE: [
                self._q("hw_1", "Does the system overheat or does the fan run unusually loud?", "thermal_signal", 0.9),
                self._q("hw_2", "Does the issue occur under heavy load like gaming or compiling?", "load_trigger", 0.88),
                self._q("hw_3", "Do you notice random shutdowns or sudden restarts?", "power_instability", 0.86),
                self._q("hw_4", "Does behavior change when running on battery versus charger?", "power_source_dependency", 0.82),
                self._q("hw_5", "Any burning smell, swelling battery, or electrical noise?", "electrical_hazard_signal", 0.95),
                self._q("hw_6", "Any new RAM/GPU/peripheral installed before issue started?", "recent_hardware_change", 0.84),
            ],
            IssueCategory.PERFORMANCE: [
                self._q("perf_1", "Is CPU or memory usage consistently high when the issue occurs?", "resource_pressure", 0.91),
                self._q("perf_2", "Did startup become slower after installing new software?", "startup_regression", 0.88),
                self._q("perf_3", "Does slowness affect all apps or only one specific app?", "scope_of_impact", 0.86),
                self._q("perf_4", "Is disk usage frequently above 90% during slowdown?", "disk_pressure", 0.86),
                self._q("perf_5", "Did this begin after a system update, driver update, or security software change?", "performance_change_timeline", 0.87),
                self._q("perf_6", "Do temperatures spike when slowdown occurs?", "performance_thermal_correlation", 0.84),
            ],
            IssueCategory.SOFTWARE: [
                self._q("sw_1", "Do you get a repeatable error message or code?", "error_signature", 0.94),
                self._q("sw_2", "Does the issue happen in one app or across multiple apps?", "app_scope", 0.88),
                self._q("sw_3", "Did reinstalling or updating the affected app change anything?", "reinstall_effect", 0.83),
                self._q("sw_4", "Did this start after adding a plugin, extension, or security tool?", "extension_or_security_change", 0.84),
                self._q("sw_5", "Does the same issue occur in a clean user profile?", "profile_scope", 0.81),
                self._q("sw_6", "Is there a crash log or event signature we can use?", "log_signature", 0.86),
            ],
            IssueCategory.STORAGE: [
                self._q("st_1", "Is your disk almost full or showing disk read/write errors?", "disk_capacity_health", 0.94),
                self._q("st_2", "Do apps freeze during file operations?", "io_freeze", 0.9),
                self._q("st_3", "Have you noticed unusual clicking sounds from storage hardware?", "mechanical_fault_signal", 0.91),
                self._q("st_4", "Any SMART warning or frequent file-system repair prompt?", "smart_or_fs_warning", 0.88),
                self._q("st_5", "Did issues start after a sudden power loss?", "power_loss_before_io_issue", 0.84),
            ],
            IssueCategory.NETWORK: [
                self._q("net_1", "Is the problem only with Wi-Fi or also with wired connections?", "network_scope", 0.9),
                self._q("net_2", "Does reconnecting or rebooting the router temporarily fix it?", "router_dependency", 0.84),
                self._q("net_3", "Did this start after a network adapter or VPN change?", "adapter_change", 0.88),
                self._q("net_4", "Do you receive an IP but still fail DNS or website access?", "dns_vs_link_layer", 0.86),
                self._q("net_5", "Does the issue appear after sleep/hibernation resume?", "resume_related_network_drop", 0.82),
            ],
            IssueCategory.OS_SPECIFIC: [
                self._q("os_1", "Did this begin after a recent OS patch or upgrade?", "os_change", 0.9),
                self._q("os_2", "Is the issue present for all user accounts?", "account_scope", 0.82),
                self._q("os_3", "Can you sign in but fail to open desktop/services?", "login_stage_failure", 0.88),
                self._q("os_4", "Does safe mode or recovery mode behave differently?", "os_recovery_behavior", 0.89),
            ],
        }

        self._global_branch_questions: List[AdaptiveQuestion] = [
            self._q(
                "g_1",
                "Does connecting an external monitor change the black-screen behavior?",
                "external_display_behavior",
                0.87,
                trigger_keywords={"black screen", "no display", "no signal"},
            ),
            self._q(
                "g_2",
                "Can you share the exact error code/text shown on screen?",
                "exact_error_code",
                0.93,
                trigger_keywords={"error", "failed", "code", "exception"},
            ),
            self._q(
                "g_3",
                "Did the problem begin within 24-48 hours of an update or driver change?",
                "timeline_correlation",
                0.9,
                trigger_keywords={"update", "driver", "patch", "upgrade"},
                blocked_signals={"update_timeline", "driver_timeline"},
            ),
            self._q(
                "g_4",
                "Is there risk of hardware damage (heat, smell, sparks, swelling battery)?",
                "hazard_signal",
                0.95,
                trigger_keywords={"hot", "overheat", "smell", "battery", "burn"},
            ),
        ]

        self._os_specific_questions: Dict[OSType, List[AdaptiveQuestion]] = {
            OSType.WINDOWS: [
                self._q("win_1", "Do Event Viewer logs show repeated critical errors around the incident time?", "windows_event_critical", 0.82, os_scope={OSType.WINDOWS}),
                self._q("win_2", "Does the issue occur before sign-in, after sign-in, or only in one app?", "windows_failure_stage", 0.84, os_scope={OSType.WINDOWS}),
                self._q("win_3", "Did a specific KB update correlate with symptom start?", "windows_kb_correlation", 0.88, os_scope={OSType.WINDOWS}),
            ],
            OSType.MACOS: [
                self._q("mac_1", "Do you see kernel panic or repeated crash reports in Console?", "macos_panic_or_crash_report", 0.86, os_scope={OSType.MACOS}),
                self._q("mac_2", "Does Safe Mode reduce crashes or freezes?", "macos_safe_mode_effect", 0.85, os_scope={OSType.MACOS}),
                self._q("mac_3", "Did the issue start after a macOS point update or app extension change?", "macos_update_or_extension_timeline", 0.87, os_scope={OSType.MACOS}),
            ],
            OSType.LINUX: [
                self._q("lin_1", "Is there a package manager error (apt/dnf/pacman) tied to this issue?", "linux_package_error", 0.87, os_scope={OSType.LINUX}),
                self._q("lin_2", "Do journal or systemd logs show dependency/permission failures?", "linux_service_log_failure", 0.88, os_scope={OSType.LINUX}),
                self._q("lin_3", "Did kernel or driver updates happen immediately before the issue?", "linux_kernel_update_timeline", 0.86, os_scope={OSType.LINUX}),
            ],
        }

    def _q(
        self,
        question_id: str,
        text: str,
        target_signal: str,
        information_gain: float,
        *,
        os_scope: Optional[Set[OSType]] = None,
        required_signals: Optional[Set[str]] = None,
        blocked_signals: Optional[Set[str]] = None,
        trigger_keywords: Optional[Set[str]] = None,
    ) -> AdaptiveQuestion:
        return AdaptiveQuestion(
            question=Question(
                id=question_id,
                text=text,
                target_signal=target_signal,
                information_gain=information_gain,
            ),
            os_scope=os_scope or set(),
            required_signals=required_signals or set(),
            blocked_signals=blocked_signals or set(),
            trigger_keywords=trigger_keywords or set(),
        )

    def next_question(self, session: TroubleshootingSession) -> Optional[Question]:
        if not session.triage:
            return None

        if len(session.qa_history) >= self.max_questions:
            session.status = SessionStatus.DIAGNOSIS_READY
            return None

        if self._should_stop_for_confidence(session):
            session.status = SessionStatus.DIAGNOSIS_READY
            return None

        candidates = self._build_candidates(session)
        if not candidates:
            session.status = SessionStatus.DIAGNOSIS_READY
            return None

        ranked = sorted(
            candidates,
            key=lambda item: self._score_question(session, item),
            reverse=True,
        )
        return ranked[0].question

    def _build_candidates(self, session: TroubleshootingSession) -> List[AdaptiveQuestion]:
        triage = session.triage
        if not triage:
            return []

        question_pool: List[AdaptiveQuestion] = []
        question_pool.extend(self.question_bank.get(triage.category, []))
        question_pool.extend(self._global_branch_questions)

        effective_os = self._effective_os(session)
        if effective_os in self._os_specific_questions:
            question_pool.extend(self._os_specific_questions[effective_os])

        filtered: List[AdaptiveQuestion] = []
        text_blob = self._text_blob(session)
        evidence_keys = set(session.evidence.keys())

        for item in question_pool:
            if item.question.id in session.asked_question_ids:
                continue
            if item.question.target_signal in session.evidence:
                continue
            if item.os_scope and effective_os not in item.os_scope:
                continue
            if item.required_signals and not item.required_signals.issubset(evidence_keys):
                continue
            if item.blocked_signals and item.blocked_signals.intersection(evidence_keys):
                continue
            if item.trigger_keywords and not any(keyword in text_blob for keyword in item.trigger_keywords):
                continue
            filtered.append(item)

        return filtered

    def _score_question(self, session: TroubleshootingSession, item: AdaptiveQuestion) -> float:
        score = item.question.information_gain
        missing_fields = set(session.triage.missing_fields if session.triage else [])

        if item.question.target_signal in missing_fields:
            score += 0.08
        if item.required_signals:
            score += 0.06
        if item.trigger_keywords:
            score += 0.04

        target_key = item.question.target_signal
        if target_key in session.evidence:
            score -= 0.4

        effective_os = self._effective_os(session)

        if effective_os in item.os_scope:
            score += 0.03

        update_signals = {"update_timeline", "driver_timeline", "update_error_code", "update_failure_phase"}
        if session.metadata.recent_update and target_key in update_signals:
            score += 0.05

        if "hazard" in target_key or "electrical" in target_key:
            score += 0.07

        return round(score, 4)

    def _should_stop_for_confidence(self, session: TroubleshootingSession) -> bool:
        qa_count = len(session.qa_history)
        if qa_count < 2:
            return False

        affirmative_count = 0
        negative_count = 0
        unknown_count = 0
        for answer in session.evidence.values():
            state = classify_evidence_state(answer)
            if state == "affirmative":
                affirmative_count += 1
            elif state == "negative":
                negative_count += 1
            else:
                unknown_count += 1

        strong_evidence_count = affirmative_count + negative_count
        if strong_evidence_count < 3:
            return False

        coverage = min(1.0, strong_evidence_count / 6.0)
        quality = affirmative_count / max(strong_evidence_count, 1)
        triage_conf = session.triage.confidence if session.triage else 0.5

        contradiction_penalty = min(0.25, 0.08 * negative_count)
        if affirmative_count and negative_count:
            contradiction_penalty += 0.05
        if unknown_count and strong_evidence_count < 4:
            contradiction_penalty += 0.03

        confidence_estimate = (0.44 * coverage) + (0.34 * quality) + (0.22 * triage_conf)
        confidence_estimate -= contradiction_penalty

        threshold = self.min_confidence_to_stop

        if session.loops > 0:
            threshold = max(threshold, 0.82)

        if affirmative_count and negative_count:
            threshold += 0.05

        return confidence_estimate >= threshold

    @staticmethod
    def _effective_os(session: TroubleshootingSession) -> OSType:
        if session.metadata.os != OSType.UNKNOWN:
            return session.metadata.os
        if session.triage and session.triage.inferred_os != OSType.UNKNOWN:
            return session.triage.inferred_os
        return OSType.UNKNOWN

    @staticmethod
    def _text_blob(session: TroubleshootingSession) -> str:
        answers = " ".join(item.answer for item in session.qa_history)
        metadata = " ".join(
            [
                session.metadata.recent_update or "",
                session.metadata.recent_driver_change or "",
                session.metadata.error_message or "",
                session.metadata.boot_status or "",
                session.metadata.overheating_symptoms or "",
                session.metadata.storage_symptoms or "",
                session.metadata.device_model or "",
            ]
        )
        return f"{session.user_issue} {answers} {metadata}".lower()

    def record_answer(
        self,
        session: TroubleshootingSession,
        question: Question,
        answer: str,
    ) -> None:
        if question.id not in session.asked_question_ids:
            session.asked_question_ids.append(question.id)
        if not any(item.question_id == question.id for item in session.qa_history):
            session.qa_history.append(
                QAPair(question_id=question.id, question=question.text, answer=answer)
            )
        session.evidence[question.target_signal] = answer
        session.status = SessionStatus.QUESTIONING
