# 05 - Detaylı Geliştirme Backlog'u

Bu liste, projenin portföy ve üst yönetim sunumu seviyesinde kusursuza yaklaşması için kalan işleri önceliklendirir.

## P0 - Kritik

1. Power BI native visual dönüşümü
   - Mevcut açılabilir rapor layout'u korunacak.
   - Gömülü analiz görselleri nihai teslimde yardımcı referans olarak kalabilir ancak ana rapor native Power BI visual'lardan oluşmalı.
   - Her sayfada KPI card, bar/line/matrix/table gibi Power BI visual'ları kullanılmalı.

2. DirectQuery veri modeli kontrolü
   - Rapor yalnız `workintech-working.fraud_project_powerbi` datasetinden beslenmeli.
   - Ham transaction tabloları rapora doğrudan bağlanmamalı.
   - Ağır sayfalar aggregate `pbi_*` tablolarını kullanmalı.

3. Açılış ve yenileme testi
   - `powerbi/fraud_project_v2.pbix` Power BI Desktop'ta açılmalı.
   - Credential/permission ekranları dışında hata vermemeli.
   - Sayfalarda boş visual kalmamalı.
   - DirectQuery sorguları zaman aşımına düşmemeli.

4. Yönetici anlatısı
   - Her sayfanın tek ana mesajı olmalı.
   - İlk sayfa problem büyüklüğünü, son sayfa veri güvenilirliğini anlatmalı.
   - Model sayfası, modelin karar verici değil önceliklendirme katmanı olduğunu açıkça göstermeli.

## P1 - Güçlü Analitik

1. Segment lift anlatımı
   - Product C lift
   - Identity lift
   - Risk bandı lift
   - Email domain lift
   - Payment segment lift

2. Risk katkısı analizi
   - Fraud share ve transaction share birlikte gösterilmeli.
   - Sadece fraud rate'e bakılmamalı; küçük hacimli segmentlerin yanıltıcı etkisi açıklanmalı.

3. Zaman drift analizi
   - Günlük fraud rate
   - 7 günlük hareketli ortalama
   - Drift flag
   - Hacim ile risk trendinin birlikte okunması

4. Model izleme
   - Risk bandı dağılımı
   - Critical ve High bantlarında fraud capture
   - Feature importance
   - Model skorlarının operasyonel kullanımı

## P2 - dbt ve Veri Kalitesi

1. dbt kalite kapısı
   - `dbt build --target prod` final kalite komutu olarak kullanılmalı.
   - 67 data test ve singular QA testleri korunmalı.
   - Test başarısızsa Power BI final raporu yenilenmemeli.

2. Power BI veri kontratı
   - `pbi_quality_contract` Power BI'da Veri Kalitesi sayfasına eklenmeli.
   - Beklenen ve gerçekleşen satır sayıları raporda görülebilmeli.
   - Tüm kontrat satırları `PASS` olmalı.

3. dbt docs
   - `dbt docs generate` her final build sonrası çalıştırılmalı.
   - Exposure: `fraud_project_v2`
   - Kritik modellerde açıklamasız kolon kalmamalı.

## P3 - Sunum Kalitesi

1. Görsel tasarım
   - Kurumsal bankacılık paleti kullanılmalı.
   - Aşırı renkli veya demo hissi veren tasarımdan kaçınılmalı.
   - Risk renkleri tutarlı olmalı: Critical kırmızı, High koyu turuncu, Elevated amber, Low yeşil/gri.

2. Sayfa düzeni
   - 1280x720 canvas standardı korunmalı.
   - Üst satır KPI, orta alan ana grafik, alt alan detay/aksiyon mesajı olacak şekilde düzenlenmeli.
   - Başlıklar kısa, grafik etiketleri okunabilir olmalı.

3. Yönetici dil kontrolü
   - Teknik jargon minimumda tutulmalı.
   - Her sayfada "ne oldu, neden önemli, ne yapılmalı" yapısı kurulmalı.
   - Görünür hiçbir yerde geliştirme aracı izi, demo dili veya proje içi teknik not olmamalı.

## P4 - Teslim ve Portföy

1. GitHub temizlik
   - Ham CSV, DuckDB, credential, output dump commitlenmemeli.
   - README proje hikayesini net anlatmalı.
   - `powerbi/fraud_project_v2.pbix` ana teslim olarak kalmalı.

2. Demo akışı
   - 3 dakikalık kısa anlatım hazırlanmalı.
   - 10 dakikalık teknik walkthrough hazırlanmalı.
   - dbt lineage ve BigQuery dataset yapısı gösterilebilir olmalı.

3. Final kabul
   - Power BI açılır.
   - BigQuery bağlantısı çalışır.
   - dbt build geçer.
   - Rapor 6 ana sunum sayfası ve 1 canlı analitik kontrol sayfasıyla doludur.
   - Analiz hikayesi savunulabilir ve profesyoneldir.
