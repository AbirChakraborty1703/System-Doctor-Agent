from pathlib import Path

from agents.diagnosis_engine.diagnosis_engine_agent import DIAGNOSIS_BY_ID
from packages.shared_utils.knowledge_loader import KnowledgeBase


def test_issue_taxonomy_uses_underscore_filename() -> None:
    kb = KnowledgeBase.load(
        knowledge_dir=Path("knowledge"),
        foundry_dir=Path(".foundry"),
    )

    categories = kb.get_issue_categories()
    assert "hardware" in categories
    assert "os_specific" in categories
    assert len(categories) >= 8


def test_local_symptom_mapping_takes_precedence_over_foundry() -> None:
    kb = KnowledgeBase.load(
        knowledge_dir=Path("knowledge"),
        foundry_dir=Path(".foundry"),
    )

    mapping = kb.mappings["symptom-to-diagnosis.yaml"]["mapping"]
    assert mapping["random_restart_after_update"] == [
        "windows_driver_regression",
        "random_restart_power_or_driver_instability",
        "windows_update_install_failure",
    ]
    assert "driver_regression" not in mapping["random_restart_after_update"]


def test_legacy_foundry_aliases_are_normalized() -> None:
    kb = KnowledgeBase.load(
        knowledge_dir=Path("knowledge"),
        foundry_dir=Path(".foundry"),
    )

    assert kb.map_diagnosis_to_playbook("driver_regression") == "windows_driver_rollback"
    assert kb.map_diagnosis_to_playbook("bios_configuration_issue") == "windows_boot_recovery"
    assert kb.map_diagnosis_to_playbook("package_conflict") == "linux_package_manager_recovery"

    report = kb.validate_integrity(set(DIAGNOSIS_BY_ID))
    assert report.is_valid
