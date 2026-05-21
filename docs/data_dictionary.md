# Data Dictionary

This document summarizes the fields used in the reporting and modeling layer. The raw Kaggle dataset contains hundreds of anonymized engineered variables; this project exposes the fields required for fraud analysis, model scoring, and executive reporting.

## Core Transaction Fields

| Field | Layer | Description |
| --- | --- | --- |
| `transaction_id` | staging, marts, powerbi | Unique transaction identifier. |
| `transaction_day` | staging, marts, powerbi | Relative day derived from `TransactionDT`. |
| `transaction_week` | powerbi | Relative week derived from transaction day. |
| `transaction_hour` | staging, powerbi | Relative hour within day derived from elapsed seconds. Not a real clock timestamp. |
| `relative_day_of_week` | staging, powerbi | Relative day-of-week index derived from `TransactionDT`. Not a calendar weekday. |
| `transaction_amount` | staging, marts, powerbi | Transaction amount. |
| `transaction_amount_cents` | staging, powerbi | Decimal-cent component of `TransactionAmt`. |
| `is_round_amount` | staging, powerbi | Flag for whole-number transaction amounts. |
| `amount_band` | intermediate, marts, powerbi | Business-friendly transaction amount bucket. |
| `product_cd` | powerbi | Product code normalized from Kaggle `ProductCD`. |
| `is_fraud` | staging, marts, powerbi | Fraud label: `1` fraud, `0` legitimate. |

## Identity and Device Fields

| Field | Layer | Description |
| --- | --- | --- |
| `has_identity` | intermediate, powerbi | Indicates whether the transaction has a matching identity record. |
| `synthetic_uid_card_addr` | staging, powerbi | Synthetic customer-like analysis key built from `card1 + addr1`; not a verified customer ID. |
| `device_type` | staging, marts, powerbi | Device type, normalized to desktop, mobile, or unknown. |
| `device_info` | staging | Raw device information when available. |

## Payment and Email Fields

| Field | Layer | Description |
| --- | --- | --- |
| `card_network` | intermediate, powerbi | Card network from `card4`, with missing values handled. |
| `card_type` | intermediate, powerbi | Card type from `card6`, with missing values handled. |
| `purchaser_email_group` | intermediate, powerbi | Grouped purchaser email domain. |
| `purchaser_email_risk_group` | intermediate, powerbi | Business-facing email domain group: mainstream, privacy masked, institutional, unknown, or long-tail. |

## Model Fields

| Field | Layer | Description |
| --- | --- | --- |
| `predicted_fraud_probability` | marts, powerbi | LightGBM fraud probability score. |
| `risk_band` | marts, powerbi | Score band: Low, Elevated, High, Critical. |
| `is_critical_risk` | powerbi | Flag for Critical risk band. |
| `is_high_or_critical_risk` | powerbi | Flag for High or Critical risk bands. |

## Data Quality Fields

| Field | Layer | Description |
| --- | --- | --- |
| `column_family` | marts, powerbi | Feature family used for missingness profiling. |
| `column_name` | marts, powerbi | Source column name. |
| `row_count` | marts, powerbi | Profiled row count. |
| `missing_count` | marts, powerbi | Number of missing values. |
| `missing_rate` | marts, powerbi | Missing values divided by row count. |

## Executive Metrics

| Metric | Description |
| --- | --- |
| Fraud rate | Fraud transactions divided by total transactions. |
| Lift | Segment fraud rate divided by baseline fraud rate. |
| Fraud share | Segment fraud count divided by total fraud count. |
| Transaction share | Segment transaction count divided by total transaction count. |
| Expected fraud capture | Share of fraud expected to be captured by a review band. |
