# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Final Durum

`fraud_project_v2.pbix` BigQuery DirectQuery veri modelini koruyan ana teslim dosyasıdır. Rapor 6 Türkçe sunum sayfasından oluşur ve yalnızca native Power BI görselleriyle yapılandırılmıştır.

Son paket doğrulaması:

- Sayfa sayısı: 6
- Visual container sayısı: 159
- Query-bound native visual sayısı: 29
- Slicer sayısı: 6
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- PBIX zip bütünlüğü: PASS
- Stil verilen container sayısı: 53
- Tema: kurumsal fraud-risk paleti

## Sayfa 1 - Yönetici Özeti

Ana mesaj: Fraud düşük frekanslıdır fakat belirli segmentlerde yoğunlaşır.

İçerik:

- KPI kartları: toplam işlem, sahte işlem, baz fraud oranı, identity kapsama.
- Ürün filtresi.
- Ürün kırılımında fraud oranı.
- Risk bandı gözlenen fraud oranı.
- Tutar bandına göre risk.
- Yönetim aksiyon metinleri.
- Bulgu, risk ve aksiyon karar panelleri.

## Sayfa 2 - Risk Konsantrasyonu

Ana mesaj: Risk ürün, cihaz ve risk bandı segmentlerinde homojen dağılmaz.

İçerik:

- Ürün filtresi.
- Risk bandı filtresi.
- Ürün bazlı risk ayrışması.
- Cihaz tipine göre risk.
- Risk bandı öncelik sırası.
- Karar mesajı: Product C ve mobil/identity sinyalleri öncelikli izlenmelidir.
- Bulgu, öncelik ve kontrol karar panelleri.

## Sayfa 3 - Tutar ve Zaman Analizi

Ana mesaj: Fraud davranışı tutar ve işlem saati ekseninde doğrusal değildir.

İçerik:

- Tutar bandı filtresi.
- Tutar bandı fraud oranı.
- Gün içi sahte işlem adedi.
- Tutar bandı işlem hacmi.
- Zaman ve tutar yorum metni.
- Bulgu, zaman ve aksiyon karar panelleri.

## Sayfa 4 - Ödeme ve Email Segmentleri

Ana mesaj: Ödeme tipi ve email domain grupları operasyonel izleme segmentleri üretir.

İçerik:

- Email grubu filtresi.
- Kart ağına göre sahte işlem adedi.
- Kart tipine göre sahte işlem adedi.
- Email domain fraud oranı.
- Segment karar mesajı.
- Bulgu, segment ve aksiyon karar panelleri.

## Sayfa 5 - Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru kararın kendisi değil, operasyonel önceliklendirme katmanıdır.

İçerik:

- Risk bandı filtresi.
- Risk bandı gözlenen fraud oranı.
- Risk bandı sahte işlem hacmi.
- Risk bandı işlem tutarı.
- Modelin inceleme kuyruğu oluşturma rolünü açıklayan metinler.
- Amaç, operasyon ve yönetim karar panelleri.

## Sayfa 6 - Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi, test kapsamı ve lineage raporun güvenilirlik temelidir.

İçerik:

- Feature ailesi eksiklik oranı.
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
- Görseller: yalnızca card, slicer, clusteredColumnChart, clusteredBarChart ve textbox.
- Karar panelleri: gerçek mart sonuçlarından türetilmiş kısa yönetici bulguları.

## Kabul Kriteri

- Rapor Power BI Desktop içinde açılır.
- DirectQuery modeli `workintech-working.fraud_project_powerbi` veri katmanını kullanır.
- 6 sayfanın tamamı sunum anlatısını eksiksiz verir.
- Her sayfada veri modeline bağlı native visual vardır.
- Rapor içinde proje dışı üretim izi veya sunum dışı teknik not bulunmaz.
