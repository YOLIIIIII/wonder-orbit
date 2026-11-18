"""Integrity checker regression uses synthetic artifacts, not private live captures."""

import hashlib
import pytest
from test_learning_quality_evals import load

history = load("g_history_tests", "check_knowledge_g_history.py")


def test_history_detects_tampering_and_missing_artifacts(tmp_path):
    artifact = tmp_path / "raw.json"
    artifact.write_bytes(b"historical input/output/schema/config/ledger")
    manifest = {"files": {"raw.json": hashlib.sha256(artifact.read_bytes()).hexdigest()}}
    assert history.verify(tmp_path, manifest) == ["raw.json"]
    artifact.write_bytes(b"changed")
    with pytest.raises(ValueError, match="historical_artifact_changed"):
        history.verify(tmp_path, manifest)
    artifact.unlink()
    with pytest.raises(FileNotFoundError):
        history.verify(tmp_path, manifest)


def test_history_rejects_path_escape(tmp_path):
    with pytest.raises(ValueError, match="path_outside_project"):
        history.verify(tmp_path, {"files": {"../outside": "hash"}})
