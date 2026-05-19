# 06 - Eksik Listesi ve Son Geliştirme Durumu

Bu doküman, son geliştirme iterasyonundan sonra projenin gerçek durumunu ve kalan kalite risklerini gösterir. Mevcut teslim, BigQuery DirectQuery modeline bağlı 6 sayfalık native Power BI yönetici raporudur.

## Bu Iterasyonda Kapatılan Eksikler

1. Ana Power BI raporu native-only hale getirildi
   - Final rapor 6 sayfadan oluşuyor.
   - Ek teknik kontrol sayfası kaldırıldı.
   - Gömülü görüntü visual kullanılmıyor.
   - Kırılgan çizgi grafik ve tablo görseli kullanılmıyor.
   - Kullanılan görsel tipleri card, slicer, clustered column chart, clustered bar chart ve textbox ile sınırlandı.

2. Hata üreten alan bağımlılıkları temizlendi
   - Rapor yalnızca mevcut Power BI model metadata'sında güvenli alanları kullanıyor.
   - Yeni dbt kolonları rapor görsellerinden çıkarıldı; BigQuery/dbt tarafında kalmaya devam ediyor.
   - Tüm query-bound alanlar allowlist kontrolünden geçti.

3. Sayfa anlatısı yeniden yapılandırıldı
   - Yönetici Özeti: KPI, ürün riski, risk bandı ve tutar bandı aksiyon mesajı.
   - Risk Konsantrasyonu: ürün, cihaz ve risk bandı ayrışması.
   - Tutar ve Zaman Analizi: tutar bandı, saat ve hacim örüntüleri.
   - Ödeme ve Email Segmentleri: kart ağı, kart tipi ve email domain riskleri.
   - Model Skorlama ve Risk Bantları: skorların operasyon kuyruğu olarak kullanımı.
   - Veri Kalitesi ve Mimari: missingness, kalite kanıtı ve lineage.
   - Her sayfaya üst yönetim okumasını hızlandıran kısa karar panelleri eklendi.
   - Karar panelleri gerçek mart sonuçlarından türetilmiş oran, pay ve yoğunlaşma cümleleriyle güçlendirildi.
   - Rapor teması ve visual container stilleri kurumsal fraud-risk paletine taşındı.
   - Sayfa tasarım kabuğu sol rail, header panel, alt navigasyon ve filtre kontrol alanlarıyla tamamlandı.

4. dbt kalite kapsamı korundu
   - Data test sayısı 73.
   - Son prod build sonucu: `PASS=102 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=103`.
   - Power BI kontrat testleri ve reconciliation kontrolleri korunuyor.

5. BigQuery katmanları doğrulandı
   - Raw Kaggle tabloları beklenen satır sayılarıyla duruyor.
   - Mart ve Power BI datasetleri dolu.
   - `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
   - `fraud_project_mart.mart_risk_band_stats`: 8 satır.

## Kalan P0 Kontroller

1. Power BI Desktop görsel açılış kontrolü
   - `powerbi/fraud_project_v2.pbix` dosyasını Power BI Desktop içinde aç.
   - 6 sayfanın tamamını sırayla kontrol et.
   - Card, slicer ve chart görsellerinin veri döndürdüğünü kontrol et.

2. DirectQuery yenileme kontrolü
   - Rapor açıldıktan sonra BigQuery bağlantı yetkisini onayla.
   - Slicer seçimi yapıldığında ilgili görsellerin bozulmadığını kontrol et.
   - Kart değerlerinde otomatik kısaltma görünürse Power BI Desktop içindeki format panelinden display unit ayarını `None` yap.

## Kalan P1 İyileştirmeler

1. Power BI ölçü katmanı
   - Fraud Rate.
   - Fraud Transactions.
   - Average Amount.
   - Review Workload Share.

2. Yeni model metadata yenilemesi sonrası genişletilmiş görseller
   - `pbi_*` tabloları model metadata'sına eklendikten sonra segment watchlist ve review strategy tablosu native rapora alınabilir.
   - Yeni kolonlar eklendiğinde rapor allowlist'i kontrollü şekilde genişletilmelidir.

3. Conditional formatting
   - Risk bandı ve fraud oranı alanlarında eşik bazlı renk vurgusu.
   - PASS/FAIL kalite alanlarında durum rengi.

## Kabul Eşiği

Final portföy kullanımı için aşağıdaki maddeler aynı anda sağlanmalıdır:

- BigQuery `fraud_project_powerbi` datasetindeki rapor tabloları dolu.
- dbt full build PASS.
- dbt docs generate PASS.
- Power BI dosyası açılıyor.
- 6 sunum sayfası boş değil.
- Her sayfada veri modeline bağlı native visual var.
- Rapor içinde proje dışı üretim izi, geçici not veya sunum dışı teknik dil görünmüyor.
