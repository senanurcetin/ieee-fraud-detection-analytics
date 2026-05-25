# 01 - Yönetici Özeti

## Amaç

`fraud_project`, dijital ödeme işlemlerinde sahtecilik riskinin hangi segmentlerde yoğunlaştığını ölçmek ve operasyon ekipleri için önceliklendirilebilir risk katmanları oluşturmak amacıyla hazırlanmıştır. Çalışma, bankacılık fraud analitiği perspektifiyle üst yönetim sunumuna uygun şekilde kurgulanmıştır.

## Veri Kapsamı

- Toplam işlem: 590.540
- Sahtecilik etiketi taşıyan işlem: 20.663
- Gözlenen sahtecilik oranı: %3,50
- Identity kaydı bulunan işlem oranı: %24,42
- Gözlem süresi: 183 göreli işlem günü
- Ürün ailesi sayısı: 5

## Ana Bulgular

1. Sahtecilik nadir görünür, ancak belirli segmentlerde güçlü biçimde yoğunlaşır.
2. Product C, %11,69 fraud oranıyla portföy ortalamasının yaklaşık 3,3 katı risk üretir.
3. Identity kaydı bulunan işlemlerde fraud oranı %7,85; identity kaydı olmayan işlemlerde %2,09 seviyesindedir.
4. Çok düşük tutarlı işlemler ile yüksek tutarlı işlemler orta tutar bantlarına göre daha risklidir.
5. Hotmail ve Gmail domain grupları, hacim ve fraud oranı birlikte değerlendirildiğinde öncelikli izleme segmentleridir.
6. Modelin kritik risk bandında gözlenen fraud oranı %96,31 seviyesine çıkar; bu bant operasyonel inceleme kuyruğu için güçlü bir önceliklendirme sağlar.

## Yönetim Mesajı

Fraud riski tek bir değişkenle açıklanamaz. Ürün ailesi, identity varlığı, ödeme tipi, email domain, tutar ve zaman kırılımları birlikte ele alındığında sahteciliğin rastgele dağılmadığı görülür. Bu nedenle önerilen yaklaşım, segment bazlı iş kuralları ile makine öğrenmesi skorlarını aynı canlı web analitik panelinde birleştiren izlenebilir bir risk yönetimi katmanıdır.

## Çıktılar

- BigQuery üzerinde katmanlı dataset mimarisi
- dbt staging, intermediate ve mart modelleri
- Canlı web dashboard için final raporlama datasetleri
- Türkçe canlı yönetici sunumu
- Model skorlama, risk bandı ve veri kalitesi dokümantasyonu
