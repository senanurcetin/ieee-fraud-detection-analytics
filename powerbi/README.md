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

Rapor yalnızca native Power BI görselleriyle yapılandırılmıştır. Kullanılan görsel tipleri card, slicer, clustered column chart, clustered bar chart ve textbox ile sınırlıdır.

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
- Visual container sayısı: 159
- Query-bound native visual sayısı: 29
- Gömülü görüntü visual sayısı: 0
- Kayıtlı görsel kaynağı: 0
- Kırılgan çizgi grafik ve tablo görseli kullanılmıyor
- Kurumsal fraud-risk teması ve 53 stillendirilmiş container var
- dbt prod build: PASS, 102 PASS / 0 ERROR / 1 exposure NO-OP
- dbt docs generate: PASS
