# Live Fraud Analytics Report Guide

The live web application is the primary presentation layer for the IEEE-CIS fraud analytics project. It is structured as a BI-style analytical report embedded in a web app.

## Production URL

```text
https://fraud-project-web.vercel.app
```

## Report Story

The report answers nine executive and analytical questions:

1. What is the total fraud exposure?
2. Is fraud increasing or decreasing?
3. Which transaction amounts are most risky?
4. Which masked customer proxy groups are riskier?
5. Do masked address and distance proxies separate fraud risk without pretending to be geography?
6. Which behaviors indicate fraud?
7. Which features explain prediction?
8. How well does the model perform?
9. What should the business do next?

Current delivery status: production-ready web report, with focused Primary Analysis views and Supporting Visuals available on each page for deeper evidence.

## Page Flow

1. **Executive Fraud Overview**
   - Start here for total population, fraud rate, exposure, capturable exposure, and concentration.

2. **Fraud Trend Analysis**
   - Use relative-day and relative-hour visuals to discuss drift and time-window risk.

3. **Transaction Amount Analysis**
   - Show amount-band fraud rate, product x amount heatmaps, and amount-score outliers.

4. **Customer Risk Analysis**
   - Explain identity, email, device, product, and payment-email intersection risk using masked dataset proxies. The payment x email heatmap is a primary full-width visual because it supports the nested segmentation story.

5. **Masked Address & Distance Analysis**
   - Use address, distance, and masked entity proxies as analytical signals without inferring country or city.

6. **Behavioral Pattern Analysis**
   - Link payment, email, hour, score, and amount behavior into actionable risk patterns.

7. **Feature Importance Analysis**
   - Explain which features and feature families drive model scoring.

8. **Model Performance Analysis**
   - Present ROC-AUC, PR-AUC, precision, recall, threshold tradeoffs, risk bands, and confusion matrix.

9. **Key Insights & Recommendations**
   - Close with a recommendation matrix and expected exposure reduction logic.

## Interactions

- Global slicers filter report visuals by relative day window, product, amount band, email group, identity status, and risk band.
- Clicking chart segments applies cross-filtering.
- Clicking a visual header/card opens chart-level drill-through context.
- Clicking a data mark opens segment-level drill-through for comparable nested cuts.
- Hover tooltips expose count, rate, lift, share, score, and exposure context.
- Same-family drill-down charts show the analytical breakdown behind a selected segment.
- CSV export downloads the active page data.
- PDF export uses browser print styles for the current report state.
- Dark and light mode support presentation environments.
- Primary Analysis / Supporting Visuals toggles keep the main story concise while retaining diagnostic charts.

## Dataset Limits

- `TransactionDT` is relative elapsed time and must not be presented as a calendar date.
- IEEE-CIS does not contain native country, city, IP-location, or user-age fields.
- Address and distance fields are proxy signals only; geography requires external enrichment before maps can be enabled.
- Customer analysis uses masked proxy fields, not real customer master data.
- Model scores are used for analytical prioritization and threshold simulation.

## Recommended Presentation Sequence

For a short presentation:

1. Executive Fraud Overview
2. Transaction Amount Analysis
3. Customer Risk Analysis
4. Model Performance Analysis
5. Key Insights & Recommendations

Recommended 6-minute story:

1. Start with total fraud exposure and concentration in Executive Fraud Overview.
2. Move to Transaction Amount Analysis to show rate-versus-exposure tradeoffs.
3. Use Customer Risk Analysis to prove nested segmentation through identity, email, and payment-email heatmap evidence.
4. Use Behavioral Pattern Analysis only if time allows; focus on relative-hour fraud pattern.
5. Use Model Performance Analysis to explain threshold simulation, capture, precision, and workload.
6. Close with Key Insights & Recommendations as the business action layer.

For a detailed technical review:

1. Fraud Trend Analysis
2. Behavioral Pattern Analysis
3. Feature Importance Analysis
4. Model Performance Analysis
5. Masked Address & Distance Analysis proxy-signal discussion

## Operational Notes

- Vercel hosts the web application and serverless API.
- BigQuery remains the production source of truth.
- DuckDB is used for zero-cost local QA.
- Service-account credentials must be stored as environment variables, never in Git.
- The app uses cached reporting data to control query cost.
