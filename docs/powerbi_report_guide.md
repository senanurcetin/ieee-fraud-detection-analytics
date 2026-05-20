# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Final Durum

`fraud_project_v2.pbix`, BigQuery DirectQuery veri modelini koruyan Türkçe yönetici sunumu raporudur. Rapor 6 sayfadan oluşur ve yalnızca native Power BI görselleriyle yapılandırılmıştır.

Son otomatik paket doğrulaması:

- Sayfa sayısı: 6
- Visual container sayısı: 349
- Query-bound native visual sayısı: 27
- Slicer sayısı: 6
- Kontrollü native kanıt tablosu sayısı: 4
- Tooltip destekli analiz görseli sayısı: 14
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- PBIX zip bütünlüğü: PASS
- Başlık kırpılma kontrolü: PASS
- Native visual başlığı sızma kontrolü: PASS
- Otomatik Power BI paket kontrolü: `python scripts/validate_powerbi_report.py` PASS

## Sayfa Akışı

### 1. Yönetici Özeti

Ana mesaj: Fraud riski az sayıda segmentte yönetilebilir hale geliyor.

İçerik:

- Toplam işlem, sahte işlem, baz fraud oranı ve identity kapsama KPI'ları.
- Ürün filtresi.
- Ürün, risk bandı ve tutar bandı bazında sahte işlem hacmi.
- Bulgu, kanıt ve karar panelleri.

### 2. Risk Konsantrasyonu

Ana mesaj: Ürün, cihaz ve risk bandı operasyon önceliğini belirliyor.

İçerik:

- Ürün ve risk bandı filtreleri.
- Ürün/risk bandı kanıt tablosu.
- Ürün, cihaz tipi ve risk bandı bazında sahte işlem hacmi.
- Risk renk standardı.
- Bulgu, kanıt ve aksiyon panelleri.

### 3. Tutar ve Zaman Analizi

Ana mesaj: Tutar ve saat pencereleri doğrusal olmayan risk sinyali veriyor.

İçerik:

- Tutar bandı filtresi.
- Tutar bandı kanıt tablosu.
- Tutar bandı, işlem saati ve işlem hacmi grafikleri.
- Bulgu, kanıt ve aksiyon panelleri.

### 4. Ödeme ve Email Segmentleri

Ana mesaj: Ödeme ve email kırılımları izlenebilir operasyon segmentleri üretiyor.

İçerik:

- Email grubu filtresi.
- Ödeme segmenti kanıt tablosu.
- Kart ağı, kart tipi ve email grubu bazında sahte işlem hacmi.
- Bulgu, kanıt ve aksiyon panelleri.

### 5. Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru karar değil, inceleme kuyruğu önceliğidir.

İçerik:

- Risk bandı filtresi.
- Risk bandı inceleme kanıt tablosu.
- Gözlenen fraud oranı, sahte işlem hacmi ve işlem tutarı grafikleri.
- Risk renk standardı.
- Bulgu, kanıt ve karar panelleri.

### 6. Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi ve lineage rapor güvenilirliğini kanıtlıyor.

İçerik:

- dbt build, reconciliation ve lineage kalite kapısı panelleri.
- Feature ailesi bazında eksik değer hacmi.
- Profil edilen satır ve eksik değer sinyali KPI'ları.
- Lineage: `Kaggle CSV -> BigQuery Raw -> dbt Staging -> dbt Mart -> Power BI DirectQuery`.

## Format Standardı

- Görünen başlıklar Türkçe ve yönetici seviyesinde olmalıdır.
- Ham alan adları rapor yüzeyinde görünmemelidir.
- Native visual başlıkları kapalı kalmalıdır; görünen başlıklar ayrı panel başlığıdır.
- Slicer alanları çıplak checkbox görünümünde bırakılmamalıdır.
- KPI değerleri otomatik sayı kısaltması üretmemelidir.
- Her sayfa tek ana mesaj taşımalıdır.
- Karar panelleri kısa, sayısal ve aksiyon odaklı olmalıdır.

## Kabul Kriteri

- Rapor Power BI Desktop içinde açılır.
- DirectQuery modeli `workintech-working.fraud_project_powerbi` veri katmanını kullanır.
- 6 sayfanın tamamı sunum anlatısını eksiksiz verir.
- Her sayfada veri modeline bağlı native visual vardır.
- Rapor içinde proje dışı üretim izi, geçici not veya sunum dışı teknik dil bulunmaz.
- `python scripts\validate_powerbi_report.py` PASS döner.
