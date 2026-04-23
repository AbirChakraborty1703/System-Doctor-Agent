"""Diagnosis ranking engine combining local knowledge and specialist signals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from agents.specialists import BaseSpecialistAgent
from packages.schemas import (
    DiagnosisCandidate,
    IssueCategory,
    OSType,
    TroubleshootingSession,
)
from packages.shared_utils.knowledge_loader import KnowledgeBase
from packages.shared_utils.llm_provider import LLMProvider
from packages.shared_utils.text_utils import classify_evidence_state, tokenize


@dataclass(frozen=True)
class DiagnosisDefinition:
    diagnosis_id: str
    title: str
    category: IssueCategory
    keywords: Tuple[str, ...]
    expected_signals: Tuple[str, ...] = ()
    os_scope: Tuple[OSType, ...] = ()


DIAGNOSIS_CATALOG: Tuple[DiagnosisDefinition, ...] = (
    DiagnosisDefinition(
        "windows_boot_loop_firmware",
        "Windows boot chain or firmware boot-mode mismatch",
        IssueCategory.BIOS_BOOT,
        ("boot loop", "startup repair", "bios", "uefi", "post", "bcd", "winload"),
        ("logo_visibility", "firmware_change", "post_code", "recovery_entry_possible"),
        (OSType.WINDOWS,),
    ),
    DiagnosisDefinition(
        "windows_driver_regression",
        "Driver regression after update",
        IssueCategory.UPDATE_DRIVER,
        (
            "driver",
            "after update",
            "rollback",
            "device manager",
            "bsod",
            "dpc watchdog",
            "driver irql",
            "code 43",
        ),
        ("update_timeline", "driver_timeline", "safe_mode_behavior", "rollback_effect"),
        (OSType.WINDOWS,),
    ),
    DiagnosisDefinition(
        "windows_update_install_failure",
        "Windows update installation or servicing stack failure",
        IssueCategory.UPDATE_DRIVER,
        (
            "windows update",
            "cumulative",
            "kb",
            "servicing stack",
            "install failed",
            "0x800f",
            "0x8024",
            "0xc190",
        ),
        ("update_error_code", "update_failure_phase", "update_timeline"),
        (OSType.WINDOWS,),
    ),
    DiagnosisDefinition(
        "windows_performance_background_tasks",
        "Background process or startup-service performance bottleneck",
        IssueCategory.PERFORMANCE,
        ("slow", "lag", "startup", "high cpu", "high memory", "task manager", "startup apps"),
        ("resource_pressure", "startup_regression", "scope_of_impact", "disk_pressure"),
        (OSType.WINDOWS,),
    ),
    DiagnosisDefinition(
        "startup_login_path_failure",
        "OS startup or login sequence failure",
        IssueCategory.OS_SPECIFIC,
        ("login", "sign in", "profile", "desktop", "stuck", "startup", "launch"),
        ("login_stage_failure", "account_scope", "os_recovery_behavior"),
    ),
    DiagnosisDefinition(
        "macos_app_crash_extension_conflict",
        "macOS app crash due to extension or dependency conflict",
        IssueCategory.SOFTWARE,
        ("macos", "app crash", "not responding", "extension", "plugin", "beachball", "crash report"),
        ("error_signature", "app_scope", "reinstall_effect", "macos_safe_mode_effect"),
        (OSType.MACOS,),
    ),
    DiagnosisDefinition(
        "macos_update_recovery_issue",
        "macOS update or recovery-path regression",
        IssueCategory.UPDATE_DRIVER,
        ("macos update", "ventura", "sonoma", "sequoia", "recovery", "kernel panic", "failed to update"),
        ("os_change", "macos_update_or_extension_timeline", "os_recovery_behavior"),
        (OSType.MACOS,),
    ),
    DiagnosisDefinition(
        "linux_service_dependency_failure",
        "Linux service failure caused by missing dependency or unit config",
        IssueCategory.SOFTWARE,
        ("linux", "systemctl", "service failed", "dependency", "daemon", "journalctl", "unit failed"),
        ("error_signature", "app_scope", "linux_service_log_failure"),
        (OSType.LINUX,),
    ),
    DiagnosisDefinition(
        "linux_package_manager_conflict",
        "Linux package manager conflict or broken dependency state",
        IssueCategory.UPDATE_DRIVER,
        ("apt", "dnf", "pacman", "dpkg", "broken package", "dependency problem", "held packages"),
        ("linux_package_error", "update_failure_phase", "update_timeline"),
        (OSType.LINUX,),
    ),
    DiagnosisDefinition(
        "overheating_thermal_throttle",
        "Thermal throttling or cooling-path hardware issue",
        IssueCategory.HARDWARE,
        ("overheat", "fan", "hot", "thermal", "throttle", "temperature", "thermal shutdown"),
        ("thermal_signal", "load_trigger", "performance_thermal_correlation"),
    ),
    DiagnosisDefinition(
        "no_display_gpu_or_ram_fault",
        "No display due to GPU, RAM, or board-level startup fault",
        IssueCategory.HARDWARE,
        ("no display", "black screen", "beep", "no signal", "monitor no input", "led blink"),
        ("logo_visibility", "post_code", "external_display_behavior", "external_display_boot"),
    ),
    DiagnosisDefinition(
        "gpu_display_driver_timeout",
        "GPU/display driver timeout or compatibility mismatch",
        IssueCategory.UPDATE_DRIVER,
        ("display driver", "tdr", "screen flicker", "black screen after login", "gpu update", "video scheduler"),
        ("driver_timeline", "external_display_behavior", "windows_failure_stage"),
    ),
    DiagnosisDefinition(
        "random_restart_power_or_driver_instability",
        "Random restart from power instability or unstable driver",
        IssueCategory.HARDWARE,
        ("random restart", "restarts randomly", "shutdown", "power", "reboot", "unexpected restart"),
        ("power_instability", "driver_timeline", "power_source_dependency", "load_trigger"),
    ),
    DiagnosisDefinition(
        "memory_instability_fault",
        "Memory instability or RAM fault pattern",
        IssueCategory.HARDWARE,
        ("memory", "ram", "beep", "freeze", "memtest", "new ram"),
        ("post_code", "recent_hardware_change", "power_instability"),
    ),
    DiagnosisDefinition(
        "wifi_adapter_or_stack_issue",
        "Wi-Fi adapter, driver, or network stack instability",
        IssueCategory.NETWORK,
        ("wifi", "wi-fi", "network", "adapter", "internet", "disconnect", "network manager"),
        ("network_scope", "adapter_change", "dns_vs_link_layer", "resume_related_network_drop"),
    ),
    DiagnosisDefinition(
        "network_dns_stack_corruption",
        "DNS resolver or network stack corruption",
        IssueCategory.NETWORK,
        ("dns", "cannot resolve", "connected no internet", "flush dns", "name resolution"),
        ("dns_vs_link_layer", "router_dependency", "network_scope"),
    ),
    DiagnosisDefinition(
        "storage_capacity_or_disk_health_issue",
        "Storage saturation or disk-health degradation",
        IssueCategory.STORAGE,
        ("disk full", "storage", "i/o", "slow disk", "ssd", "hdd", "smart", "read write"),
        ("disk_capacity_health", "io_freeze", "smart_or_fs_warning"),
    ),
    DiagnosisDefinition(
        "disk_io_corruption_after_power_loss",
        "Disk I/O corruption pattern following abrupt power loss",
        IssueCategory.STORAGE,
        ("power loss", "file system", "corrupt", "chkdsk", "mount failed", "fsck"),
        ("power_loss_before_io_issue", "io_freeze", "smart_or_fs_warning"),
    ),
    DiagnosisDefinition(
        "insufficient_evidence_unknown",
        "Insufficient evidence for confident root cause",
        IssueCategory.UNKNOWN,
        ("unknown", "unclear", "not sure"),
    ),
)


DIAGNOSIS_BY_ID: Dict[str, DiagnosisDefinition] = {
    item.diagnosis_id: item for item in DIAGNOSIS_CATALOG
}

ERROR_CODE_HINTS: Dict[str, Tuple[str, ...]] = {
    "windows_update_install_failure": (
        "0x800f",
        "0x8024",
        "0xc190",
        "servicing stack",
        "cbs.log",
        "windows update error",
    ),
    "windows_driver_regression": (
        "driver_irql",
        "video_tdr",
        "dpc_watchdog",
        "code 43",
        "nvlddmkm",
        "amdkmdag",
    ),
    "macos_update_recovery_issue": ("kernel panic", "panic(cpu", "bridgeos", "software update failed"),
    "linux_package_manager_conflict": ("dpkg", "apt --fix-broken", "dependency problems", "conflicts"),
    "linux_service_dependency_failure": ("failed with result", "dependency failed", "unit entered failed state"),
    "network_dns_stack_corruption": ("dns_probe_finished", "name resolution", "dns server not responding"),
}


CATEGORY_NEGATIVE_SIGNALS: Dict[IssueCategory, Tuple[str, ...]] = {
    IssueCategory.UPDATE_DRIVER: ("update_timeline", "driver_timeline", "timeline_correlation"),
    IssueCategory.HARDWARE: (
        "thermal_signal",
        "load_trigger",
        "power_instability",
        "recent_hardware_change",
    ),
    IssueCategory.NETWORK: ("network_scope", "adapter_change", "dns_vs_link_layer"),
    IssueCategory.STORAGE: ("disk_capacity_health", "io_freeze", "smart_or_fs_warning"),
}


STOPWORDS = {
    "a",
    "after",
    "and",
    "or",
    "the",
    "to",
    "of",
    "with",
    "within",
    "issue",
    "problem",
}


class DiagnosisEngineAgent:
    """Ranks probable root causes with deterministic, conservative scoring."""

    def __init__(
        self,
        knowledge: KnowledgeBase,
        specialists: List[BaseSpecialistAgent],
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.specialists = specialists
        self.llm_provider = llm_provider
        self._known_ids = set(DIAGNOSIS_BY_ID)

    def diagnose(self, session: TroubleshootingSession) -> List[DiagnosisCandidate]:
        text_blob = self._build_text_blob(session)
        effective_os = self._effective_os(session)

        scores: Dict[str, float] = {}
        support_map: Dict[str, List[str]] = {}
        conflict_map: Dict[str, List[str]] = {}

        for definition in DIAGNOSIS_CATALOG:
            diagnosis_id = definition.diagnosis_id
            scores[diagnosis_id] = 0.04
            support_map[diagnosis_id] = []
            conflict_map[diagnosis_id] = []

            keyword_hits = [kw for kw in definition.keywords if kw in text_blob]
            matched_signals = [sig for sig in definition.expected_signals if sig in session.evidence]
            negative_signals = self._negative_expected_signals(session, definition.expected_signals)

            scores[diagnosis_id] += min(0.42, 0.08 * len(keyword_hits))
            scores[diagnosis_id] += min(0.34, 0.065 * len(matched_signals))
            scores[diagnosis_id] -= min(0.24, 0.09 * len(negative_signals))

            if session.triage:
                if definition.category == session.triage.category:
                    scores[diagnosis_id] += 0.18
                elif definition.category != IssueCategory.UNKNOWN:
                    scores[diagnosis_id] -= 0.025

            if definition.os_scope:
                if effective_os in definition.os_scope:
                    scores[diagnosis_id] += 0.08
                elif effective_os != OSType.UNKNOWN:
                    scores[diagnosis_id] -= 0.16
                    conflict_map[diagnosis_id].append(
                        f"OS scope mismatch: expected {self._os_label(definition.os_scope)}, observed {effective_os.value}."
                    )

            for keyword in keyword_hits[:5]:
                support_map[diagnosis_id].append(f"Matched keyword: {keyword}")
            for signal_name in matched_signals[:5]:
                value = session.evidence.get(signal_name, "")
                support_map[diagnosis_id].append(
                    f"Evidence signal present: {signal_name}={value}"
                )
            for signal_name in negative_signals[:3]:
                conflict_map[diagnosis_id].append(
                    f"Evidence signal is negative for this cause: {signal_name}"
                )

        self._apply_mapping_boosts(text_blob, scores, support_map)
        self._apply_decision_tree_boosts(session, scores, support_map)
        self._apply_error_code_boosts(text_blob, scores, support_map)
        self._apply_metadata_cues(session, scores, support_map, conflict_map)
        self._apply_online_insight_boosts(session, scores, support_map)
        self._apply_specialist_signals(session, scores, support_map, conflict_map)
        self._apply_contradiction_penalties(session, scores, conflict_map)
        self._apply_sparse_evidence_fallback(session, scores, support_map)

        ranked = self._rank(scores)
        top_score = ranked[0][1] if ranked else 0.01

        output: List[DiagnosisCandidate] = []
        for diagnosis_id, score in ranked:
            definition = DIAGNOSIS_BY_ID.get(diagnosis_id)
            if not definition:
                continue
            output.append(
                DiagnosisCandidate(
                    diagnosis_id=diagnosis_id,
                    title=definition.title,
                    confidence=self._calibrate_confidence(
                        raw_score=score,
                        top_score=top_score,
                        evidence_count=len(session.evidence),
                        has_conflict=bool(conflict_map.get(diagnosis_id)),
                    ),
                    category=definition.category,
                    supporting_evidence=self._dedupe(support_map.get(diagnosis_id, []))[:8],
                    conflicting_evidence=self._dedupe(conflict_map.get(diagnosis_id, []))[:6],
                )
            )
            if len(output) == 3:
                break

        return output

    def _apply_mapping_boosts(
        self,
        text_blob: str,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
    ) -> None:
        mapping_payload = self.knowledge.mappings.get("symptom-to-diagnosis.yaml") or {}
        table = mapping_payload.get("mapping", {}) if isinstance(mapping_payload, dict) else {}
        if not isinstance(table, dict):
            return

        for symptom_key, diagnosis_ids in table.items():
            if not isinstance(diagnosis_ids, list) or not self._symptom_matches(symptom_key, text_blob):
                continue
            for diagnosis_id in diagnosis_ids:
                if diagnosis_id not in self._known_ids:
                    continue
                scores[diagnosis_id] += 0.22
                support_map[diagnosis_id].append(f"Mapped symptom pattern: {symptom_key}")

    def _apply_decision_tree_boosts(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
    ) -> None:
        for tree_name, tree in self.knowledge.decision_trees.items():
            if not isinstance(tree, dict) or not self._tree_relevant(session, tree_name, tree):
                continue
            diagnosis_id = self._traverse_tree(session, tree)
            if diagnosis_id not in self._known_ids:
                continue
            scores[diagnosis_id] += 0.24
            support_map[diagnosis_id].append(
                f"Decision tree path matched: {tree.get('tree_id', tree_name)}"
            )

    def _apply_error_code_boosts(
        self,
        text_blob: str,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
    ) -> None:
        for diagnosis_id, patterns in ERROR_CODE_HINTS.items():
            if diagnosis_id not in self._known_ids:
                continue
            for pattern in patterns:
                if pattern in text_blob:
                    scores[diagnosis_id] += 0.14
                    support_map[diagnosis_id].append(f"Error/signature hint matched: {pattern}")

        windows_hex_codes = re.findall(r"0x[0-9a-f]{6,8}", text_blob)
        if windows_hex_codes:
            scores["windows_update_install_failure"] += 0.16
            support_map["windows_update_install_failure"].append(
                f"Detected Windows-style error code: {windows_hex_codes[0]}"
            )

    def _apply_metadata_cues(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
        conflict_map: Dict[str, List[str]],
    ) -> None:
        if session.metadata.recent_update:
            for diagnosis_id in (
                "windows_update_install_failure",
                "windows_driver_regression",
                "macos_update_recovery_issue",
                "linux_package_manager_conflict",
            ):
                scores[diagnosis_id] += 0.055
                support_map[diagnosis_id].append("Metadata cue: recent update present.")

        if session.metadata.recent_driver_change:
            for diagnosis_id in ("windows_driver_regression", "gpu_display_driver_timeout"):
                scores[diagnosis_id] += 0.08
                support_map[diagnosis_id].append("Metadata cue: recent driver change present.")

        if session.metadata.overheating_symptoms:
            scores["overheating_thermal_throttle"] += 0.1
            support_map["overheating_thermal_throttle"].append(
                "Metadata cue: overheating symptoms provided."
            )

        if session.metadata.storage_symptoms:
            scores["storage_capacity_or_disk_health_issue"] += 0.08
            support_map["storage_capacity_or_disk_health_issue"].append(
                "Metadata cue: storage symptoms provided."
            )

        if session.metadata.boot_status:
            boot_status = session.metadata.boot_status.lower()
            if any(marker in boot_status for marker in ("loop", "no display", "black screen", "repair")):
                for diagnosis_id in ("windows_boot_loop_firmware", "no_display_gpu_or_ram_fault"):
                    scores[diagnosis_id] += 0.08
                    support_map[diagnosis_id].append("Metadata cue: boot status matches startup failure.")

        hazard = " ".join(
            [
                session.evidence.get("hazard_signal", ""),
                session.evidence.get("electrical_hazard_signal", ""),
            ]
        ).lower()
        if any(marker in hazard for marker in ("yes", "smell", "sparks", "swelling", "burn")):
            for diagnosis_id in DIAGNOSIS_BY_ID:
                if DIAGNOSIS_BY_ID[diagnosis_id].category not in {IssueCategory.HARDWARE, IssueCategory.UNKNOWN}:
                    scores[diagnosis_id] -= 0.06
                    conflict_map[diagnosis_id].append(
                        "Hazard signal favors hardware escalation over software remediation."
                    )
            scores["overheating_thermal_throttle"] += 0.12
            support_map["overheating_thermal_throttle"].append("Safety hazard signal reported.")

    def _apply_online_insight_boosts(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
    ) -> None:
        for insight in session.online_insights[:6]:
            insight_text = f"{insight.title} {insight.summary}".lower()
            relevance = min(1.0, max(0.0, insight.relevance))
            for diagnosis_id, definition in DIAGNOSIS_BY_ID.items():
                if diagnosis_id not in scores:
                    continue
                if any(keyword in insight_text for keyword in definition.keywords[:6]):
                    boost = 0.035 + (0.055 * relevance)
                    scores[diagnosis_id] += boost
                    support_map[diagnosis_id].append(f"Online insight support: {insight.title}")

    def _apply_specialist_signals(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
        conflict_map: Dict[str, List[str]],
    ) -> None:
        for specialist in self.specialists:
            signal = specialist.analyze(session)
            for diagnosis_id, boost in signal.diagnosis_boosts.items():
                if diagnosis_id not in self._known_ids:
                    continue
                scores[diagnosis_id] += boost
                if signal.supporting_evidence:
                    support_map[diagnosis_id].extend(signal.supporting_evidence)
                if signal.conflicting_evidence:
                    conflict_map[diagnosis_id].extend(signal.conflicting_evidence)

    def _apply_contradiction_penalties(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        conflict_map: Dict[str, List[str]],
    ) -> None:
        for definition in DIAGNOSIS_CATALOG:
            negative_keys = CATEGORY_NEGATIVE_SIGNALS.get(definition.category, ())
            negative_count = len(self._negative_expected_signals(session, negative_keys))
            if negative_count:
                scores[definition.diagnosis_id] -= min(0.18, 0.07 * negative_count)
                conflict_map[definition.diagnosis_id].append(
                    f"Negative category evidence count: {negative_count}"
                )

    def _apply_sparse_evidence_fallback(
        self,
        session: TroubleshootingSession,
        scores: Dict[str, float],
        support_map: Dict[str, List[str]],
    ) -> None:
        evidence_count = len(session.evidence)
        best_specific = max(
            score
            for diagnosis_id, score in scores.items()
            if diagnosis_id != "insufficient_evidence_unknown"
        )

        if evidence_count < 2 and best_specific < 0.55:
            scores["insufficient_evidence_unknown"] += 0.36
            support_map["insufficient_evidence_unknown"].append(
                "Evidence set is sparse; confidence remains conservative."
            )
        else:
            scores["insufficient_evidence_unknown"] = max(
                0.01,
                scores.get("insufficient_evidence_unknown", 0.0) - 0.16,
            )

    def _rank(self, scores: Dict[str, float]) -> List[Tuple[str, float]]:
        clean_scores = {
            diagnosis_id: max(0.01, score)
            for diagnosis_id, score in scores.items()
            if diagnosis_id in self._known_ids
        }
        return sorted(clean_scores.items(), key=lambda item: item[1], reverse=True)

    @staticmethod
    def _calibrate_confidence(
        raw_score: float,
        top_score: float,
        evidence_count: int,
        has_conflict: bool,
    ) -> float:
        relative = raw_score / max(top_score, 0.01)
        magnitude = min(1.0, raw_score / 1.55)
        evidence_factor = min(1.0, evidence_count / 6.0)
        confidence = (0.34 * relative) + (0.46 * magnitude) + (0.20 * evidence_factor)
        if has_conflict:
            confidence -= 0.055
        return round(max(0.08, min(0.94, confidence)), 4)

    def _traverse_tree(self, session: TroubleshootingSession, tree: Dict[str, Any]) -> Optional[str]:
        current = tree.get("root")
        nodes = tree.get("nodes", {})
        visited: set[str] = set()

        for _ in range(6):
            if not isinstance(current, dict):
                return self._normalize_diagnosis_ref(current)

            node_id = str(current.get("id", ""))
            if node_id in visited:
                return None
            if node_id:
                visited.add(node_id)

            answer_state = self._answer_for_tree_question(session, str(current.get("question", "")))
            if answer_state not in {"affirmative", "negative"}:
                return None

            branch = self._branch_value(current, answer_state == "affirmative")
            diagnosis_id = self._normalize_diagnosis_ref(branch)
            if diagnosis_id:
                return diagnosis_id

            if isinstance(branch, str) and isinstance(nodes, dict):
                current = nodes.get(branch)
                continue
            return None

        return None

    @staticmethod
    def _branch_value(node: Dict[str, Any], affirmative: bool) -> Any:
        candidates: Sequence[Any]
        if affirmative:
            candidates = ("yes", "true", True)
        else:
            candidates = ("no", "false", False)

        for key in candidates:
            if key in node:
                return node[key]
        for key, value in node.items():
            if str(key).strip().lower() in {str(item).lower() for item in candidates}:
                return value
        return None

    @staticmethod
    def _normalize_diagnosis_ref(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        if value.startswith("diagnosis_"):
            return value.removeprefix("diagnosis_")
        if value in DIAGNOSIS_BY_ID:
            return value
        return None

    def _tree_relevant(
        self,
        session: TroubleshootingSession,
        tree_name: str,
        tree: Dict[str, Any],
    ) -> bool:
        text = f"{tree_name} {tree.get('tree_id', '')}".lower()
        category = session.triage.category if session.triage else IssueCategory.UNKNOWN
        if category == IssueCategory.UPDATE_DRIVER and any(key in text for key in ("update", "driver")):
            return True
        if category == IssueCategory.BIOS_BOOT and any(key in text for key in ("boot", "bios")):
            return True
        if category in {IssueCategory.NETWORK, IssueCategory.STORAGE} and "network_storage" in text:
            return True
        if category == IssueCategory.PERFORMANCE and "performance" in text:
            return True
        return False

    def _answer_for_tree_question(self, session: TroubleshootingSession, question: str) -> str:
        question_tokens = set(self._meaningful_tokens(question))
        best_state = "unknown"
        best_overlap = 0

        evidence_labels = {
            "update_timeline": "symptoms begin within 48 hours update driver installation",
            "driver_timeline": "driver installed updated",
            "safe_mode_behavior": "safe mode reduce remove issue",
            "rollback_effect": "rollback uninstall update improve stability",
            "logo_visibility": "manufacturer logo before restart",
            "post_code": "beep codes motherboard led error patterns",
            "firmware_change": "bios uefi settings changed",
            "network_scope": "internet dropouts inability connect wifi wired",
            "disk_capacity_health": "disk full file operations freeze",
            "resource_pressure": "cpu memory usage consistently high",
        }

        for key, answer in session.evidence.items():
            state = classify_evidence_state(answer)
            if state == "unknown":
                continue
            label = evidence_labels.get(key, key.replace("_", " "))
            overlap = len(question_tokens.intersection(self._meaningful_tokens(label)))
            if overlap > best_overlap:
                best_overlap = overlap
                best_state = state

        for qa in session.qa_history:
            state = classify_evidence_state(qa.answer)
            if state == "unknown":
                continue
            overlap = len(question_tokens.intersection(self._meaningful_tokens(qa.question)))
            if overlap > best_overlap:
                best_overlap = overlap
                best_state = state

        return best_state if best_overlap >= 2 else "unknown"

    def _build_text_blob(self, session: TroubleshootingSession) -> str:
        answers = " ".join(item.answer for item in session.qa_history)
        evidence = " ".join(session.evidence.values())
        meta = " ".join(
            [
                session.metadata.device_type or "",
                session.metadata.device_model or "",
                session.metadata.symptom_duration or "",
                session.metadata.recent_update or "",
                session.metadata.recent_driver_change or "",
                session.metadata.error_message or "",
                session.metadata.boot_status or "",
                session.metadata.overheating_symptoms or "",
                session.metadata.storage_symptoms or "",
            ]
        )
        insight_blob = " ".join(
            f"{item.title} {item.summary}" for item in session.online_insights[:5]
        )
        return f"{session.user_issue} {answers} {evidence} {meta} {insight_blob}".lower()

    @staticmethod
    def _effective_os(session: TroubleshootingSession) -> OSType:
        if session.metadata.os != OSType.UNKNOWN:
            return session.metadata.os
        if session.triage and session.triage.inferred_os != OSType.UNKNOWN:
            return session.triage.inferred_os
        return OSType.UNKNOWN

    @staticmethod
    def _negative_expected_signals(
        session: TroubleshootingSession,
        signals: Iterable[str],
    ) -> List[str]:
        negative: List[str] = []
        for signal in signals:
            value = session.evidence.get(signal)
            if value and classify_evidence_state(value) == "negative":
                negative.append(signal)
        return negative

    @staticmethod
    def _symptom_matches(symptom_key: str, text_blob: str) -> bool:
        phrase = symptom_key.replace("_", " ").lower()
        if phrase in text_blob:
            return True

        symptom_tokens = set(DiagnosisEngineAgent._meaningful_tokens(symptom_key))
        text_tokens = set(DiagnosisEngineAgent._meaningful_tokens(text_blob))
        if not symptom_tokens:
            return False
        overlap = symptom_tokens.intersection(text_tokens)
        required = min(len(symptom_tokens), max(2, int(len(symptom_tokens) * 0.55)))
        return len(overlap) >= required

    @staticmethod
    def _meaningful_tokens(text: str) -> List[str]:
        normalized: List[str] = []
        for token in tokenize(text.replace("_", " ")):
            if token in STOPWORDS:
                continue
            if len(token) > 3 and token.endswith("s"):
                token = token[:-1]
            normalized.append(token)
        return normalized

    @staticmethod
    def _os_label(os_scope: Tuple[OSType, ...]) -> str:
        return "/".join(item.value for item in os_scope)

    @staticmethod
    def _dedupe(values: List[str]) -> List[str]:
        seen: set[str] = set()
        output: List[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            output.append(value)
        return output
