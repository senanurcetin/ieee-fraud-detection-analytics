# Power BI Native Visual Spesifikasyonu

Bu doküman, `fraud_project_v2.pbix` dosyasının Power BI Desktop içinde native visual seviyesine taşınması için kesin uygulama tarifidir.

## Model Tabloları

Rapor yalnız şu dataset üzerinden çalışmalıdır:

```text
workintech-working.fraud_project_powerbi
```

Kullanılacak ana tablolar:

- `fact_train_transactions`
- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_identity_risk`
- `pbi_amount_bands`
- `pbi_daily_drift`
- `pbi_payment_heatmap`
- `pbi_email_domain_risk`
- `pbi_model_risk_bands`
- `pbi_feature_importance`
- `pbi_data_quality_scorecard`
- `pbi_report_narrative`
- `pbi_quality_contract`

## DAX Ölçüleri

```DAX
Transactions = COUNTROWS(fact_train_transactions)

Fraud Transactions = SUM(fact_train_transactions[is_fraud])

Fraud Rate = DIVIDE([Fraud Transactions], [Transactions])

Average Amount = AVERAGE(fact_train_transactions[transaction_amount])

Critical Risk Transactions =
CALCULATE(
    [Transactions],
    fact_train_transactions[risk_band] = "Critical"
)

High Critical Transactions =
CALCULATE(
    [Transactions],
    fact_train_transactions[risk_band] IN {"High", "Critical"}
)

High Critical Share =
DIVIDE([High Critical Transactions], [Transactions])

Predicted Risk = AVERAGE(fact_train_transactions[predicted_fraud_probability])
```

## Sayfa Bazlı Visual Kurulumu

### Yönetici Özeti

- Card: `pbi_executive_kpis[total_transactions]`
- Card: `pbi_executive_kpis[fraud_rate]`
- Card: `pbi_executive_kpis[fraud_transactions]`
- Card: `pbi_executive_kpis[critical_risk_fraud_rate]`
- Clustered column chart: Axis `pbi_product_risk[product_cd]`, Values `pbi_product_risk[fraud_rate]`
- Clustered column chart: Axis `pbi_identity_risk[identity_segment]`, Values `pbi_identity_risk[fraud_rate]`

### Risk Konsantrasyonu

- Bar chart: Axis `pbi_product_risk[product_cd]`, Values `pbi_product_risk[lift]`
- Matrix: Rows `mart_product_device_stats[product_cd]`, Columns `mart_product_device_stats[device_type]`, Values `mart_product_device_stats[fraud_rate]`
- Table: `pbi_report_narrative[executive_message]`, `pbi_report_narrative[recommended_action]`, page filter `page_name = Risk Konsantrasyonu`

### Tutar ve Zaman Analizi

- Combo chart: Axis `pbi_daily_drift[transaction_day]`, Column `pbi_daily_drift[transaction_count]`, Line `pbi_daily_drift[fraud_rate_ma7]`
- Bar chart: Axis `pbi_amount_bands[amount_band]`, Values `pbi_amount_bands[fraud_rate]`
- Table: `pbi_daily_drift[transaction_day]`, `pbi_daily_drift[drift_flag]`, `pbi_daily_drift[fraud_rate_ma7]`

### Ödeme ve Email Segmentleri

- Matrix heatmap: Rows `pbi_payment_heatmap[card_network]`, Columns `pbi_payment_heatmap[card_type]`, Values `pbi_payment_heatmap[fraud_rate]`
- Bar chart: Axis `pbi_email_domain_risk[purchaser_email_group]`, Values `pbi_email_domain_risk[fraud_rate]`
- Bar chart: Axis `pbi_email_domain_risk[purchaser_email_group]`, Values `pbi_email_domain_risk[fraud_share]`

### Model Skorlama ve Risk Bantları

- Bar chart: Axis `pbi_model_risk_bands[risk_band]`, Values `pbi_model_risk_bands[observed_fraud_rate]`, Sort by `band_rank`
- Bar chart: Axis `pbi_model_risk_bands[risk_band]`, Values `pbi_model_risk_bands[lift]`, Sort by `band_rank`
- Bar chart: Axis `pbi_feature_importance[feature]`, Values `pbi_feature_importance[importance]`, Top N 15 by `importance`

### Veri Kalitesi ve Mimari

- Table: `pbi_quality_contract[object_name]`, `expected_rows`, `actual_rows`, `status`
- Bar chart: Axis `pbi_data_quality_scorecard[column_family]`, Values `avg_missing_rate`
- Table: `pbi_report_narrative[executive_message]`, `pbi_report_narrative[recommended_action]`, page filter `page_name = Veri Kalitesi ve Mimari`

## Format Kuralları

- `fraud_rate`, `lift`, `transaction_share`, `fraud_share`, `avg_missing_rate`: yüzde veya 2 ondalıklı sayı formatı.
- `transaction_count`, `fraud_count`, `total_transactions`: binlik ayracı.
- Kritik risk rengi: kırmızı.
- Normal/low risk rengi: yeşil veya nötr gri.
- Başlıklar Türkçe ve yönetici dilinde olmalı.
