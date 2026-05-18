# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Mevcut Teknik Durum

`fraud_project_v2.pbix` BigQuery DirectQuery veri modelini koruyan açılabilir ana teslim dosyasıdır. Rapor 6 ana Türkçe sunum sayfası ve 1 canlı analitik kontrol sayfasından oluşur.

Son paket doğrulaması:

- Sayfa sayısı: 7
- Visual container sayısı: 46
- Native query-bound visual sayısı: 9
- Kayıtlı analiz görseli: 24
- PBIX zip bütünlüğü: PASS

## Sayfa 1 - Yönetici Özeti

Ana mesaj: Fraud düşük frekanslıdır fakat belirli segmentlerde yoğunlaşır.

İçerik:

- Yönetici KPI kontrol paneli
- Product C fraud lift
- Identity kaydı var/yok risk ayrımı
- Risk yakalama hunisi
- Üst yönetim aksiyon matrisi

## Sayfa 2 - Risk Konsantrasyonu

Ana mesaj: Risk ürün, cihaz ve identity segmentlerinde homojen dağılmaz.

İçerik:

- Operasyonel segment watchlist
- Product lift analizi
- Identity lift analizi
- Product/device risk kırılımı

## Sayfa 3 - Tutar ve Zaman Analizi

Ana mesaj: Fraud davranışı tutar ve zaman ekseninde doğrusal değildir.

İçerik:

- Tutar bandı fraud oranı
- Fraud tutar dağılımı
- Günlük fraud rate drift trendi
- Gün içi işlem hacmi ve fraud oranı

## Sayfa 4 - Ödeme ve Email Segmentleri

Ana mesaj: Ödeme tipi ve email domain grupları operasyonel izleme segmentleri üretir.

İçerik:

- Kart network x kart tipi heatmap
- Email domain fraud oranı
- Üst yönetim karar matrisi

## Sayfa 5 - Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru kararın kendisi değil, operasyonel önceliklendirme katmanıdır.

İçerik:

- Model eşik simülasyonu
- Risk bandı inceleme stratejisi
- Feature importance
- Risk bandı fraud oranı

## Sayfa 6 - Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi, test kapsamı ve lineage raporun güvenilirlik temelidir.

İçerik:

- dbt kalite kapısı
- Feature family missingness
- BigQuery/dbt/Power BI lineage

## Sayfa 7 - Canlı Analitik Katmanı

Ana mesaj: Raporun veri modeli Power BI içinde çalışan native görsellerle doğrulanır.

Native görseller:

- Card: toplam işlem
- Card: sahte işlem
- Card: baz sahtecilik oranı
- Card: identity kapsama oranı
- Column chart: tutar bandı sahtecilik oranı
- Line chart: 7 günlük sahtecilik oranı
- Bar chart: email domain sahtecilik oranı
- Table: risk bandı inceleme kuyruğu
- Table: feature eksiklik izleme listesi

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
- 7. sayfadaki native görseller veri döndürür.
- Rapor içinde proje dışı üretim izi veya demo dili bulunmaz.
