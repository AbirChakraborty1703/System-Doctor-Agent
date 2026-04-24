from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.shared_utils.config import get_config
from packages.shared_utils.knowledge_loader import _load_directory_map


def test_config_parsing_falls_back_for_invalid_env(monkeypatch) -> None:
    monkeypatch.setenv("MAX_QUESTIONS", "not-an-int")
    monkeypatch.setenv("MIN_CONFIDENCE_TO_STOP_QUESTIONS", "bad-float")
    monkeypatch.setenv("MAX_VERIFICATION_LOOPS", "-99")
    monkeypatch.setenv("ONLINE_SEARCH_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("ONLINE_SEARCH_MAX_RESULTS", "999")

    get_config.cache_clear()
    config = get_config()

    assert config.max_questions == 6
    assert config.min_confidence_to_stop_questions == 0.72
    assert config.max_verification_loops == 1
    assert config.online_search_timeout_seconds == 1
    assert config.online_search_max_results == 20



def test_directory_loader_skips_malformed_structured_file(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    malformed = knowledge_dir / "bad.yaml"
    malformed.write_text("mapping: [oops", encoding="utf-8")

    valid = knowledge_dir / "good.yaml"
    valid.write_text("mapping:\n  key: value\n", encoding="utf-8")

    payload = _load_directory_map(knowledge_dir)

    assert "good.yaml" in payload
    assert payload["good.yaml"]["mapping"]["key"] == "value"
    assert "bad.yaml" not in payload



def test_api_rejects_blank_issue_payload() -> None:
    client = TestClient(app)
    response = client.post("/sessions", json={"issue": "   ", "metadata": {}})
    assert response.status_code == 422
    assert "Issue must not be blank" in response.text
