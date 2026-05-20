# Modeling Decisions

## Objective

The model is designed to rank transactions for fraud review. It is not positioned as an automated decline engine. The expected business use is review queue prioritization and segment monitoring.

## Algorithm Choice

The project uses `LightGBMClassifier`.

Reasons:

- Handles tabular fraud data with many sparse and anonymized features.
- Performs well with non-linear interactions across amount, card, identity, device, and engineered V/C/D/M features.
- Trains efficiently on the IEEE-CIS dataset size in a local environment.
- Supports feature importance outputs for analyst interpretation.

Rejected alternatives:

- Logistic regression: easier to explain but weaker for non-linear interactions.
- Random forest: heavier runtime and less efficient for this dataset size.
- XGBoost: strong alternative, but LightGBM offers faster iteration for this project.

## Validation Strategy

The validation split is time-based:

- Training: first 80% of transactions by `TransactionDT`.
- Validation: last 20% of transactions by `TransactionDT`.

This avoids random leakage across time and better reflects fraud monitoring use cases.

## Metrics

Primary metric:

- ROC-AUC

Secondary metric:

- Average precision

Operational metrics:

- Risk-band fraud capture
- Review workload share
- Segment lift
- Fraud share by segment
- Precision, recall, and F1 at the selected review policy

Latest validation snapshot:

- ROC-AUC: 0.9167
- Average precision: 0.5308
- High + Critical queue: 54.8% precision, 78.3% recall, 0.645 F1, 5.0% review workload

## Class Imbalance Strategy

The dataset has a baseline fraud rate of 3.50%, so accuracy is not a useful model-quality measure. The project handles class imbalance through:

- Probability-based ranking instead of hard class prediction.
- Average precision as a secondary metric.
- Quantile-based review bands that control analyst workload.
- Business-facing threshold simulation rather than a fixed 0.50 classification threshold.

Synthetic oversampling is not used because the validation design is time-based and the priority is preserving realistic transaction chronology and review workload behavior.

## Risk Bands

Model scores are converted into review bands using score quantiles:

- `Low`: below p80
- `Elevated`: p80 to p95
- `High`: p95 to p99
- `Critical`: p99 and above

These bands support capacity planning: the operations team can decide how much review volume to allocate to each band.

Recommended starting policy:

- Review `High + Critical` first.
- Expected workload: 5.0% of train transactions.
- Expected fraud capture: 78.3% of train fraud labels.
- Expected precision: 54.8% in the reviewed queue.

## Monitoring Gap

The project includes drift-style reporting tables and daily fraud-rate monitoring, but it does not expose a production inference API or automated model drift service. For production use, the next steps would be:

- Model registry
- Batch scoring schedule
- Drift thresholds
- Alerting on score distribution and fraud-rate movement
- Human approval workflow for threshold changes
