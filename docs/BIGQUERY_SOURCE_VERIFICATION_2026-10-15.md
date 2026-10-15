# BigQuery Fraud reporting source verification — 15 October 2026

## Verified source identity (metadata-only)

On 15 October 2026, the owner-authorized Windows environment contained an existing service-account JSON in Downloads. Its service-account project was `workintech-working`. Using `google.cloud.bigquery.Client.from_service_account_json`, **metadata and table rows only** were read. No credentials or service-account key contents were copied to GitHub or this document, and no SQL query, new job, export, table write or dbt rebuild was executed.

| Dataset (workintech-working) | Region | Observed objects |
| --- | --- | ---: |
| `fraud_project_raw` | US | 10 tables |
| `fraud_project_staging` | US | 2 views |
| `fraud_project_intermediate` | US | 2 tables |
| `fraud_project_mart` | US | 10 tables |
| `fraud_project_reporting` | US | 24 tables |
| Additional unused BI-oriented dataset | US | 0 objects |

`data-analiz-490513` contained no matching Fraud datasets. The earlier failure to discover the source was a **wrong GCP project**, not proof that the reporting source was missing.

## Table and snapshot evidence

- `fraud_project_raw.train_transaction`: **590,540** table rows (last modified 2026-09-01 UTC).
- `fraud_project_raw.train_identity`: **144,233** rows.
- `fraud_project_raw.validation_predictions`: **118,108** rows.
- `fraud_project_reporting.fact_train_transactions`: **590,540** rows.
- `fraud_project_reporting.rpt_executive_kpis`: **1** row, last modified 2026-09-11T02:02:11Z.
- Snapshot `webapp/snapshots/dashboard.json`: `meta.project_id=workintech-working`, `meta.dataset=fraud_project_reporting`, `meta.total_transactions=590540`, `meta.fraud_transactions=20663`, and historical `meta.refreshed_at=2026-09-10T19:41:45Z`.
- The current BigQuery executive KPI table returned **590,540 transactions and 20,663 fraud cases**; all **21 shared scalar fields** in its inspected first row matched the snapshot values at comparison precision.
- First-row comparisons also found no common-field differences for `product_risk`, `identity_risk`, `feature_importance`, and `validation_threshold_simulation`. This first-row result is **not** proof that all rows/metrics match.

## Historical metadata limitation

The snapshot records `table_count=27`, whereas **24 reporting tables** were observed by listing the current dataset on 15 October. The reporting objects were last modified after the snapshot's recorded refresh time, typically around 11 September. This can reflect schema evolution, and needs reconciliation; do **not** rewrite the historical timestamp, assert a new full snapshot refresh or claim that all 24 tables match solely on the basis of KPI/first-row checks.

## Extended row comparison (15 October 2026)

Using BigQuery `list_rows` (no SQL jobs), snapshot dictionaries were compared to the current reporting tables using shared field names and six-decimal float normalization. This is a **structural snapshot parity check**, not a refreshed dbt build.

**Matched without row differences:** `executive_kpis` (1), `product_risk` (5), `identity_risk` (2), `identity_product_coverage` (5), `amount_bands` (6), `daily_drift` (182), `time_amount_signals` (48), `payment_heatmap` (6), `email_domain_risk` (8), `validation_risk_bands` (4), `model_calibration` (10), `proxy_signal_risk` (6), `threshold_simulation` (16), `validation_threshold_simulation` (16), `segment_model_performance` (528), and `quality_contract` (6).

**Subset relation:** the snapshot's `feature_importance` includes 15 rows matching live report rows, while the current table contains 387; snapshot `model_risk_bands` has four rows versus eight in current table, of which one matched after normalization.

**Investigate before refresh:** `segment_watchlist` (20 of 20 rows differ on combined matching fields), `review_strategy` (3 of 4 differ), `report_narrative` (9 of 9 differ) and `report_readiness` (7 of 8 differ). Some differences may be precision, rendering or report-version changes; no explanation is assumed without a field-level diff.

**No same-named current report table:** `payment_email_matrix`, `data_quality`, `proxy_product_matrix`, `proxy_cross_matrix`, `niche_drilldown`. Their snapshot names may correspond to compositions of other report tables, but this was not validated.

Accordingly, issue #9 is **not yet closed**; static IEEE-CIS source rows and major KPI totals are corroborated, but full report freshness is not established.

## Closure conditions for issue #9

1. Perform a deterministic all-row comparison for each dashboard-backed report table and record both schema and numeric differences. Decide whether a historical snapshot can be retained or needs regeneration.
2. If regeneration is required, first confirm the owner-approved project billing and dry-run query byte estimate; run dbt tests and reconcile outputs before publishing.
3. Publish the verified report with the real refresh time (or preserve the old historical one) and test the deployed dashboard.

The source **project and region** are now verified. **Full freshness acceptance** is still open.
