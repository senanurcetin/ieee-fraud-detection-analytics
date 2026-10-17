"""Container CI guard: verify runtime test cannot publish or access cloud."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_container_smoke_is_real_http_startup_not_claimed_from_unit_tests() -> None:
    text = (ROOT / ".github/workflows/container-smoke.yml").read_text(encoding="utf-8")
    assert "docker compose config --quiet" in text
    assert "docker compose build" in text
    assert "docker compose up -d --no-build" in text
    assert "http://127.0.0.1:8000/api/evidence-status" in text
    assert "python3 -m scripts.verify_snapshot_release" in text
    assert "docker compose down --volumes --remove-orphans" in text
    assert "if: always()" in text


def test_container_workflow_is_limited_to_historical_local_smoke() -> None:
    text = (ROOT / ".github/workflows/container-smoke.yml").read_text(encoding="utf-8")
    assert "permissions:" in text
    assert "contents: read" in text
    assert "timeout-minutes: 15" in text
    assert "workflow_dispatch:" in text
    assert "Live BigQuery/model production validation: NOT RUN" in text
    assert "Vercel production deployment: NOT RUN" in text
    assert "secrets." not in text
    assert "vercel deploy" not in text
    assert "dbt run" not in text
    assert "kaggle" not in text.lower()
