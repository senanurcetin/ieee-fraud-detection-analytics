# IEEE-CIS Fraud Detection Yönetici Özeti

## Temel Metrikler

- Toplam işlem: 590,540
- Sahtecilik etiketi taşıyan işlem: 20,663
- Sahtecilik oranı: 3.50%
- Identity kapsama oranı: 24.42%
- Medyan işlem tutarı: $68.77
- P95 işlem tutarı: $445.00
- Doğrulama AUC: 0.917
- Doğrulama average precision: 0.531

## Yönetici Çıkarımı

Veri seti, nadir görülen ancak belirli segmentlerde yoğunlaşan bir sahtecilik problemidir. Risk; ürün ailesi, identity kaydı, ödeme tipi, email domain, işlem tutarı ve zaman penceresine göre belirgin biçimde ayrışır. Önerilen analitik model; ham veri katmanı, dbt dönüşümleri, LightGBM skorlaması ve Power BI için hazırlanmış mart tablolarından oluşur.
