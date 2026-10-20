# Release status and acceptance gates

**Documentation reviewed: 20 October 2026.** This is a noncommercial historical research application. Evidence dates below belong to the actual runs; reviewing this page does not refresh source data or retrain a model.

## Verified delivery

[PR #44](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/44) merged on 19 October as `2c54bb3d6c090c36181162b31f402f3ea8bfdc44`. Its exact-main checks passed:

| Evidence | Result and scope |
|---|---|
| [Main CI](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39245073391) | Python tests, Ruff, compilation, dependency audit and dbt parse passed. Full-source dbt run/test was skipped, not certified. |
| [Container smoke](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39245073372) | Docker historical snapshot and local HTTP contract passed. |
| [Public production attestation](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39245073536) | Exact deployed Git SHA and public HTTPS historical-report contract passed on that revision. |
| Local Python suite, 19 October | 248 passed, exit 0; 8 dependency/SHAP warnings. Includes atomic imports, SQLite lifecycle and snapshot deletion-race regressions. |
| Local static/HTTP checks, 19 October | Ruff 0.4.10, JavaScript syntax, compileall, Markdown links, SEO/image provenance and pinned FastAPI 0.136.3 HTTP checks passed. |

These checks apply to the recorded revision. Subsequent code changes require their own checks. READY preview status alone never substitutes for production attestation.

## Historical data and model boundaries

The public dashboard serves **historical JSON snapshots**, built **10 September 2026** (`2026-09-10T19:41:45Z`). It does not perform live transaction monitoring. The published 500-estimator model score is **uncalibrated**, despite the historical source field name `predicted_fraud_probability`.

The [published model summary](model_validation_evidence.md) and [canonical 17 October research](research/KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md) describe different model contracts. Full-source F03 temporal hygiene and F04 calibration research passed; those results were not promoted into the dashboard. No automatic declines, real customer identification or measured prevented losses are claimed.

## Current acceptance matrix

| Area | State | Remaining work |
|---|---|---|
| Engineering / historical release | Recorded 19 October checks passed | Validate each subsequent revision; keep source timestamps unchanged |
| BigQuery source reconciliation | **OPEN**, [issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9) | Configure repository-scoped WIF/ADC and reconcile all 27 dashboard groups, including derived/filtered groups; 24 physical tables are not 27 verified groups |
| GitHub Kaggle access | Configured secret and [successful 17 October full-source run](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39063907895) | A stored secret alone does not establish its current validity |
| Local Kaggle access | Previous local listing returned 401 | A new credential was supplied for this task; fresh authentication has not yet been tested during this documentation-first stage |
| Kaggle notebook publication | **OPEN**, [issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8) | Authenticate, execute and read back the replacement notebook/public URL; the original unavailable notebook is not recovered |
| Research F03/F04 | **PASS for recorded research** | Retain source hashes, exact runs and methodological limits |
| Calibrated published-model promotion | **OPEN**, [issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20) | Match the exact base model/features, independent temporal validation and versioned probability contract |
| Browser acceptance | Prior dated evidence only | Playwright workflow is disabled at the owner's request; no current browser run is claimed |

The previous blanket statement that exact production SHA/HTTPS was unverified is superseded by the 19 October attestation. [Issue #29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29) also includes browser acceptance; its remaining scope must not be silently marked complete.

## Browser and cost policy

The owner instructed continued development without Playwright on 19 October. The existing `Historical Browser Acceptance` workflow was disabled before merging #44 to prevent automatic execution. Keep it disabled unless the owner changes that instruction. The 18 October Chromium/Studio run passed 16 tests; screenshots at 1440, 375 and 320 pixels are dated prior evidence, not a new cross-engine result.

No paid cloud query, dataset rebuild or commercial payment integration is part of this work. Public serving uses committed aggregates. Kaggle workflows are manual and upload aggregate metrics/source hashes only. Never expose credentials or redistribute competition CSVs. Do not re-enable the previous release-monitor automation by implication.

## Reproduction and source references

- [Development scope](DEVELOPMENT_PLAN.md), [architecture](architecture.md), [environment](environment_setup.md), [Kaggle runbook](runbooks/KAGGLE_RESEARCH_RUNBOOK.md).
- [BigQuery bounded parity](BIGQUERY_BOUNDED_SOURCE_PARITY.md), [15 October partial source evidence](BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md), [snapshot audit](SNAPSHOT_PARITY_AUDIT.md).
- [Local container release](F08_LOCAL_RELEASE.md), [public attestation method](PUBLIC_RELEASE_ATTESTATION.md).
- Approved NEXUS SVG rechecked against the owner's Drive pack: SHA-256 `143788fc114348b03bcef5285c134d63135bd7dbd908380e973596f743c9f45b` matches. See [brand provenance](BRAND_IDENTITY.md).

Archived checklists, old plans and screenshot dates are historical records. Use this page and exact-run GitHub evidence for current claims.
