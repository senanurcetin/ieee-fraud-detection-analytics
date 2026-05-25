# Development Backlog

Bu backlog, Power BI prototipinden canlı web analitik katmanına geçiş sonrası kalan geliştirme alanlarını gösterir. Ana hedef, dashboard'u üst yönetim sunumu ve portföy gösterimi için daha etkileşimli, açıklanabilir ve güvenilir tutmaktır.

## P0 - Sunum ve Veri Güveni

1. Vercel production doğrulaması
   - `/api/dashboard?refresh=true` endpoint'i 18 tabloyu döndürmeli.
   - Toplam işlem sayısı 590.540 olarak görünmeli.
   - `pbi_report_readiness` 6/6 PASS olmalı.

2. Dashboard görsel kontrolü
   - Masaüstü 1440px ve mobil 390px görünümleri kontrol edilmeli.
   - Başlık kırpılması, taşan metin ve boş chart olmamalı.
   - Slicer, tooltip, drill-through ve threshold slider akışı çalışmalı.

3. README ekran görüntüleri
   - Yönetici özeti, segment analizi, model simülasyonu ve kalite sayfası güncel web arayüzünden alınmış olmalı.

## P1 - Analitik Derinlik

1. Segment karşılaştırma modu
   - İki segmentin fraud oranı, lift, fraud payı ve işlem payı yan yana karşılaştırılmalı.

2. Dynamic threshold policy
   - Threshold slider yalnızca model eğrisini değil, önerilen operasyon politikasını da güncellemeli.

3. Explainability sayfası
   - Feature importance yanında SHAP benzeri iş yorumları ve feature family katkısı sunulmalı.

4. Fraud contribution waterfall
   - Product, identity, payment, email ve amount eksenlerinin fraud hacmine katkısı kademeli gösterilmeli.

## P2 - Operasyonel Olgunluk

1. Alert simulation
   - Fraud rate drift, kritik bant hacmi ve veri kalite düşüşü için uyarı senaryoları görselleştirilmeli.

2. Export story
   - Dashboard JSON export yanında executive summary PDF/PNG export akışı eklenmeli.

3. Monitoring runbook
   - Vercel, BigQuery ve dbt hata durumlarında kontrol edilecek adımlar dokümante edilmeli.

## P3 - Ürünleşme

1. Multi-dataset template
   - Aynı dashboard iskeleti farklı fraud veri setlerine uygulanabilir hale getirilmeli.

2. Tenant-ready architecture note
   - Ücretsiz katman sınırları korunarak çoklu müşteri mimarisi için dataset izolasyonu planlanmalı.

3. Payment-independent validation
   - Stripe varsayımı olmadan, waitlist ve Merchant of Record uyumlu ürün doğrulama akışı tasarlanmalı.
