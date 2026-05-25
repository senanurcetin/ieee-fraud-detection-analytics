# Live Web Dashboard Guide

The live dashboard is the primary presentation layer for the fraud analytics project. It replaces the archived Power BI prototype and presents the dbt-built BigQuery marts through a FastAPI API and a browser-based executive analytics interface.

## Production URL

```text
https://fraud-project-web.vercel.app
```

## Data Contract

The dashboard reads only from the `fraud_project_powerbi` dataset. It does not query raw Kaggle tables directly.

Core API endpoint:

```text
/api/dashboard
```

Main table groups:

- Executive KPIs: `mart_fraud_summary`, `pbi_executive_kpis`
- Segment analysis: `pbi_segment_watchlist`, `pbi_product_risk`, `pbi_identity_risk`, `pbi_payment_heatmap`
- Amount and time analysis: `pbi_amount_bands`, `pbi_daily_drift`, `pbi_time_amount_signals`
- Model operations: `pbi_threshold_simulation`, `pbi_review_strategy`, `pbi_feature_importance`, `pbi_model_risk_bands`
- Data quality: `pbi_quality_contract`, `pbi_report_readiness`, `pbi_feature_family_missingness`

## Dashboard Sections

1. Executive Overview
   - portfolio KPIs
   - key risk influencers
   - fraud contribution Pareto
   - product, risk-band and amount-band comparisons

2. Deep Segment Analysis
   - global metric and priority slicers
   - decomposition tree
   - segment watchlist
   - identity/product coverage matrix
   - relative hour and amount-decimal heatmap

3. Model and Threshold Simulation
   - threshold what-if slider
   - workload, capture and precision simulation
   - review strategy table
   - feature importance
   - feature-family treemap

4. Data Trust and Lineage
   - data quality contract
   - report readiness scorecard
   - missingness profile
   - BigQuery/dbt/web lineage
   - narrative matrix for presentation support

## Interactions

- Global slicers update segment metrics without changing the source data.
- Chart clicks open the drill-through drawer with segment-level evidence.
- Custom tooltips expose count, rate, lift and share values.
- Threshold slider recalculates operational model trade-offs.
- JSON export downloads the currently cached dashboard payload for audit or offline review.

## Operational Notes

- Vercel hosts only the web app and serverless API.
- Service-account credentials are stored as Vercel environment variables.
- The app uses cached BigQuery results to reduce query cost.
- dbt remains the source of truth for all analytical transformations.
