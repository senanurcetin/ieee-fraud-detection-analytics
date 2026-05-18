# 06 - Eksik Listesi ve Son Geliştirme Durumu

Bu doküman, son düzeltmeden sonra projenin gerçek durumunu ve kalan kalite risklerini gösterir. Mevcut teslim artık boş veya yalnızca taslak rapor değildir; `powerbi/fraud_project_v2.pbix` içinde 6 ana sunum sayfası, 1 canlı analitik kontrol sayfası, 46 visual container ve BigQuery model alanlarına bağlı 9 native visual vardır.

## Bu Iterasyonda Kapatılan Eksikler

1. Power BI placeholder riski kapatıldı
   - Yeni yönetici görselleri PBIX içinde `RegisteredResources` manifestine eklendi.
   - Paket doğrulamasında 24 görsel varlık kayıtlı görünüyor.
   - `SecurityBindings` kaldırılmış durumda; PBIX zip bütünlüğü PASS.

2. Native görsel kanıt katmanı eklendi
   - Yeni sayfa: `Canlı Analitik Katmanı`.
   - 4 card, 1 clustered column chart, 1 line chart, 1 clustered bar chart ve 2 table visual eklendi.
   - Görseller `mart_fraud_summary`, `mart_amount_bands`, `mart_daily_stats`, `mart_email_domain_stats`, `mart_risk_band_stats` ve `mart_feature_missingness` tablolarına bağlıdır.
   - Native visual alanları dbt catalog ile kolon seviyesinde doğrulandı.

3. dbt prod kalite kapısı tekrar çalıştırıldı
   - 29 model bulundu.
   - 67 data test çalıştı.
   - Sonuç: `PASS=96 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=97`.
   - `dbt docs generate` başarıyla tamamlandı ve `target/catalog.json` güncellendi.

4. BigQuery katmanları doğrulandı
   - Raw Kaggle tabloları beklenen satır sayılarıyla duruyor.
   - Staging view sorguları satır döndürüyor.
   - Mart ve Power BI datasetleri dolu.
   - `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
   - `fraud_project_powerbi.pbi_segment_watchlist`: 20 satır.
   - `fraud_project_powerbi.pbi_report_readiness`: 6 satır.

## Kalan P0 Kontroller

1. Power BI Desktop görsel açılış kontrolü
   - `powerbi/fraud_project_v2.pbix` dosyasını Power BI Desktop içinde aç.
   - 7 sayfanın tamamını sırayla kontrol et.
   - Özellikle `Canlı Analitik Katmanı` sayfasında native card/bar/line/table görsellerinin veri döndürdüğünü kontrol et.

2. DirectQuery tablo görünürlüğü
   - Veri panelinde `fact_train_transactions` ve `mart_*` tabloları görünüyorsa yeni native sayfa çalışmalıdır.
   - `pbi_*` tabloları da rapora eklenirse ana 6 sayfa tamamen native visual seviyesine taşınabilir.

3. Son sunum estetik kontrolü
   - Üst yönetim sunumu için ilk 6 sayfa ana anlatım olarak kullanılmalı.
   - 7. sayfa teknik doğrulama ve canlı model kanıtı olarak gösterilmeli.
   - Görsellerin kesilmediği, ölçeklenmediği ve başlıkların okunur olduğu Power BI Desktop içinde kontrol edilmeli.

## P1 - Bir Sonraki Profesyonel Seviye

1. Ana 6 sayfanın native dönüşümü
   - Yönetici KPI kartları native card olarak taşınmalı.
   - Segment watchlist native table veya matrix olmalı.
   - Product/identity lift chart'ları native bar chart olmalı.
   - Threshold simulation native line chart olmalı.
   - QA readiness native table olmalı.

2. Power BI ölçü katmanı
   - `Fraud Rate`
   - `Fraud Transactions`
   - `High Critical Share`
   - `Average Amount`
   - `Predicted Risk`
   - `Review Workload Share`

3. Format standardizasyonu
   - Fraud oranları yüzde formatında.
   - İşlem sayıları binlik ayraçla.
   - Lift değerleri `x` formatında.
   - Kritik risk kırmızı, kalite/başarı petrol yeşili, ana metin koyu lacivert.

## Kabul Eşiği

Final portföy kullanımı için aşağıdaki maddeler aynı anda sağlanmalıdır:

- BigQuery `fraud_project_powerbi` datasetindeki tüm rapor tabloları dolu.
- dbt full build PASS.
- dbt docs generate PASS.
- Power BI dosyası açılıyor.
- 6 ana sunum sayfası boş değil.
- 7. sayfadaki native görseller veri döndürüyor.
- Rapor içinde proje dışı üretim izi, demo dili veya gereksiz teknik not görünmüyor.
