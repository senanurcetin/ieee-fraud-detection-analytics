# Data Dictionary

This document summarizes the fields used in the reporting and modeling layer. The raw Kaggle dataset contains hundreds of anonymized engineered variables; this project exposes the fields required for fraud analysis, model scoring, and executive reporting.

## Core Transaction Fields

| Field | Layer | Description |
| --- | --- | --- |
| `transaction_id` | staging, marts, reporting | Unique transaction identifier. |
| `transaction_day` | staging, marts, reporting | Relative day derived from `TransactionDT`. |
| `transaction_week` | reporting | Relative week derived from transaction day. |
| `transaction_hour` | staging, reporting | Relative hour within day derived from elapsed seconds. Not a real clock timestamp. |
| `relative_day_of_week` | staging, reporting | Relative day-of-week index derived from `TransactionDT`. Not a calendar weekday. |
| `transaction_amount` | staging, marts, reporting | Transaction amount. |
| `transaction_amount_cents` | staging, reporting | Decimal-cent component of `TransactionAmt`. |
| `is_round_amount` | staging, reporting | Flag for whole-number transaction amounts. |
| `amount_band` | intermediate, marts, reporting | Business-friendly transaction amount bucket. |
| `product_cd` | reporting | Product code normalized from Kaggle `ProductCD`. |
| `is_fraud` | staging, marts, reporting | Fraud label: `1` fraud, `0` legitimate. |

## Identity and Device Fields

| Field | Layer | Description |
| --- | --- | --- |
| `has_identity` | intermediate, reporting | Indicates whether the transaction has a matching identity record. |
| `synthetic_uid_card_addr` | staging, reporting | Synthetic customer-like analysis key built from `card1 + addr1`; not a verified customer ID. |
| `device_type` | staging, marts, reporting | Device type, normalized to desktop, mobile, or unknown. |
| `device_info` | staging | Raw device information when available. |

## Payment and Email Fields

| Field | Layer | Description |
| --- | --- | --- |
| `card_network` | intermediate, reporting | Card network from `card4`, with missing values handled. |
| `card_type` | intermediate, reporting | Card type from `card6`, with missing values handled. |
| `purchaser_email_group` | intermediate, reporting | Grouped purchaser email domain. |
| `purchaser_email_risk_group` | intermediate, reporting | Business-facing email domain group: mainstream, privacy masked, institutional, unknown, or long-tail. |

## Model Fields

| Field | Layer | Description |
| --- | --- | --- |
| `predicted_fraud_probability` | marts, reporting | LightGBM fraud probability score. |
| `risk_band` | marts, reporting | Score band: Low, Elevated, High, Critical. |
| `is_critical_risk` | reporting | Flag for Critical risk band. |
| `is_high_or_critical_risk` | reporting | Flag for High or Critical risk bands. |

## Data Quality Fields

| Field | Layer | Description |
| --- | --- | --- |
| `column_family` | marts, reporting | Feature family used for missingness profiling. |
| `column_name` | marts, reporting | Source column name. |
| `row_count` | marts, reporting | Profiled row count. |
| `missing_count` | marts, reporting | Number of missing values. |
| `missing_rate` | marts, reporting | Missing values divided by row count. |

## Executive Metrics

| Metric | Description |
| --- | --- |
| Fraud rate | Fraud transactions divided by total transactions. |
| Lift | Segment fraud rate divided by baseline fraud rate. |
| Fraud share | Segment fraud count divided by total fraud count. |
| Transaction share | Segment transaction count divided by total transaction count. |
| Expected fraud capture | Share of fraud expected to be captured by a review band. |
