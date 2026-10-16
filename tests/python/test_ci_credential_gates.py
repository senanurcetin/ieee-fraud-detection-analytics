"""Confirm full-data CI requires manual dispatch; do not inspect credentials."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_kaggle_secret_gating():
    config = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "KAGGLE_API_TOKEN:" in config
    assert '"$GITHUB_EVENT_NAME" != "workflow_dispatch"' in config
    assert 'echo "enabled=false" >> "$GITHUB_OUTPUT"' in config
    assert "Full IEEE-CIS data build: NOT RUN" in config
    assert "secrets.KAGGLE_KEY" in config
    assert "secrets.KAGGLE_USERNAME" in config
    assert "KGAT_" not in config
    assert "-----BEGIN PRIVATE KEY-----" not in config


def test_real_data_steps_are_not_ungated():
    config = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert config.count("if: steps.kaggle.outputs.enabled == 'true'") >= 4
    assert "if: steps.kaggle.outputs.enabled != 'true'" in config
