# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Final Durum

`fraud_project_v2.pbix` BigQuery DirectQuery veri modelini koruyan ana teslim dosyasıdır. Rapor 6 Türkçe sunum sayfasından oluşur ve yalnızca native Power BI görselleriyle yapılandırılmıştır.

Son paket doğrulaması:

- Sayfa sayısı: 6
- Visual container sayısı: 169
- Query-bound native visual sayısı: 27
- Slicer sayısı: 6
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- PBIX zip bütünlüğü: PASS
- Tooltip destekli analiz görseli sayısı: 6
- Kontrollü native kanıt tablosu sayısı: 4
- Tema: kurumsal fraud-risk paleti
- Tasarım kabuğu: sade header, Türkçe visual başlıkları, alt sayfa yönlendirme metni

## Sayfa 1 - Yönetici Özeti

Ana mesaj: Fraud düşük frekanslıdır fakat belirli segmentlerde yoğunlaşır.

İçerik:

- KPI göstergeleri: toplam işlem, sahte işlem, baz fraud oranı, identity kapsama.
- Ürün filtresi.
- Ürüne göre sahte işlem hacmi.
- Risk bandına göre sahte işlem hacmi.
- Tutar bandına göre sahte işlem hacmi.
- Yönetim aksiyon metinleri.
- Bulgu, risk ve aksiyon karar panelleri.

## Sayfa 2 - Risk Konsantrasyonu

Ana mesaj: Risk ürün, cihaz ve risk bandı segmentlerinde homojen dağılmaz.

İçerik:

- Ürün filtresi.
- Risk bandı filtresi.
- Ürün bazlı sahte işlem hacmi.
- Cihaz tipine göre sahte işlem hacmi.
- Risk bandı sahte işlem hacmi.
- Ürün ve risk bandı kanıt tablosu.
- Risk renk standardı.
- Karar mesajı: Product C ve mobil/identity sinyalleri öncelikli izlenmelidir.
- Bulgu, öncelik ve kontrol karar panelleri.

## Sayfa 3 - Tutar ve Zaman Analizi

Ana mesaj: Fraud davranışı tutar ve işlem saati ekseninde doğrusal değildir.

İçerik:

- Tutar bandı filtresi.
- Tutar bandına göre sahte işlem hacmi.
- Gün içi sahte işlem adedi.
- Tutar bandı işlem hacmi.
- Tutar bandı kanıt tablosu.
- Zaman ve tutar yorum metni.
- Bulgu, zaman ve aksiyon karar panelleri.

## Sayfa 4 - Ödeme ve Email Segmentleri

Ana mesaj: Ödeme tipi ve email domain grupları operasyonel izleme segmentleri üretir.

İçerik:

- Email grubu filtresi.
- Kart ağına göre sahte işlem adedi.
- Kart tipine göre sahte işlem adedi.
- Email grubuna göre sahte işlem hacmi.
- Ödeme segmenti kanıt tablosu.
- Segment karar mesajı.
- Bulgu, segment ve aksiyon karar panelleri.

## Sayfa 5 - Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru kararın kendisi değil, operasyonel önceliklendirme katmanıdır.

İçerik:

- Risk bandı filtresi.
- Risk bandı gözlenen fraud oranı.
- Risk bandı sahte işlem hacmi.
- Risk bandı işlem tutarı.
- Risk bandı inceleme kanıt tablosu.
- Risk renk standardı.
- Modelin inceleme kuyruğu oluşturma rolünü açıklayan metinler.
- Amaç, operasyon ve yönetim karar panelleri.

## Sayfa 6 - Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi, test kapsamı ve lineage raporun güvenilirlik temelidir.

İçerik:

- Feature ailesi eksik değer hacmi.
- Eksik değer hacmi.
- Profil edilen satır KPI'ı.
- Eksik değer sinyali KPI'ı.
- Lineage: `Kaggle CSV -> BigQuery Raw -> dbt Staging -> dbt Mart -> Power BI DirectQuery`.
- Kalite mesajı: dbt build ve BigQuery row-count kontrolleri PASS.
- Build, reconciliation ve lineage kalite kapısı panelleri.

## Format Standardı

- Dil: Türkçe.
- Başlıklar: kısa, yönetici seviyesinde, tek mesajlı.
- Renkler: koyu lacivert, kırmızı risk, petrol yeşili, nötr gri.
- Sayfa düzeni: üstte ana mesaj, ortada analiz, altta aksiyon veya kanıt.
- Görseller: slicer, clusteredColumnChart, clusteredBarChart, kontrollü native tablo ve textbox.
- KPI alanları: otomatik kısaltma üretmeyen, sunum formatında metin tabanlı göstergeler.
- Tooltip: hacim, tutar ve sahte işlem sayısı gibi bağlam alanları önemli chart görsellerinde destekleyici bilgi olarak kullanılır.
- Karar panelleri: gerçek mart sonuçlarından türetilmiş kısa yönetici bulguları.
- Sayfa yapısı: sade filtre noktaları, analiz kanıtı, yönetim kararı ve alt yönlendirme düzeni.

## Kabul Kriteri

- Rapor Power BI Desktop içinde açılır.
- DirectQuery modeli `workintech-working.fraud_project_powerbi` veri katmanını kullanır.
- 6 sayfanın tamamı sunum anlatısını eksiksiz verir.
- Her sayfada veri modeline bağlı native visual vardır.
- Rapor içinde proje dışı üretim izi veya sunum dışı teknik not bulunmaz.
