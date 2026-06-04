# IEEE-CIS Dataset Methodology Notes

## Dataset Positioning

The IEEE-CIS Fraud Detection dataset is treated as an e-commerce payment fraud dataset collected from a fraud protection context. It is not positioned as a core banking account-transaction dataset.

Implications for banking presentation:

- Card, product, device, email, amount, and identity signals are relevant to fraud analytics and threshold-policy design.
- KYC, account-balance, branch, counterparty, and ledger-level banking fields are not present.
- Masked fields are used as statistical signals, not as fully interpretable business definitions.

## TransactionDT Handling

`TransactionDT` is not a real timestamp. It is an elapsed-time value from an unknown reference point.

Implementation:

- `transaction_day = floor(TransactionDT / 86400) + 1`
- `transaction_week = floor(TransactionDT / 604800) + 1`
- `transaction_hour = floor(mod(TransactionDT, 86400) / 3600)`
- `relative_day_of_week = mod(floor(TransactionDT / 86400), 7)`

Interpretation rule:

- Use these fields for relative temporal patterns and drift monitoring.
- Do not describe them as calendar dates, weekdays, or actual clock-time events.

## Identity Coverage

The train transaction table has 590,540 rows and the train identity table has 144,233 rows. Identity coverage is therefore approximately 24.42%.

Analytical treatment:

- `has_identity` is a model and reporting signal, not only a join-status field.
- Identity-present and identity-missing transactions are analyzed separately.
- Product-level identity coverage is modeled in `mart_identity_product_coverage` and `rpt_identity_product_coverage`.

## Masked Feature Interpretation

The C, D, M, V, and identity fields are anonymized or partially masked. The project uses them as predictive and segment-level signals, but does not claim proprietary business definitions.

Interpretation standard:

- C-family fields are described as masked counting-style signals.
- D-family fields are described as masked elapsed-time signals.
- M-family fields are described as masked match/comparison signals.
- V-family fields are described as Vesta engineered anonymous features.
- Any statement about these fields is observational, not a confirmed data-owner definition.

## V Feature Scope

The raw transaction table includes V1-V339 anonymous engineered features. The active registry version expands the model scope to V1-V339 with a configurable missingness ceiling, resulting in a 425-feature candidate set in the current snapshot.

Rationale:

- The objective is a portfolio-grade analytical pipeline with stable local runtime and interpretable output.
- Feature importance and feature contribution artifacts are used to show which selected features actually drive model splits.
- The report avoids business over-interpretation of individual V fields.

Current limitation:

- V1-V339 are considered through the missingness-filtered selection function in `src/prepare_raw_and_ml.py`.
- Rolling validation windows are tracked to detect whether the expanded feature scope introduces unstable time-window behavior.

## ProductCD Framing

`ProductCD` has five coded values: W, H, C, S, and R. The project does not assign unsupported real-world labels such as web, hotel, or cashback. It uses the codes as product segments.

Operational rule:

- Product C is treated as a high-risk coded segment because its observed fraud rate and fraud share are materially above baseline.
- Product thresholds should be calibrated by observed fraud rate, fraud share, and review capacity rather than by assumed product meaning.

## Synthetic UID

The dataset does not provide a verified customer identifier. The project creates `synthetic_uid_card_addr` from `card1 + addr1` for segment-level analysis.

Governance rule:

- This is a customer-like analytical key, not a verified customer ID.
- It can support aggregation and repeat-pattern exploration.
- It should not be used for customer-level decisioning without production identity resolution.

## Amount Decimal Signal

`TransactionAmt` is decomposed into:

- `transaction_amount_cents`
- `is_round_amount`

Purpose:

- Separate round-amount behavior from fractional-amount behavior.
- Support fraud-rate comparison by amount pattern.
- Give the business an additional rule-candidate signal without relying only on broad amount bands.

## Email Domain Grouping

Purchaser email domains are modeled at two levels:

- `purchaser_email_group`: top visible reporting groups such as gmail.com, hotmail.com, anonymous.com, and Other.
- `purchaser_email_risk_group`: business-facing group such as Mainstream consumer, Privacy masked, Institutional, Unknown, and Long-tail / other.

This avoids overfitting to rare raw domains while keeping email behavior interpretable for stakeholders.
