# Power BI Teslimi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Bu dosya Türkçe, yönetici sunumuna hazır fraud-risk raporudur. Rapor BigQuery DirectQuery veri modelini korur ve final raporlama katmanı olarak `workintech-working.fraud_project_powerbi` datasetini kullanır.

## Sunum Yapısı

Rapor 6 sayfadan oluşur:

1. Yönetici Özeti
2. Risk Konsantrasyonu
3. Tutar ve Zaman Analizi
4. Ödeme ve Email Segmentleri
5. Model Skorlama ve Risk Bantları
6. Veri Kalitesi ve Mimari

Her sayfa aynı karar akışını izler: üstte tek yönetici mesajı, ortada veri kanıtı, altta kısa bulgu/kanıt/karar veya kalite panelleri.

## Tasarım Standardı

- Dil: Türkçe.
- Teslim formatı: PBIX only.
- Görsel tipi standardı: textbox, slicer, clustered column chart, clustered bar chart ve kontrollü native tablo.
- KPI standardı: Power BI otomatik `K`, `M`, `B` kısaltmasına düşmeyen metin tabanlı sunum değerleri.
- Slicer standardı: koyu başlık şeridi, iç panel ve filtre kontrol alanı ile rapor tasarımına bağlı görünüm.
- Header standardı: sayfa numarası, sunuma hazır etiketi ve aktif sayfa vurgulu alt navigasyon.
- Karar panelleri: gerçek mart sonuçlarından türetilmiş kısa yönetici bulguları.

## DAX Ölçü Katmanı

25 hazır DAX ölçüsü şu dosyada tutulur:

```text
powerbi/dax/fraud_project_measures.dax
```

PBIX model metadata'sı binary olduğu için ölçüler Power BI Desktop modelleme ekranında uygulanmak üzere ayrı teslim edilir; PBIX içine zorla gömülmez.

## Son Otomatik Doğrulama

Komut:

```powershell
python scripts\validate_powerbi_report.py
```

Sonuç:

- PBIX paket bütünlüğü: PASS
- Sayfa sayısı: 6
- Visual container sayısı: 349
- Query-bound native visual sayısı: 27
- Slicer sayısı: 6
- Kontrollü native tablo sayısı: 4
- Tooltip destekli analiz görseli sayısı: 14
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- Native card visual sayısı: 0
- Native visual başlık sızıntısı: 0
- Ham alan adı sızıntısı: 0
- Güvenli alan ihlali: 0
- Metin kırpılma riski: 0

## Kalan Manuel Kontrol

Power BI Desktop komut satırında bulunamadığı için otomatik açılış kontrolü yapılamadı. Desktop erişimi olduğunda şu iki kontrol tamamlanmalıdır:

- `powerbi/fraud_project_v2.pbix` Power BI Desktop içinde açılır.
- DirectQuery yenilemesi sonrasında tüm sayfalardaki veri bağlı görseller veri döndürür.
