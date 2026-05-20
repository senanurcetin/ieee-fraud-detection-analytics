# 05 - Detaylı Geliştirme Backlog'u

Bu liste, projenin portföy ve üst yönetim sunumu seviyesinde korunması için kalan işleri önceliklendirir. Son iterasyonda ana rapor native Power BI görsellerine taşındığı için backlog artık bakım, doğrulama ve kontrollü genişletme odağındadır.

## P0 - Kritik

1. Power BI Desktop açılış testi
   - `powerbi/fraud_project_v2.pbix` Power BI Desktop'ta açılmalı.
   - 6 sayfanın tamamında hata placeholder'ı olmadığı kontrol edilmeli.
   - KPI metinleri, slicer, clustered column chart, clustered bar chart ve kanıt tabloları doğru görünmeli.
   - Açılış öncesi `python scripts/validate_powerbi_report.py` PASS vermeli.

2. DirectQuery veri modeli kontrolü
   - Rapor `workintech-working.fraud_project_powerbi` veri katmanına bağlı kalmalı.
   - Slicer seçimleri sayfa görsellerini bozmamalı.
   - BigQuery bağlantı yetkisi onaylandıktan sonra görseller boş dönmemeli.

3. Format kontrolü
   - KPI alanlarında otomatik kısaltma görünmemeli; değerler sunum formatında kalmalı.
   - Grafik başlıklarında ham alan adı görünmemeli.
   - Grafik başlıkları Türkçe ve yönetici seviyesinde kalmalı.

## P1 - Güçlü Analitik

1. Segment lift anlatımı
   - Product C lift.
   - Identity lift.
   - Risk bandı lift.
   - Email domain lift.
   - Payment segment lift.

2. Risk katkısı analizi
   - Fraud share ve transaction share birlikte gösterilmeli.
   - Sadece fraud rate'e bakılmamalı; küçük hacimli segmentlerin yanıltıcı etkisi açıklanmalı.

3. Zaman drift analizi
   - Günlük fraud rate.
   - 7 günlük hareketli ortalama.
   - Drift flag.
   - Hacim ile risk trendinin birlikte okunması.

4. Model izleme
   - Risk bandı dağılımı.
   - Critical ve High bantlarında fraud capture.
   - Feature importance.
   - Model skorlarının operasyonel kullanımı.

## P2 - dbt ve Veri Kalitesi

1. dbt kalite kapısı
   - `dbt build --target prod` final kalite komutu olarak kullanılmalı.
   - 73 data test ve singular QA testleri korunmalı.
   - Test başarısızsa Power BI final raporu yenilenmemeli.

2. Power BI veri kontratı
   - `pbi_quality_contract` ve `pbi_report_readiness` tabloları BigQuery tarafında PASS kalmalı.
   - Beklenen ve gerçekleşen satır sayıları final kontrollerinde izlenmeli.

3. dbt docs
   - `dbt docs generate` her final build sonrası çalıştırılmalı.
   - Exposure: `fraud_project_v2`.
   - Kritik modellerde açıklamasız kolon kalmamalı.

## P3 - Sunum Kalitesi

1. Görsel tasarım
   - Kurumsal bankacılık paleti kullanılmalı.
   - Aşırı renkli veya amatör hissi veren tasarımdan kaçınılmalı.
   - Risk renkleri tutarlı olmalı: Critical kırmızı, High koyu turuncu, Elevated amber, Low yeşil/gri.

2. Sayfa düzeni
   - 1280x720 canvas standardı korunmalı.
   - Üst satır KPI, orta alan ana grafik, alt alan detay/aksiyon mesajı olacak şekilde düzenlenmeli.
   - Başlıklar kısa, grafik etiketleri okunabilir olmalı.

3. Yönetici dil kontrolü
   - Teknik jargon minimumda tutulmalı.
   - Her sayfada "ne oldu, neden önemli, ne yapılmalı" yapısı kurulmalı.
   - Görünür hiçbir yerde geliştirme aracı izi, geçici sunum dili veya proje içi teknik not olmamalı.

## P4 - Teslim ve Portföy

1. GitHub temizlik
   - Ham CSV, DuckDB, credential ve geçici output dump commitlenmemeli.
   - README proje hikayesini net anlatmalı.
   - `powerbi/fraud_project_v2.pbix` ana teslim olarak kalmalı.

2. Sunum akışı
   - 3 dakikalık kısa yönetici anlatımı hazırlanmalı.
   - 10 dakikalık teknik walkthrough hazırlanmalı.
   - dbt lineage ve BigQuery dataset yapısı gösterilebilir olmalı.

3. Final kabul
   - Power BI açılır.
   - BigQuery bağlantısı çalışır.
   - dbt build geçer.
   - Rapor 6 dolu sunum sayfasından oluşur.
   - Analiz hikayesi savunulabilir ve profesyoneldir.
