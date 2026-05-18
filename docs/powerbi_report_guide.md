# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Mevcut Teknik Durum

`fraud_project_v2.pbix` açılır durumdadır ve BigQuery DirectQuery veri modelini korur. Rapor içinde 6 Türkçe sayfa vardır. Mevcut layout, açılabilir teslimi garanti etmek için metin kutuları ve gömülü analiz görselleriyle yapılandırılmıştır.

Bir sonraki kalite seviyesi, bu sayfaların Power BI Desktop içinde native visual setine çevrilmesidir. Bunun için veri katmanı hazırdır: tüm rapor sayfaları `workintech-working.fraud_project_powerbi` datasetindeki `fact_*` ve `pbi_*` tablolarından beslenmelidir.

## Sayfa 1 - Yönetici Özeti

Ana mesaj: Fraud düşük frekanslıdır fakat belirli segmentlerde yoğunlaşır.

Kullanılacak tablolar:

- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_identity_risk`
- `pbi_model_risk_bands`

Native visual hedefleri:

- KPI card: toplam işlem
- KPI card: fraud oranı
- KPI card: fraud işlem sayısı
- KPI card: kritik risk bandı fraud oranı
- Bar chart: ProductCD bazında fraud rate ve lift
- Bar chart: identity var/yok fraud rate
- Column chart: risk bandı lift

## Sayfa 2 - Risk Konsantrasyonu

Ana mesaj: Risk ürün, cihaz ve identity segmentlerinde homojen dağılmaz.

Kullanılacak tablolar:

- `pbi_product_risk`
- `pbi_identity_risk`
- `mart_product_device_stats`
- `pbi_report_narrative`

Native visual hedefleri:

- Bar chart: product bazında lift
- Matrix: product/device segmentleri
- KPI card: en yüksek lift
- KPI card: en yüksek fraud share
- Table: önerilen aksiyon mesajı

## Sayfa 3 - Tutar ve Zaman Analizi

Ana mesaj: Fraud davranışı tutar ve zaman ekseninde doğrusal değildir.

Kullanılacak tablolar:

- `pbi_amount_bands`
- `pbi_daily_drift`

Native visual hedefleri:

- Combo chart: günlük işlem hacmi ve fraud rate
- Line chart: 7 günlük fraud rate hareketli ortalama
- Bar chart: amount band fraud rate
- Table: drift flag günleri
- KPI card: p95 işlem tutarı

## Sayfa 4 - Ödeme ve Email Segmentleri

Ana mesaj: Ödeme tipi ve email domain grupları operasyonel izleme segmentleri üretir.

Kullanılacak tablolar:

- `pbi_payment_heatmap`
- `pbi_email_domain_risk`

Native visual hedefleri:

- Matrix heatmap: card network x card type fraud rate
- Bar chart: email domain fraud rate
- Bar chart: email domain fraud share
- KPI card: en yüksek email lift
- KPI card: en yüksek ödeme segment lift

## Sayfa 5 - Model Skorlama ve Risk Bantları

Ana mesaj: Model skoru kararın kendisi değil, operasyonel önceliklendirme katmanıdır.

Kullanılacak tablolar:

- `pbi_model_risk_bands`
- `pbi_feature_importance`
- `fact_train_transactions`

Native visual hedefleri:

- Bar chart: risk bandı fraud rate
- Bar chart: risk bandı lift
- Bar chart: top 15 feature importance
- KPI card: critical risk fraud rate
- KPI card: high + critical işlem hacmi

## Sayfa 6 - Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi, test kapsamı ve lineage raporun güvenilirlik temelidir.

Kullanılacak tablolar:

- `pbi_data_quality_scorecard`
- `pbi_quality_contract`
- `pbi_report_narrative`

Native visual hedefleri:

- Table: kalite kontratı PASS/FAIL
- Bar chart: feature family bazında ortalama missing rate
- KPI card: toplam dbt test sayısı
- KPI card: source row-count kontrol sonucu
- Text/table: mimari ve kalite mesajı

## Format Standardı

- Dil: Türkçe
- Başlıklar: kısa, yönetici seviyesinde, tek mesajlı
- Renkler: koyu lacivert, kırmızı risk, petrol yeşili, nötr gri
- Sayfa düzeni: üstte KPI alanı, ortada ana görsel, altta detay tablo veya aksiyon mesajı
- Tüm yüzdeler yüzde formatında, işlem sayıları binlik ayracıyla, tutarlar para formatında gösterilmelidir.

## Kabul Kriteri

- 6 sayfa görünür ve boş değildir.
- Her sayfada en az 3 native Power BI visual vardır.
- Her visual `fraud_project_powerbi` datasetindeki tablolardan beslenir.
- Rapor DirectQuery modunda kalır.
- Sayfalarda geliştirme aracı, yapay üretim izi veya demo dili bulunmaz.
