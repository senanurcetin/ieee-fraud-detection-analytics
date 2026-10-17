# Documentation

This directory contains **maintained project reference** and **dated research/release evidence**. For a short introduction and working commands, start with the [repository README](../README.md).

The product is a **historical IEEE-CIS analytics demonstration**, not live bank monitoring. Model scores are **uncalibrated rankings** unless a separately validated calibration artifact exists. A green CI run does not by itself establish source freshness or live production readiness.

## Start here

| Document | Purpose |
|---|---|
| [Release status and open gates](RELEASE_STATUS.md) | What has been tested, what remains blocked, and where to check current status |
| [Executive summary](executive_summary.md) | Business question, evidence and recommended analytical review strategy |
| [Dataset methodology](ieee_cis_dataset_methodology.md) | Source, `TransactionDT`, masked fields and interpretation constraints |
| [Architecture](architecture.md) | Offline pipeline, dbt layers and snapshot-serving model |
| [Data dictionary](data_dictionary.md) | Reporting and model field definitions |
| [Analytical hypotheses](analysis_hypotheses.md) | Research questions and segment findings |

## Engineering and development

- [Environment setup](environment_setup.md) — prerequisites, DuckDB/dbt configuration and credential handling.
- [Kaggle manual research workflow](KAGGLE_RESEARCH_RUNBOOK.md) — authorized full-data random-vs-time, temporal hygiene and calibration experiments with hash-only artifacts.
- [dbt project guide](dbt_project_guide.md) and [BigQuery/dbt lineage](bigquery_dbt_lineage.md) — transformation and reporting contracts.
- [Web application guide](../webapp/README.md) — API, nine-page report, snapshots and local serving.
- [Source code contribution workflow](../CONTRIBUTING.md) — PR review and reproducible tests.
- [Security policy](../SECURITY.md) — secret handling, reporting and supported use.
- [NEXUS official brand identity](BRAND_IDENTITY.md) — approved Drive source files, vector SHA checksums and dashboard/Studio usage.

## Research and model evidence

- [Modeling decisions](modeling_decisions.md) and [model validation evidence](model_validation_evidence.md) — chronological evaluation and scoring contracts.
- [Model results](model_results.md), [recomputed validation](model_validation_recomputed.md) and [model registry](model_registry.json) — historical metrics and supporting artifact metadata.
- [17 Oct full-source Kaggle split results](KAGGLE_FULL_SOURCE_VALIDATION_2026-10-17.md) — first verified 590,540-row real-data random vs chronological metrics and source digest.
- [Random vs. time-split reproduction](RANDOM_VS_TIME_SPLIT_REPRODUCTION.md), [temporal hygiene](TEMPORAL_HYGIENE_EXPERIMENT.md), [temporal calibration](TEMPORAL_CALIBRATION_EXPERIMENT.md) — experiment methodology and evidence limits.
- [Local TreeSHAP explanations](LOCAL_SHAP_EXPLANATIONS.md) and [offline drift monitoring](OFFLINE_DRIFT_MONITORING.md) — gated/offline analyses, not default public inference.
- [Business impact](banking_business_impact.md), [operational playbook](operational_playbook.md) and [regulatory context](regulatory_context.md) — capacity assumptions, analytical controls and governance context.

## Data lineage, audits and release controls

- [BigQuery discovery](BIGQUERY_SOURCE_DISCOVERY.md) and [15 Oct source verification](BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md) — dated metadata and partial source comparison.
- [Bounded BigQuery table parity](BIGQUERY_BOUNDED_SOURCE_PARITY.md) and [offline snapshot audit](SNAPSHOT_PARITY_AUDIT.md) — source validation tools with explicit boundaries.
- [Source revalidation (14 Oct)](bigquery_source_revalidation_2026-10-14.md) — retained historical evidence, not fresh source certification.
- [CI and research credentials](CI_AND_RESEARCH_CREDENTIALS.md), [security controls](SECURE_RELEASE_GATES.md) and [security review](dependency_security_review_2026-10-14.md) — credential/safety acceptance.
- [Docker release runbook](F08_LOCAL_RELEASE.md) and [public release attestation](PUBLIC_RELEASE_ATTESTATION.md) — local demo vs. real production SHA verification.
- [Evidence/provenance rail](F07_EVIDENCE_TRUST_RAIL.md), [analyst case review](F07_HISTORICAL_ANALYST_REVIEW.md) and [three-engine browser acceptance](F07_BROWSER_ACCEPTANCE.md) — NEXUS UI safety contracts.
- [Visual provenance](assets/production_screenshot_provenance_20261014.json) and [SEO/social preview](SEO_AND_SOCIAL_PREVIEW_GUIDE.md) — reviewed image dates and asset integrity.

## Historical records

The following are **date-specific evidence or acceptance snapshots**. Their PASS flags belong to the period described and must not be read as proof of today's complete release gates.

- [14 October readiness audit](nexus_fraud_release_readiness_2026-10-14.md)
- [Historical production validation](production_validation.md)
- [Historical QA acceptance checklist](qa_acceptance_checklist.md)
- [Analyst coverage and prior closure notes](professional_analysis_coverage.md) · [gap closure](data_analyst_gap_closure.md)
- [Analysis story](analysis_story.md) and [dashboard presentation guide](live_web_dashboard_guide.md)

For **current unresolved work**, use [GitHub Issues](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues), not historical backlogs. Do not edit old evidence dates to manufacture recency or delete reproducibility/security artifacts simply to shorten the repo.
