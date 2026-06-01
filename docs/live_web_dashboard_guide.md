# Live Fraud Intelligence Platform Guide

The live web application is the primary presentation layer for the IEEE-CIS fraud analytics project. It exposes the dbt-built reporting layer through a FastAPI backend and a browser-based enterprise fraud intelligence interface.

## Production URL

```text
https://fraud-project-web.vercel.app
```

## Platform Story

The platform is structured as a decision workflow, not a static report:

1. Executives see where fraud is concentrated and how much exposure is at stake.
2. Analysts receive a prioritized investigation queue.
3. A transaction detail workspace explains why one case is risky.
4. Fraud strategy teams explore nested segment behavior.
5. Model-risk users monitor performance, threshold trade-offs, and drift.
6. Operations teams review historical replay alerts.

The application is English-first and web-only. No external reporting desktop dependency is part of the presentation path.

## Data Contract

The dashboard reads only governed reporting tables from `fraud_project_reporting`. It does not query raw Kaggle tables directly.

Backward-compatible endpoint:

```text
/api/dashboard
```

Enterprise endpoints:

```text
/api/enterprise/summary
/api/enterprise/cases
/api/enterprise/cases/{transaction_id}
/api/enterprise/segments
/api/enterprise/alerts
/api/enterprise/model-monitoring
/api/enterprise/metadata
```

Main data groups:

- Executive: `rpt_executive_kpis`, `rpt_segment_watchlist`, `rpt_daily_drift`
- Investigation: `fact_train_transactions`, `rpt_model_risk_bands`
- Segment intelligence: `rpt_product_risk`, `rpt_identity_risk`, `rpt_amount_bands`, `rpt_payment_heatmap`, `rpt_email_domain_risk`
- Model operations: `rpt_threshold_simulation`, `rpt_review_strategy`, `rpt_feature_importance`
- Data trust: `rpt_quality_contract`, `rpt_report_readiness`, `rpt_data_quality_scorecard`

## Page Guide

### Executive Command Center

Use this page for the first 30 seconds of a presentation.

Key points:

- Fraud is rare at portfolio level, but concentrated in specific pockets.
- Loss exposure and capturable exposure convert the technical result into business terms.
- Pareto and contribution charts show where controls should focus first.

### Analyst Investigation Queue

Use this page to show how the model output becomes an operational workflow.

Key points:

- Cases are grouped by calibrated risk category.
- The queue avoids automatic rejection language and frames the model as review prioritization.
- Clicking a case opens the detailed investigation workspace.

### Transaction Detail

Use this page to answer "why was this transaction flagged?"

Key points:

- Risk score and category are separated from raw probability.
- Explanation cards show top contributing signals.
- Audit trail and action blocks make the page look like an analyst case workspace.

### Fraud Intelligence Center

Use this page to explain segmentation depth.

Key points:

- Drilldowns compare related populations instead of unrelated segment types.
- Product, amount, payment, email, device, and identity signals are read as nested risk pockets.
- Heatmaps and Pareto charts support targeted control design.

### Model Monitoring

Use this page for model credibility.

Key points:

- ROC-AUC, PR-AUC, precision, recall, false positive rate, and top-decile lift are visible.
- The threshold simulator shows the trade-off between capture, workload, precision, review cost, and missed exposure.
- Feature importance and drift proxy views support explainability.

### Alert Management

Use this page to show operational monitoring.

Key points:

- Alerts are historical replay from IEEE-CIS relative time, not a real-time stream.
- The alert table links severity, trigger, current value, threshold, and recommended action.
- This page demonstrates how the platform would support monitoring routines in a production environment.

## Dataset Limits

The interface explicitly avoids unsupported claims:

- `TransactionDT` is relative elapsed time, not a calendar timestamp.
- IEEE-CIS does not provide real country, IP geolocation, or user age.
- Product, card, email, device, and identity fields are masked or anonymized.
- Masked entity relationships are analytical proxies, not verified customer networks.
- The model supports review prioritization, not automatic decline decisions.

## Presentation Flow

Recommended 3-minute sequence:

1. Start with the Executive Command Center and explain concentration plus exposure.
2. Move to Fraud Intelligence Center and show nested segment logic.
3. Open Analyst Investigation Queue and click one case.
4. Use Transaction Detail to explain why the case is risky.
5. Close with Model Monitoring threshold trade-offs.

## Operational Notes

- Vercel hosts the web application and serverless API.
- BigQuery remains the production source of truth.
- DuckDB is used for zero-cost local QA.
- Service-account credentials must be stored as environment variables, never in Git.
- API cache settings protect free-tier usage and reduce unnecessary BigQuery scans.
