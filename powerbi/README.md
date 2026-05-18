# Power BI Teslimi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Rapor 6 sayfadan oluşur:

1. Yönetici Özeti
2. Risk Konsantrasyonu
3. Tutar ve Zaman Analizi
4. Ödeme ve Email Segmentleri
5. Model Skorlama ve Risk Bantları
6. Veri Kalitesi ve Mimari

## Veri Modeli

PBIX dosyası BigQuery DirectQuery veri modelini korur ve rapor layout'unu profesyonel sunum akışına göre doldurur. Power BI için final veri katmanı `fraud_project_powerbi` datasetidir.

## Görsel Varlıklar

`powerbi/assets/` klasörü raporda kullanılan analiz görsellerini içerir. Görseller; fraud oranı, risk lift, tutar dağılımı, ödeme segmentleri, email domain riski, model performansı ve veri kalitesi temalarını kapsar.

Ek yönetici görselleri:

- `17_executive_control_panel.png`
- `18_segment_watchlist.png`
- `19_model_threshold_simulation.png`
- `20_qa_readiness_scorecard.png`

Bu görseller BigQuery `fraud_project_powerbi` datasetindeki raporlama tablolarından üretilir ve `fraud_project_v2.pbix` içine gömülüdür.
