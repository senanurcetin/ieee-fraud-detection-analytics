# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project.pbix
```

## 1. Yönetici Özeti

Amaç: Fraud probleminin büyüklüğünü ve ana risk ayrışmalarını tek sayfada göstermek.

İçerik:

- Toplam işlem ve fraud oranı
- Sınıf dengesizliği
- Product C risk lift
- Identity varlığına göre fraud ayrışması
- Kritik risk bandı lift analizi

## 2. Risk Konsantrasyonu

Amaç: Fraud riskinin ürün ve identity kırılımlarında nasıl yoğunlaştığını göstermek.

İçerik:

- ProductCD bazlı fraud oranı
- Device type kırılımları
- Identity kaydı olan ve olmayan işlemler
- Yüksek riskli ürün-device kombinasyonları

## 3. Tutar ve Zaman Analizi

Amaç: İşlem tutarı ve zaman penceresinin fraud davranışındaki rolünü göstermek.

İçerik:

- Tutar bandı fraud oranları
- İşlem tutarı dağılımı
- Günlük fraud oranı drift görünümü
- Göreli saat bazında hacim ve fraud oranı

## 4. Ödeme ve Email Segmentleri

Amaç: Ödeme tipi ve email domain gruplarının operasyonel segment üretip üretmediğini göstermek.

İçerik:

- Kart ağı ve kart tipi heatmap analizi
- Email domain fraud oranı
- Hacim ve risk birlikte yorumlama

## 5. Model Skorlama ve Risk Bantları

Amaç: Model skorlarının operasyonel önceliklendirme katmanına nasıl çevrildiğini göstermek.

İçerik:

- Feature importance
- Validasyon ROC eğrisi
- Risk bandı bazlı fraud oranı
- Kritik ve yüksek risk bantları

## 6. Veri Kalitesi ve Mimari

Amaç: Analizin veri güvenilirliği ve mimari izlenebilirliğini göstermek.

İçerik:

- Feature ailesi bazında eksiklik oranı
- dbt katman mimarisi
- Veri ambarı akışı
- Raporlama katmanı ve test kapsamı

## Sunum Akışı

Sunum, önce problemin büyüklüğünü ve ana KPI'ları göstermelidir. Ardından riskin belirli segmentlerde yoğunlaştığı kanıtlanmalı, model skorları ise en son operasyonel önceliklendirme katmanı olarak anlatılmalıdır. Teknik mimari sayfası ana hikayenin sonunda güvenilirlik ve sürdürülebilirlik kanıtı olarak kullanılmalıdır.
