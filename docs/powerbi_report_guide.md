# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Mevcut Teknik Durum

`fraud_project_v2.pbix` BigQuery DirectQuery veri modelini koruyan açılabilir ana teslim dosyasıdır. Rapor 6 ana Türkçe sunum sayfası ve 1 canlı analitik kontrol sayfasından oluşur.

Son paket doğrulaması:

- Sayfa sayısı: 7
- Visual container sayısı: 63
- Native query-bound visual sayısı: 40
- Slicer sayısı: 6
- Kayıtlı analiz görseli: 24
- PBIX zip bütünlüğü: PASS

## Sayfa 1 - Yönetici Özeti

Ana mesaj: Fraud düşük frekanslıdır fakat belirli segmentlerde yoğunlaşır.

İçerik:

- Native KPI kartları: toplam işlem, sahte işlem, baz sahtecilik oranı, identity kapsama.
- Native slicer: ürün filtresi.
- Native chart: ürün bazlı fraud oranı.
- Native chart: risk bandı lift.
- Native table: risk bandı inceleme kuyruğu.
- Destek görseli: üst yönetim aksiyon matrisi.

## Sayfa 2 - Risk Konsantrasyonu

Ana mesaj: Risk ürün, cihaz ve identity segmentlerinde homojen dağılmaz.

İçerik:

- Native slicer: ürün.
- Native slicer: risk bandı.
- Native table: product/device risk kırılımı.
- Native chart: product/device lift.
- Native chart: cihaz kırılımı fraud oranı.
- Native table: risk bandı yakalama payı.
- Destek görseli: segment watchlist.

## Sayfa 3 - Tutar ve Zaman Analizi

Ana mesaj: Fraud davranışı tutar ve zaman ekseninde doğrusal değildir.

İçerik:

- Native slicer: tutar bandı.
- Native chart: amount band fraud oranı.
- Native line chart: 7 günlük fraud trendi.
- Native table: günlük drift izleme.
- Destek görseli: fraud tutar dağılımı.

## Sayfa 4 - Ödeme ve Email Segmentleri

Ana mesaj: Ödeme tipi ve email domain grupları operasyonel izleme segmentleri üretir.

İçerik:

- Native slicer: email domain grubu.
- Native chart: kart ağı sahte işlem adedi.
- Native chart: kart tipi sahte işlem adedi.
- Native bar chart: email domain fraud oranı.
- Native table: email domain risk ve lift.
- Destek görselleri: ödeme heatmap ve karar matrisi.

## Sayfa 5 - Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru kararın kendisi değil, operasyonel önceliklendirme katmanıdır.

İçerik:

- Native slicer: risk bandı.
- Native chart: risk bandı gözlenen fraud oranı.
- Native chart: risk bandı yakalama payı.
- Native table: model inceleme kuyruğu.
- Destek görselleri: feature importance ve review strategy.

## Sayfa 6 - Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi, test kapsamı ve lineage raporun güvenilirlik temelidir.

İçerik:

- Native table: feature missingness izleme.
- Native bar chart: feature ailesi eksiklik skoru.
- Native KPI kartları: profil edilen satır ve eksik değer sinyali.
- Destek görselleri: dbt kalite kapısı ve mimari akış.

## Sayfa 7 - Canlı Analitik Katmanı

Ana mesaj: Raporun veri modeli Power BI içinde çalışan native görsellerle doğrulanır.

İçerik:

- Native card: toplam işlem.
- Native card: sahte işlem.
- Native card: baz sahtecilik oranı.
- Native card: identity kapsama oranı.
- Native column chart: tutar bandı sahtecilik oranı.
- Native line chart: 7 günlük sahtecilik oranı.
- Native bar chart: email domain sahtecilik oranı.
- Native table: risk bandı inceleme kuyruğu.
- Native table: feature eksiklik izleme listesi.

## Format Standardı

- Dil: Türkçe
- Başlıklar: kısa, yönetici seviyesinde, tek mesajlı
- Renkler: koyu lacivert, kırmızı risk, petrol yeşili, nötr gri
- Sayfa düzeni: üstte ana mesaj, ortada analiz, altta aksiyon veya kanıt
- Yüzdeler yüzde formatında, işlem sayıları binlik ayraçla, tutarlar para formatında gösterilmelidir.

## Kabul Kriteri

- Rapor Power BI Desktop içinde açılır.
- DirectQuery modeli `workintech-working.fraud_project_powerbi` veri katmanını kullanır.
- 6 ana sayfa sunum anlatısını eksiksiz verir.
- Her ana sayfada veri modeline bağlı native visual vardır.
- 7. sayfadaki native görseller veri döndürür.
- Rapor içinde proje dışı üretim izi veya demo dili bulunmaz.
