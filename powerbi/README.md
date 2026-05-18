# Power BI Teslimi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Rapor 6 ana sunum sayfası ve 1 canlı model kontrol sayfasından oluşur:

1. Yönetici Özeti
2. Risk Konsantrasyonu
3. Tutar ve Zaman Analizi
4. Ödeme ve Email Segmentleri
5. Model Skorlama ve Risk Bantları
6. Veri Kalitesi ve Mimari
7. Canlı Analitik Katmanı

## Veri Modeli

PBIX dosyası BigQuery DirectQuery veri modelini korur. Final raporlama katmanı `workintech-working.fraud_project_powerbi` datasetidir.

`Canlı Analitik Katmanı` sayfası Power BI modelindeki `mart_*` tablolarına bağlı native card, bar, line ve table görselleri içerir. Bu sayfa, raporun yalnızca gömülü analiz görsellerinden ibaret olmadığını ve DirectQuery model alanlarının rapor içinde çalıştığını doğrulamak için eklendi.

## Görsel Varlıklar

`powerbi/assets/` klasörü raporda kullanılan analiz görsellerini içerir. Görseller; fraud oranı, risk lift, tutar dağılımı, ödeme segmentleri, email domain riski, model performansı, operasyon kuyruğu ve veri kalitesi temalarını kapsar.

Ek yönetici görselleri:

- `17_executive_control_panel.png`
- `18_segment_watchlist.png`
- `19_model_threshold_simulation.png`
- `20_qa_readiness_scorecard.png`
- `21_executive_decision_matrix.png`
- `22_review_strategy_matrix.png`
- `24_risk_funnel.png`
- `25_dbt_quality_gate.png`

## Son Doğrulama

- PBIX paket bütünlüğü: PASS
- Sayfa sayısı: 7
- Visual container sayısı: 46
- Native query-bound visual sayısı: 9
- dbt prod build: PASS, 96 PASS / 0 ERROR / 1 exposure NO-OP
- dbt docs generate: PASS
