# Documentation

**Status: active noncommercial historical research, 20 October 2026.** Start with [release status](RELEASE_STATUS.md) for verified results and remaining gates. The [repository README](../README.md) provides the project overview and local quick start.

The dashboard serves historical aggregates built 10 September 2026. Its public model scores are uncalibrated rankings. Source freshness, model promotion and hosted release checks are distinct claims.

## Maintained reference

| Document | Purpose |
|---|---|
| [Executive summary](executive_summary.md) | Analytical question, historical observations and interpretation limits |
| [Architecture](architecture.md) | Offline serving, data layers, API authorization and research import boundaries |
| [Dataset methodology](ieee_cis_dataset_methodology.md) | Masked variables, relative time, source terms and cohort definitions |
| [Data dictionary](data_dictionary.md) | Reporting field definitions |
| [Published model evidence](model_validation_evidence.md) | One maintained model summary, metrics and validation limits |
| [Modeling decisions](modeling_decisions.md) | Historical implementation versus measured research alternatives |
| [Recomputed aggregate evidence](model_validation_recomputed.md) | Retained artifact-derived tables; not a new model run |
| [Analytical hypotheses](analysis_hypotheses.md) | Exploratory questions and observed segment patterns |
| [Business scenarios](banking_business_impact.md) | Explicit hypothetical costs and review capacity |
| [Analysis coverage](professional_analysis_coverage.md) | Questions mapped to dashboard evidence |
| [NEXUS identity](BRAND_IDENTITY.md) | Official Drive source and immutable artwork hashes |

## Research and operations

- [Research index](research/README.md): canonical measured results, reproduction methods and scope distinctions.
- [Notebook handoff](../notebooks/README.md): execution prerequisites and publication state.
- [Kaggle runbook](runbooks/KAGGLE_RESEARCH_RUNBOOK.md) and [credential modes](runbooks/CI_AND_RESEARCH_CREDENTIALS.md): explicit research execution without source redistribution.
- [Environment setup](environment_setup.md), [dbt guide](dbt_project_guide.md) and [BigQuery/dbt lineage](bigquery_dbt_lineage.md).
- [Web application guide](../webapp/README.md), [local release](F08_LOCAL_RELEASE.md) and [public HTTP attestation](PUBLIC_RELEASE_ATTESTATION.md).
- [20 October BigQuery validation](research/BIGQUERY_READ_ONLY_VALIDATION_2026-10-20.md), [bounded BigQuery parity](BIGQUERY_BOUNDED_SOURCE_PARITY.md), [source discovery](BIGQUERY_SOURCE_DISCOVERY.md), [15 October source evidence](BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md) and [snapshot audit](SNAPSHOT_PARITY_AUDIT.md).
- [Local TreeSHAP](LOCAL_SHAP_EXPLANATIONS.md), [offline drift](OFFLINE_DRIFT_MONITORING.md), [analyst policy](operational_playbook.md) and [governance context](regulatory_context.md).
- [Security policy](../SECURITY.md), [secret handling](security_and_secrets.md), [release controls](SECURE_RELEASE_GATES.md) and [contribution workflow](../CONTRIBUTING.md).
- [Evidence rail](F07_EVIDENCE_TRUST_RAIL.md), [historical case review](F07_HISTORICAL_ANALYST_REVIEW.md), [prior browser methodology](F07_BROWSER_ACCEPTANCE.md) and [SEO assets](SEO_AND_SOCIAL_PREVIEW_GUIDE.md). Playwright is disabled at the owner's request; previous browser evidence remains dated.
- [Development scope and folder map](DEVELOPMENT_PLAN.md).

## Folder policy

```text
docs/             maintained reference and current status
  research/       experiment methods and canonical measured results
  runbooks/       Kaggle execution and credential modes
  archive/        superseded plans and historical acceptance records
  assets/         approved logos, dated images and provenance
notebooks/        standalone analytical notebooks and publication handoff
```

The former duplicate `model_results.md` and `hiring-summary.md` were consolidated into the published model evidence and executive summary. Historical production/QA checklists and presentation guides are archived, not active acceptance gates. Their checked boxes and PASS values belong to the period described. Preserve scientific provenance and original timestamps; use [release status](RELEASE_STATUS.md) for current decisions.
