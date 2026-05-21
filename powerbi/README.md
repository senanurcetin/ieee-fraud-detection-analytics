# Power BI Report

Main deliverable:

```text
powerbi/fraud_project_v2.pbix
```

The report is an executive fraud-risk dashboard connected to the `fraud_project_powerbi` BigQuery reporting layer through DirectQuery. It is designed for presentation and operational decision support, not for raw-table exploration.

## Report Pages

The report contains six executive pages:

1. Executive Summary
2. Risk Concentration
3. Amount and Time Analysis
4. Payment and Email Segments
5. Model Scoring and Risk Bands
6. Data Quality and Architecture

Each page follows the same structure: a single management message, supporting evidence, and a short decision or action panel.

## Recommended Power BI Tables

Load only the reporting layer tables from `fraud_project_powerbi`:

- `fact_train_transactions`
- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_identity_risk`
- `pbi_identity_product_coverage`
- `pbi_amount_bands`
- `pbi_time_amount_signals`
- `pbi_daily_drift`
- `pbi_payment_heatmap`
- `pbi_email_domain_risk`
- `pbi_model_risk_bands`
- `pbi_threshold_simulation`
- `pbi_review_strategy`
- `pbi_segment_watchlist`
- `pbi_feature_importance`
- `pbi_data_quality_scorecard`
- `pbi_quality_contract`
- `pbi_report_readiness`
- `pbi_report_narrative`

Do not load raw Kaggle tables into the report model.

## Design Standard

- Storage mode: DirectQuery.
- Visual style: native visuals only where possible.
- Recommended visual types: textbox, slicer, clustered column chart, clustered bar chart, and controlled table visuals.
- KPI formatting: disable automatic display units so values are not shown as ambiguous `K`, `M`, or `B` abbreviations.
- Slicers: use report-level styling and clear Turkish labels in the PBIX delivery.
- Titles: use business-language titles, not raw field names.

## DAX Layer

Reusable DAX measures are documented in:

```text
powerbi/dax/fraud_project_measures.dax
```

Because PBIX model metadata is binary and difficult to review, DAX definitions are kept as a text artifact for version control and manual application in Power BI Desktop.

## Automated Validation

Run:

```powershell
python scripts\validate_powerbi_report.py
```

Latest automated package validation:

- PBIX package integrity: PASS
- Page count: 6
- Visual containers: 349
- Query-bound native visuals: 27
- Slicers: 6
- Controlled native tables: 4
- Tooltip-enabled analysis visuals: 14
- Embedded image visuals: 0
- Registered image resources: 0
- Unsafe field references: 0
- Raw query references: 0
- Native title leakage: 0
- Text clipping risk: 0

## Manual Final Check

Power BI Desktop must still be used for final visual review:

- Open `powerbi/fraud_project_v2.pbix`.
- Refresh DirectQuery.
- Confirm every page returns data.
- Confirm slicers do not break visuals.
- Confirm no placeholder or error visual remains.
