# 06 - Eksik Listesi ve Son Geliştirme Durumu

Bu doküman, son geliştirme iterasyonundan sonra projenin gerçek durumunu ve kalan kalite risklerini gösterir. Mevcut teslim artık boş veya yalnızca taslak rapor değildir; `powerbi/fraud_project_v2.pbix` içinde 6 ana sunum sayfası, 1 canlı analitik kontrol sayfası, 63 visual container ve BigQuery model alanlarına bağlı 40 native visual vardır.

## Bu Iterasyonda Kapatılan Eksikler

1. Ana Power BI sayfaları native görsellerle güçlendirildi
   - Yönetici Özeti: native KPI kartları, product/risk band chart'ları, slicer ve risk kuyruğu tablosu.
   - Risk Konsantrasyonu: product/device tablo, product/device chart, risk bandı yakalama tablosu ve slicer'lar.
   - Tutar ve Zaman Analizi: amount band chart, 7 günlük fraud trendi, drift table ve amount slicer.
   - Ödeme ve Email Segmentleri: card network/type chart, email domain chart/table ve email slicer.
   - Model Skorlama ve Risk Bantları: risk bandı fraud oranı, yakalama payı, inceleme kuyruğu ve risk slicer.
   - Veri Kalitesi ve Mimari: missingness table, missingness chart ve kalite KPI kartları.

2. Native model kanıtı rapor geneline yayıldı
   - Önceki sürümde native görseller ağırlıklı olarak `Canlı Analitik Katmanı` sayfasındaydı.
   - Yeni sürümde her ana sunum sayfasında en az 4 query-bound native Power BI visual var.
   - Toplam query-bound native visual sayısı 40'a çıktı.

3. dbt kalite kapsamı artırıldı
   - Data test sayısı 67'den 73'e çıktı.
   - Yeni singular testler:
     - `assert_threshold_simulation_monotonic`
     - `assert_threshold_precision_signal`
     - `assert_risk_band_monotonicity`
     - `assert_segment_watchlist_business_rules`
     - `assert_review_strategy_business_rules`
     - `assert_powerbi_report_contract`
   - Son prod build sonucu: `PASS=102 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=103`.

4. BigQuery katmanları doğrulandı
   - Raw Kaggle tabloları beklenen satır sayılarıyla duruyor.
   - Staging view sorguları satır döndürüyor.
   - Mart ve Power BI datasetleri dolu.
   - `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
   - `fraud_project_powerbi.pbi_segment_watchlist`: 20 satır.
   - `fraud_project_powerbi.pbi_threshold_simulation`: 16 satır.
   - `fraud_project_powerbi.pbi_review_strategy`: 4 satır.
   - `fraud_project_powerbi.pbi_report_readiness`: 6 satır.

## Kalan P0 Kontroller

1. Power BI Desktop görsel açılış kontrolü
   - `powerbi/fraud_project_v2.pbix` dosyasını Power BI Desktop içinde aç.
   - 7 sayfanın tamamını sırayla kontrol et.
   - Native card, slicer, chart ve table görsellerinin veri döndürdüğünü kontrol et.

2. DirectQuery yenileme kontrolü
   - Rapor açıldıktan sonra BigQuery bağlantı yetkisini onayla.
   - DirectQuery görsellerinin boş dönmediğini kontrol et.
   - Slicer seçimi yapıldığında ilgili görsellerin bozulmadığını kontrol et.

3. Son görsel estetik kontrol
   - Sayfa başlıkları okunur kalmalı.
   - Native görseller statik analiz görselleriyle üst üste binmemeli.
   - Kritik sayılarda format gerekiyorsa Power BI Desktop içinde yüzde/binlik ayracı formatı uygulanmalı.

## Kalan P1 İyileştirmeler

1. Ana 6 sayfanın tamamını yüzde yüz native hale getirme
   - Mevcut sürüm hibrit yapıdadır: native görseller + gömülü analiz görselleri.
   - Tam native final için `pbi_*` tabloları Power BI modeline eklenmeli ve ana görseller bu tablolara taşınmalıdır.

2. Power BI ölçü katmanı
   - `Fraud Rate`
   - `Fraud Transactions`
   - `High Critical Share`
   - `Average Amount`
   - `Predicted Risk`
   - `Review Workload Share`

3. Conditional formatting
   - Risk priority alanlarında kırmızı/turuncu/amber/yeşil format.
   - PASS/FAIL kalite tablolarında durum rengi.
   - Lift ve fraud share alanlarında eşik bazlı vurgu.

## Kabul Eşiği

Final portföy kullanımı için aşağıdaki maddeler aynı anda sağlanmalıdır:

- BigQuery `fraud_project_powerbi` datasetindeki tüm rapor tabloları dolu.
- dbt full build PASS.
- dbt docs generate PASS.
- Power BI dosyası açılıyor.
- 6 ana sunum sayfası boş değil.
- Her ana sayfada veri modeline bağlı native visual var.
- 7. sayfadaki native görseller veri döndürüyor.
- Rapor içinde proje dışı üretim izi, demo dili veya gereksiz teknik not görünmüyor.
