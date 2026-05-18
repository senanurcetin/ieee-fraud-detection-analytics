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

Ana 6 sunum sayfası artık yalnızca gömülü analiz görsellerinden oluşmaz; her ana sayfada BigQuery modelindeki tablolara bağlı native Power BI card, slicer, chart veya table görselleri vardır. `Canlı Analitik Katmanı` sayfası ek teknik kontrol sayfasıdır.

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
- Visual container sayısı: 63
- Native query-bound visual sayısı: 40
- Her ana sunum sayfasında en az 4 query-bound native visual var
- dbt prod build: PASS, 102 PASS / 0 ERROR / 1 exposure NO-OP
- dbt docs generate: PASS
