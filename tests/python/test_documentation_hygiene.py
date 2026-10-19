"""Repository-facing documentation integrity and safety-contract regression gates.

Uses only checked-in files, without network, model training or BigQuery access.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]

PUBLIC_ENTRYPOINTS = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "webapp/README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/RELEASE_STATUS.md",
    ROOT / "docs/architecture.md",
    ROOT / "docs/DEVELOPMENT_PLAN.md",
    ROOT / "docs/archive/nexus_fraud_release_readiness_2026-10-14.md",
    ROOT / "docs/archive/bigquery_source_revalidation_2026-10-14.md",
    ROOT / "docs/archive/KAGGLE_TEMPORAL_CALIBRATION_EVIDENCE_2026-10-17.md",
]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def test_entrypoint_document_links_resolve_without_network() -> None:
    broken: list[str] = []
    for path in PUBLIC_ENTRYPOINTS:
        assert path.is_file(), str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0]
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:", "data:")):
                continue
            relative_path = unquote(parsed.path)
            if not relative_path:
                continue
            destination = (path.parent / relative_path).resolve()
            if not destination.is_relative_to(ROOT.resolve()) or not destination.is_file():
                broken.append(f"{path.relative_to(ROOT)}: {target}")
    assert not broken, "Unresolved local Markdown targets:\n" + "\n".join(broken)


def test_obsolete_project_notes_are_not_in_active_tree() -> None:
    obsolete = [
        "docs/01_summary.md",
        "docs/02_tech_stack.md",
        "docs/03_analysis_hypotheses.md",
        "docs/04_ml_ideas.md",
        "docs/05_development_backlog.md",
        "docs/06_next_development_backlog.md",
        "docs/github_portfolio_checklist.md",
        "docs/data_analyst_gap_closure.md",
    ]
    assert all(not (ROOT / name).exists() for name in obsolete)
    assert (ROOT / "docs/analysis_hypotheses.md").is_file()


def test_start_pages_disclose_history_and_external_gates() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/RELEASE_STATUS.md").read_text(encoding="utf-8")
    assert len(readme.splitlines()) < 240
    assert "historical" in readme.lower()
    assert "uncalibrated" in readme
    assert "10 September 2026" in readme
    assert "docs/README.md" in readme and "docs/RELEASE_STATUS.md" in readme
    assert "issue #9" in release and "issue #20" in release
    assert "historical" in index.lower() and "dated" in index.lower()
    assert "active noncommercial" in readme.lower()
    assert "DEVELOPMENT_PLAN.md" in readme and "DEVELOPMENT_PLAN.md" in index


def test_public_contributor_and_security_guides_describe_actual_controls() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    assert "config/dbt/profiles.yml" in contributing
    assert "profiles/profiles.example.yml" not in contributing
    assert "dbt parse" in contributing
    assert "pip-audit -r requirements-dev.txt" in contributing
    assert "does not ignore" in security
    assert "rotate" in security
    assert "historical JSON snapshots" in architecture
    assert "not live BigQuery" in architecture


def test_dated_acceptance_documents_are_visibly_labeled_historical() -> None:
    for name in (
        "docs/production_validation.md",
        "docs/qa_acceptance_checklist.md",
        "docs/live_web_dashboard_guide.md",
        "webapp/README.md",
    ):
        body = (ROOT / name).read_text(encoding="utf-8")
        assert "snapshot" in body.lower() or "historical" in body.lower()
        assert "RELEASE_STATUS.md" in body
