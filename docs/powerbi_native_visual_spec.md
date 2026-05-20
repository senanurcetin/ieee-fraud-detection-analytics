# Power BI Native Visual Spesifikasyonu

Bu doküman, `fraud_project_v2.pbix` dosyasının güncel final rapor standardını tanımlar. Rapor BigQuery DirectQuery modelini korur ve Power BI Desktop içinde açılabilir, sade, Türkçe yönetici sunumu düzeniyle hazırlanır.

## Model Katmanı

Rapor şu BigQuery raporlama katmanına bağlıdır:

```text
workintech-working.fraud_project_powerbi
```

Final PBIX içinde güvenli şekilde kullanılan ana tablolar:

- `fact_train_transactions`
- `mart_fraud_summary`
- `mart_risk_band_stats`
- `mart_feature_missingness`

`pbi_*` tabloları BigQuery/dbt tarafında korunur. Power BI model metadata'sı yenilendikten sonra bu tablolar ek görseller için kontrollü biçimde devreye alınabilir.

## Güncel Visual Standardı

Final rapor şu görsel tipleriyle sınırlıdır:

- `textbox`
- `slicer`
- `clusteredColumnChart`
- `clusteredBarChart`
- kontrollü native tablo

Native card kullanılmaz. KPI alanları Power BI otomatik sayı kısaltmasına düşmemesi için metin tabanlı sunum formatıyla gösterilir.

Otomatik paket kontrolü:

```powershell
python scripts\validate_powerbi_report.py
```

Bu kontrol sayfa sayısını, görsel tiplerini, PNG kaynaklarını, ham alan adı referanslarını, tooltip kapsamını ve güvenli alan allowlist'ini doğrular.

## Sayfa Bazlı Kurgu

### Yönetici Özeti

- KPI göstergeleri: toplam işlem, sahte işlem, baz fraud oranı, identity kapsama.
- Ürün filtresi.
- Ürüne göre sahte işlem hacmi.
- Risk bandına göre sahte işlem hacmi.
- Tutar bandına göre sahte işlem hacmi.
- Bulgu, risk ve aksiyon karar metinleri.

### Risk Konsantrasyonu

- Ürün filtresi.
- Risk bandı filtresi.
- Ürün bazlı sahte işlem hacmi.
- Cihaz tipine göre sahte işlem hacmi.
- Risk bandı sahte işlem hacmi.
- Ürün ve risk bandı kanıt tablosu.
- Risk renk standardı.

### Tutar ve Zaman Analizi

- Tutar bandı filtresi.
- Tutar bandına göre sahte işlem hacmi.
- Gün içi sahte işlem adedi.
- Tutar bandı işlem hacmi.
- Tutar bandı kanıt tablosu.
- Zaman ve tutar karar metinleri.

### Ödeme ve Email Segmentleri

- Email grubu filtresi.
- Kart ağına göre sahte işlem adedi.
- Kart tipine göre sahte işlem adedi.
- Email grubuna göre sahte işlem hacmi.
- Ödeme segmenti kanıt tablosu.

### Model Skorlama ve Risk Bantları

- Risk bandı filtresi.
- Risk bandı gözlenen fraud oranı.
- Risk bandı sahte işlem hacmi.
- Risk bandı işlem tutarı.
- Risk bandı inceleme kanıt tablosu.
- Modelin karar değil önceliklendirme katmanı olduğunu anlatan karar metinleri.

### Veri Kalitesi ve Mimari

- Feature ailesi eksik değer hacmi.
- Eksik değer hacmi.
- Profil edilen satır KPI'ı.
- Eksik değer sinyali KPI'ı.
- Lineage: `Kaggle CSV -> BigQuery Raw -> dbt Staging -> dbt Mart -> Power BI DirectQuery`.
- dbt build ve BigQuery row-count kalite mesajı.

## Format Kuralları

- Görünen başlıklar Türkçe ve yönetici dilinde olmalıdır.
- Ham alan adları rapor yüzeyinde görünmemelidir.
- KPI değerlerinde otomatik `B`, `K`, `M` kısaltması görünmemelidir.
- Gereksiz dekoratif container kullanılmamalıdır.
- Renk standardı: kırmızı kritik risk, petrol yeşili kontrol/aksiyon, koyu lacivert ana metin, nötr gri ikincil metin.
- Önemli chart görsellerinde işlem tutarı veya sahte işlem adedi gibi tooltip bağlamı bulunmalıdır.
- Her sayfa tek ana mesaj taşımalıdır.
