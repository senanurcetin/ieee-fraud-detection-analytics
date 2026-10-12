# Reviewer brief — IEEE-CIS Fraud Risk Intelligence

**Role:** Fraud analytics, analytics engineering, explainable machine learning and executive BI. **Data:** publicly available IEEE-CIS fraud competition dataset; source data is not redistributed.

## The decision problem

At a baseline fraud rate of **3.50%**, risk concentration and review capacity matter more than accuracy alone. This project maps exposure through BigQuery/dbt marts and a LightGBM risk ranking, then surfaces threshold trade-offs to analysts.

| Reviewer question | Concrete evidence |
|---|---|
| Are the risks concentrated? | Product C has an **11.7% fraud rate**, **3.34× lift**, and **38.8% of fraud labels**; see [key findings](../README.md#key-findings) |
| Was ranking assessed out of time? | Holdout ROC-AUC **0.9134**, top 5% score band captures **58.32% of fraud** at **40.13% precision**; see [model layer](../README.md#ml-scoring-layer) |
| Why not report random-split AUC as the headline? | [Time vs random validation study](https://www.kaggle.com/code/senanuretin/ieee-cis-how-much-of-random-cv-auc-is-leakage) |
| Is there visual proof? | [Executive dashboard screenshot](assets/web_dashboard_executive_overview.png), [threshold screenshot](assets/web_dashboard_model_threshold.png), and [live web dashboard](https://fraud-project-web.vercel.app) |
| Is data quality inspectable? | [dbt models](../models/), [tests](../tests/) and [README quality checks](../README.md#quality-gates) |

## What this demonstrates

A risk-reporting workflow that connects cohort-level analysis, reproducible data models, temporal model assessment and actionable review thresholds. Identity-availability features are proxy signals that demand fairness and stability review; high lift is not evidence of causation.

## Boundaries

Competition labels and timestamps do not establish real-time banking production performance. No system here makes customer-impacting decisions automatically. Threshold choices require business loss estimates, governance and prospective monitoring.

**Start here:** [Complete methodology](../README.md).
