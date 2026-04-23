"""Knowledge base loader for local troubleshooting assets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


DIAGNOSIS_ID_ALIASES = {
    "driver_regression": "windows_driver_regression",
    "bios_configuration_issue": "windows_boot_loop_firmware",
    "package_conflict": "linux_package_manager_conflict",
    "gpu_driver_regression": "gpu_display_driver_timeout",
}

PLAYBOOK_ID_ALIASES = {
    "bios_boot_recovery": "windows_boot_recovery",
    "linux_package_repair": "linux_package_manager_recovery",
}


def _load_structured_file(file_path: Path) -> Any:
    if not file_path.exists():
        return None
    if file_path.suffix.lower() == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))
    return yaml.safe_load(file_path.read_text(encoding="utf-8"))


def _load_directory_map(directory: Path) -> Dict[str, Any]:
    if not directory.exists():
        return {}

    payload: Dict[str, Any] = {}
    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        key = str(file_path.relative_to(directory)).replace("\\", "/")
        payload[key] = _load_structured_file(file_path)
    return payload


def _merge_local_with_fallback(local_value: Any, fallback_value: Any) -> Any:
    """Merge two payloads where local content is authoritative."""
    if local_value is None:
        return fallback_value
    if fallback_value is None:
        return local_value

    if isinstance(local_value, dict) and isinstance(fallback_value, dict):
        merged: Dict[str, Any] = {}
        keys = set(local_value.keys()).union(fallback_value.keys())
        for key in keys:
            if key in local_value and key in fallback_value:
                merged[key] = _merge_local_with_fallback(local_value[key], fallback_value[key])
            elif key in local_value:
                merged[key] = local_value[key]
            else:
                merged[key] = fallback_value[key]
        return merged

    if isinstance(local_value, list) and isinstance(fallback_value, list):
        return list(local_value)

    return local_value


def _merge_directory_maps_local_first(
    local_payload: Dict[str, Any],
    fallback_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge two directory maps with local-first precedence and additive fallback."""
    merged: Dict[str, Any] = {}
    all_keys = set(local_payload.keys()).union(fallback_payload.keys())
    for key in all_keys:
        if key in local_payload and key in fallback_payload:
            merged[key] = _merge_local_with_fallback(local_payload[key], fallback_payload[key])
        elif key in local_payload:
            merged[key] = local_payload[key]
        else:
            merged[key] = fallback_payload[key]
    return merged


def _canonical_diagnosis_id(diagnosis_id: str) -> str:
    return DIAGNOSIS_ID_ALIASES.get(diagnosis_id, diagnosis_id)


def _canonical_playbook_id(playbook_id: str) -> str:
    return PLAYBOOK_ID_ALIASES.get(playbook_id, playbook_id)


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    output: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


@dataclass(frozen=True)
class KnowledgeValidationReport:
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.warnings) == 0


@dataclass
class KnowledgeBase:
    decision_trees: Dict[str, Any] = field(default_factory=dict)
    playbooks: Dict[str, Any] = field(default_factory=dict)
    command_catalog: Dict[str, Any] = field(default_factory=dict)
    hardware_fault_matrix: Dict[str, Any] = field(default_factory=dict)
    mappings: Dict[str, Any] = field(default_factory=dict)
    taxonomies: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, knowledge_dir: Path, foundry_dir: Optional[Path] = None) -> "KnowledgeBase":
        decision_trees = _load_directory_map(knowledge_dir / "decision_trees")
        playbooks = _load_directory_map(knowledge_dir / "troubleshooting_playbooks")
        command_catalog = _load_directory_map(knowledge_dir / "command_catalog")
        hardware_fault_matrix = _load_directory_map(knowledge_dir / "hardware_fault_matrix")

        local_mapping_dir = knowledge_dir / "mappings"
        local_taxonomy_dir = knowledge_dir / "taxonomies"
        local_mappings = _load_directory_map(local_mapping_dir)
        local_taxonomies = _load_directory_map(local_taxonomy_dir)

        foundry_mappings: Dict[str, Any] = {}
        foundry_taxonomies: Dict[str, Any] = {}

        if foundry_dir and foundry_dir.exists():
            foundry_assets = foundry_dir / "assets"
            foundry_mappings = _load_directory_map(foundry_assets / "mappings")
            foundry_taxonomies = _load_directory_map(foundry_assets / "taxonomies")

        mappings = _merge_directory_maps_local_first(local_mappings, foundry_mappings)
        taxonomies = _merge_directory_maps_local_first(local_taxonomies, foundry_taxonomies)

        return cls(
            decision_trees=decision_trees,
            playbooks=playbooks,
            command_catalog=command_catalog,
            hardware_fault_matrix=hardware_fault_matrix,
            mappings=mappings,
            taxonomies=taxonomies,
        )

    def get_issue_categories(self) -> List[str]:
        taxonomy = (
            self.taxonomies.get("issue_taxonomy.yaml")
            or self.taxonomies.get("issue-taxonomy.yaml")
            or {}
        )
        return taxonomy.get("issues", []) if isinstance(taxonomy, dict) else []

    def map_symptom_to_diagnoses(self, symptom_key: str) -> List[str]:
        mapping = self.mappings.get("symptom-to-diagnosis.yaml") or {}
        table = mapping.get("mapping", {}) if isinstance(mapping, dict) else {}
        values = table.get(symptom_key, [])
        if not isinstance(values, list):
            return []
        return _dedupe_preserve_order(
            [_canonical_diagnosis_id(str(value)) for value in values if isinstance(value, str)]
        )

    def map_diagnosis_to_playbook(self, diagnosis_id: str) -> str:
        mapping = self.mappings.get("diagnosis-to-playbook.yaml") or {}
        table = mapping.get("mapping", {}) if isinstance(mapping, dict) else {}
        resolved_diagnosis_id = _canonical_diagnosis_id(diagnosis_id)
        playbook_id = str(table.get(resolved_diagnosis_id, resolved_diagnosis_id))
        return _canonical_playbook_id(playbook_id)

    def get_playbook_ids(self) -> Set[str]:
        ids: Set[str] = set()
        for payload in self.playbooks.values():
            if isinstance(payload, dict) and isinstance(payload.get("playbook_id"), str):
                ids.add(payload["playbook_id"])
        return ids

    def get_playbook(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        resolved_playbook_id = _canonical_playbook_id(playbook_id)
        for payload in self.playbooks.values():
            if not isinstance(payload, dict):
                continue
            if payload.get("playbook_id") == resolved_playbook_id:
                return payload
        return None

    def validate_integrity(self, diagnosis_ids: Set[str]) -> KnowledgeValidationReport:
        warnings: List[str] = []

        playbook_ids = self.get_playbook_ids()

        diagnosis_mapping = self.mappings.get("diagnosis-to-playbook.yaml") or {}
        diagnosis_table = diagnosis_mapping.get("mapping", {}) if isinstance(diagnosis_mapping, dict) else {}
        if not isinstance(diagnosis_table, dict):
            diagnosis_table = {}

        mapped_diagnosis_ids = {_canonical_diagnosis_id(str(key)) for key in diagnosis_table.keys()}
        unknown_mapping_ids = sorted(mapped_diagnosis_ids - diagnosis_ids)
        for diagnosis_id in unknown_mapping_ids:
            warnings.append(
                f"Unknown diagnosis id in diagnosis-to-playbook mapping: {diagnosis_id}"
            )

        missing_mapping_ids = sorted(diagnosis_ids - mapped_diagnosis_ids)
        for diagnosis_id in missing_mapping_ids:
            warnings.append(
                f"Diagnosis id missing in diagnosis-to-playbook mapping: {diagnosis_id}"
            )

        for diagnosis_id, playbook_id in diagnosis_table.items():
            if not isinstance(playbook_id, str):
                warnings.append(
                    f"Invalid playbook reference type for diagnosis {diagnosis_id}: {type(playbook_id).__name__}"
                )
                continue
            if _canonical_playbook_id(playbook_id) not in playbook_ids:
                warnings.append(
                    f"Mapped playbook not found for diagnosis {diagnosis_id}: {playbook_id}"
                )

        symptom_mapping = self.mappings.get("symptom-to-diagnosis.yaml") or {}
        symptom_table = symptom_mapping.get("mapping", {}) if isinstance(symptom_mapping, dict) else {}
        if isinstance(symptom_table, dict):
            for symptom_key, mapped in symptom_table.items():
                if not isinstance(mapped, list):
                    warnings.append(
                        f"Invalid symptom-to-diagnosis mapping format for {symptom_key}; expected list."
                    )
                    continue
                for diagnosis_id in mapped:
                    if _canonical_diagnosis_id(str(diagnosis_id)) not in diagnosis_ids:
                        warnings.append(
                            f"Invalid diagnosis reference in symptom mapping {symptom_key}: {diagnosis_id}"
                        )

        referenced_playbooks = {
            value for value in diagnosis_table.values() if isinstance(value, str)
        }
        unmapped_playbooks = sorted(playbook_ids - referenced_playbooks)
        for playbook_id in unmapped_playbooks:
            warnings.append(
                f"Unmapped playbook detected (no diagnosis points to it): {playbook_id}"
            )

        return KnowledgeValidationReport(warnings=sorted(set(warnings)))

    def get_command_risk(self, os_name: str, command: str) -> str:
        target_file = f"{os_name.lower()}.yaml"
        payload = self.command_catalog.get(target_file)
        if not isinstance(payload, dict):
            return "medium"
        entries = payload.get("commands", [])
        for item in entries:
            if not isinstance(item, dict):
                continue
            if item.get("command") == command:
                return str(item.get("risk", "medium"))
        return "medium"
