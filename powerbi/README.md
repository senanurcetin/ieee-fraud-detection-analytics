# Power BI Teslimi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Rapor 6 sunum sayfasından oluşur:

1. Yönetici Özeti
2. Risk Konsantrasyonu
3. Tutar ve Zaman Analizi
4. Ödeme ve Email Segmentleri
5. Model Skorlama ve Risk Bantları
6. Veri Kalitesi ve Mimari

## Veri Modeli

PBIX dosyası BigQuery DirectQuery veri modelini korur. Final raporlama katmanı `workintech-working.fraud_project_powerbi` datasetidir.

Rapor yalnızca Power BI içinde açılabilen görsellerle yapılandırılmıştır. Kullanılan görsel tipleri slicer, clustered column chart, clustered bar chart, kontrollü native tablo ve textbox ile sınırlıdır; KPI alanları otomatik sayı kısaltması üretmeyecek şekilde metin tabanlı formatlanmıştır.

## Sunum Akışı

Rapor, üst yönetim görüşmesi için önce iş etkisini, sonra riskin nerede yoğunlaştığını, ardından operasyonel izleme ve veri güvenilirliğini anlatır.

- Yönetici Özeti: toplam hacim, fraud oranı, identity kapsama ve ilk aksiyon alanları.
- Risk Konsantrasyonu: ürün, cihaz ve risk bandı kırılımları.
- Tutar ve Zaman Analizi: tutar bandı, saat ve işlem hacmi sinyalleri.
- Ödeme ve Email Segmentleri: kart ağı, kart tipi ve email domain kırılımları.
- Model Skorlama ve Risk Bantları: skorların inceleme kuyruğu olarak kullanımı.
- Veri Kalitesi ve Mimari: missingness izleme, kalite kontrolü ve veri akışı.

## Son Doğrulama

- PBIX paket bütünlüğü: PASS
- Sayfa sayısı: 6
- Visual container sayısı: 169
- Query-bound native visual sayısı: 27
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- Kırılgan çizgi grafik kullanılmıyor
- Kontrollü native kanıt tabloları yalnızca güvenli model alanlarıyla kullanılıyor
- Ham alan adları yerine Türkçe query/visual başlıkları kullanılıyor
- Tooltip destekli analiz görseli sayısı: 6
- Gereksiz dekoratif container'lar kaldırıldı; rapor sade yönetici sunumu gridine indirildi
- dbt prod build: PASS, 102 PASS / 0 ERROR / 1 exposure NO-OP
- dbt docs generate: PASS
