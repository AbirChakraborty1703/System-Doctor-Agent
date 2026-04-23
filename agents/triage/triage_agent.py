"""Initial issue classification logic for SystemDoctor AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from packages.schemas import DeviceMetadata, IssueCategory, OSType, Severity, TriageResult
from packages.shared_utils.text_utils import contains_any


@dataclass
class CategoryRule:
    category: IssueCategory
    keywords: List[str]


class TriageAgent:
    """Classifies issue category, severity, and inferred OS using deterministic rules."""

    def __init__(self) -> None:
        self._rules: List[CategoryRule] = [
            CategoryRule(IssueCategory.BIOS_BOOT, ["boot", "bios", "uefi", "post", "no display", "black screen"]),
            CategoryRule(IssueCategory.UPDATE_DRIVER, ["update", "driver", "patch", "after update", "rollback"]),
            CategoryRule(IssueCategory.HARDWARE, ["overheat", "fan", "noise", "ram", "gpu", "motherboard", "power"]),
            CategoryRule(IssueCategory.STORAGE, ["disk full", "storage", "ssd", "hdd", "i/o", "smart"]),
            CategoryRule(IssueCategory.NETWORK, ["wifi", "network", "internet", "lan", "adapter"]),
            CategoryRule(IssueCategory.PERFORMANCE, ["slow", "lag", "freeze", "stutter", "high cpu", "high memory"]),
            CategoryRule(IssueCategory.SOFTWARE, ["crash", "app", "service", "dependency", "exception", "error"]),
        ]

    def classify(self, issue_text: str, metadata: DeviceMetadata) -> TriageResult:
        text = issue_text.lower()
        inferred_os = self._infer_os(text, metadata)
        category, confidence = self._infer_category(text)

        if metadata.expected_category:
            try:
                hinted = IssueCategory(metadata.expected_category)
                if hinted != IssueCategory.UNKNOWN:
                    category = hinted
                    confidence = min(0.9, max(confidence, 0.6))
            except ValueError:
                pass

        severity = self._infer_severity(text)

        missing_fields = self._missing_fields(category, metadata)
        likely_domain = "hardware" if category in {
            IssueCategory.HARDWARE,
            IssueCategory.BIOS_BOOT,
            IssueCategory.STORAGE,
        } else "software"

        rationale = (
            f"Classified as {category.value} based on symptom keywords; "
            f"severity={severity.value}, inferred_os={inferred_os.value}."
        )

        return TriageResult(
            category=category,
            severity=severity,
            inferred_os=inferred_os,
            likely_domain=likely_domain,
            confidence=confidence,
            missing_fields=missing_fields,
            rationale=rationale,
        )

    def _infer_os(self, text: str, metadata: DeviceMetadata) -> OSType:
        if metadata.os != OSType.UNKNOWN:
            return metadata.os

        os_map: List[Tuple[OSType, List[str]]] = [
            (OSType.WINDOWS, ["windows", "blue screen", "event viewer", "bsod"]),
            (OSType.MACOS, ["macos", "mac", "kernel panic", "launchd"]),
            (OSType.LINUX, ["linux", "ubuntu", "debian", "fedora", "systemd"]),
        ]

        for os_type, markers in os_map:
            if contains_any(text, markers):
                return os_type
        return OSType.UNKNOWN

    def _infer_category(self, text: str) -> Tuple[IssueCategory, float]:
        score_map: Dict[IssueCategory, int] = {}
        for rule in self._rules:
            hits = sum(1 for keyword in rule.keywords if keyword in text)
            if hits:
                score_map[rule.category] = score_map.get(rule.category, 0) + hits

        if not score_map:
            return IssueCategory.SOFTWARE, 0.45

        ordered = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
        winner, score = ordered[0]
        total = sum(score_map.values())
        confidence = min(0.95, max(0.5, score / max(total, 1)))
        return winner, confidence

    def _infer_severity(self, text: str) -> Severity:
        if contains_any(text, ["won't boot", "cannot boot", "data loss", "burn", "smoke", "critical"]):
            return Severity.CRITICAL
        if contains_any(
            text,
            [
                "restart loop",
                "random restart",
                "restarts randomly",
                "kernel panic",
                "bsod",
                "no display",
                "unusable",
            ],
        ):
            return Severity.HIGH
        if contains_any(text, ["slow", "lag", "intermittent", "warning", "degraded"]):
            return Severity.MEDIUM
        return Severity.LOW

    def _missing_fields(self, category: IssueCategory, metadata: DeviceMetadata) -> List[str]:
        wanted_by_category: Dict[IssueCategory, List[str]] = {
            IssueCategory.BIOS_BOOT: ["boot_status", "error_message"],
            IssueCategory.UPDATE_DRIVER: ["recent_update", "recent_driver_change"],
            IssueCategory.HARDWARE: ["overheating_symptoms", "device_type"],
            IssueCategory.STORAGE: ["storage_symptoms", "error_message"],
            IssueCategory.NETWORK: ["error_message"],
        }

        required = wanted_by_category.get(category, ["error_message"]) + ["os"]
        missing: List[str] = []

        for field_name in required:
            if field_name == "os" and metadata.os == OSType.UNKNOWN:
                missing.append(field_name)
                continue
            if field_name != "os" and not getattr(metadata, field_name, None):
                missing.append(field_name)

        return sorted(set(missing))
