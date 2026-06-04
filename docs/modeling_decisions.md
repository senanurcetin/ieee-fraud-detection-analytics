# Modeling Decisions

## Objective

The model is designed to rank transactions for threshold-policy analysis. It is not positioned as an automated decline engine. The expected business use is risk-band prioritization and segment monitoring.

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

`TransactionDT` is treated as an elapsed-time field, not a real timestamp. All daily, hourly, and weekly fields are relative transformations used for pattern analysis and drift monitoring.

## Metrics

Primary metric:

- ROC-AUC

Secondary metric:

- Average precision

Operational metrics:

- Risk-band fraud capture
- Workload share
- Segment lift
- Fraud share by segment
- Precision, recall, and F1 at selected threshold policies

Latest validation snapshot:

- ROC-AUC: 0.9134
- Average precision: 0.5354
- Top 5% validation score band: 40.13% precision, 58.32% recall, 5.00% workload
- Fixed 0.50 threshold: 25.68% precision, 69.78% recall, 9.35% workload

Validation evidence:

- ROC-AUC: 0.9134
- Average precision: 0.5354
- Top 10% score lift: 7.12x
- Top 5% false-positive rate: 3.10%

## Class Imbalance Strategy

The dataset has a baseline fraud rate of 3.50%, so accuracy is not a useful model-quality measure. The project handles class imbalance through:

- Probability-based ranking instead of hard class prediction.
- Average precision as a secondary metric.
- Quantile-based risk bands that control workload.
- Business-facing threshold simulation plus a fixed 0.50 scenario for comparison.

Synthetic oversampling is not used because the validation design is time-based and the priority is preserving realistic transaction chronology and threshold workload behavior.

## Feature Scope

The active registry version uses 425 selected features:

- Core transaction fields such as `TransactionDT` and `TransactionAmt`
- Card, address, distance, email, C, D, M, identity, device, and selected Vesta engineered V features
- V1-V339 from the anonymous Vesta feature family, filtered by the configured missingness ceiling

The V-family expansion is governed by `V_FEATURE_MISSINGNESS_THRESHOLD`. In the current registry snapshot, all 339 Vesta anonymous features are retained because they pass the configured threshold. The public dashboard exposes this scope through the model registry card and `/api/enterprise/model-registry`.

Masked feature interpretations are treated as observational. The report does not claim confirmed meanings for C, D, M, V, or identity fields beyond their role as anonymized fraud signals.

## Risk Bands

Model scores are converted into risk bands using score quantiles:

- `Low`: below p80
- `Elevated`: p80 to p95
- `High`: p95 to p99
- `Critical`: p99 and above

These bands support capacity planning: the business can decide how much flagged volume to allocate to each band.

Recommended starting policy:

- Use the top 5% validation score band as the focused policy baseline.
- Compare against the fixed 0.50 threshold when a higher-capture scenario is needed.
- Recalibrate thresholds if cost assumptions, capacity, or product mix changes.

## Monitoring Gap

The project includes drift-style reporting tables, daily fraud-rate monitoring, a registry snapshot, and rolling validation evidence. For production use, the next steps would be:

- Batch scoring schedule
- Approved drift thresholds
- Governance checks on score distribution and fraud-rate movement
- Human approval process for threshold changes

