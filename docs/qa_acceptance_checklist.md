# QA Acceptance Checklist

Final acceptance target: the live web dashboard is the only presentation layer.

## dbt and BigQuery

- [x] Production dbt build completed successfully.
- [x] Latest verified build result: `PASS=132 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=133`.
- [x] Project scope: 33 models, 99 data tests, 8 sources, 1 exposure.
- [x] dbt docs generation completed successfully.
- [x] Raw row counts reconcile to the Kaggle source files.
- [x] Reporting fact table reconciles to the training transaction source.
- [x] Risk-band completeness and monotonicity tests pass.
- [x] Threshold simulation monotonicity and precision-signal tests pass.
- [x] Segment watchlist business-rule tests pass.
- [x] Review strategy business-rule tests pass.
- [x] Web reporting contract test passes.

## Critical Row Counts

- [x] `fraud_project_raw.train_transaction`: 590,540 rows.
- [x] `fraud_project_raw.train_identity`: 144,233 rows.
- [x] `fraud_project_raw.test_transaction`: 506,691 rows.
- [x] `fraud_project_raw.test_identity`: 141,907 rows.
- [x] `fraud_project_staging.stg_transactions`: 590,540 rows.
- [x] `fraud_project_staging.stg_identity`: 144,233 rows.
- [x] `fraud_project_intermediate.int_features`: 590,540 rows.
- [x] `fraud_project_mart.mart_risk_band_stats`: 8 rows.
- [x] `fraud_project_reporting.fact_train_transactions`: 590,540 rows.
- [x] `fraud_project_reporting.rpt_segment_watchlist`: 20 rows.
- [x] `fraud_project_reporting.rpt_review_strategy`: 4 rows.
- [x] `fraud_project_reporting.rpt_threshold_simulation`: 16 rows.
- [x] `fraud_project_reporting.rpt_report_readiness`: 6 rows.
- [x] `fraud_project_reporting.rpt_identity_product_coverage`: 5 ProductCD rows.
- [x] `fraud_project_reporting.rpt_time_amount_signals`: 48 relative-hour and amount-decimal rows.
- [x] `fraud_project_reporting.rpt_quality_contract`: 6 quality gates.

## Live Web Dashboard

- [x] Production URL opens successfully.
- [x] API uses the `fraud_project_reporting` dataset.
- [x] Dashboard payload contract covers reporting groups and niche drilldown group.
- [x] UI language is English-first.
- [x] No visible legacy presentation-tool references remain in the dashboard.
- [x] Global slicers cover metric, segment family, and operational priority.
- [x] Segment comparison panel shows deltas and recommendations.
- [x] Drill-through drawer shows count, rate, lift, share, workload, and recommended action.
- [x] Fraud contribution waterfall uses the segment watchlist.
- [x] Threshold simulation recalculates workload, capture, precision, false-positive burden, and missed exposure.
- [x] Drift indicators surface fraud movement, readiness, and data quality risk without workflow screens.
- [x] Export JSON, print/save as PDF, and copy executive summary actions are available.

## ML Evidence

- [x] Time-based validation is documented.
- [x] ROC-AUC and average precision are documented.
- [x] Precision, recall, false-positive rate, workload, and lift are documented.
- [x] Feature importance artifact is available.
- [x] SHAP summary artifact is available.
- [x] Precision-recall curve artifact is available.
- [x] Risk-band operational use is documented.
- [x] Masked feature interpretation limits are documented.

## Repository Hygiene

- [x] Raw Kaggle CSV files are not committed.
- [x] Service-account JSON files are not committed.
- [x] DuckDB files are not committed.
- [x] Large temporary output dumps are ignored.
- [x] Public docs are English-first.
- [x] Legacy presentation artifacts are out of the production path.
- [x] GitHub Actions validate Python, dbt, and web dashboard contracts.
