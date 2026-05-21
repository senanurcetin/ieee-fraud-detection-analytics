# Power BI Native Visual Spesifikasyonu

Bu dokÃ¼man, `fraud_project_v2.pbix` dosyasÄ±nÄ±n gÃ¼ncel final rapor standardÄ±nÄ± tanÄ±mlar. Rapor BigQuery DirectQuery modelini korur ve Power BI Desktop iÃ§inde aÃ§Ä±labilir, sade, TÃ¼rkÃ§e yÃ¶netici sunumu dÃ¼zeniyle hazÄ±rlanÄ±r.

## Model KatmanÄ±

Rapor ÅŸu BigQuery raporlama katmanÄ±na baÄŸlÄ±dÄ±r:

```text
your-gcp-project.fraud_project_powerbi
```

Final PBIX iÃ§inde gÃ¼venli ÅŸekilde kullanÄ±lan ana tablolar:

- `fact_train_transactions`
- `mart_fraud_summary`
- `mart_risk_band_stats`
- `mart_feature_missingness`

`pbi_*` tablolarÄ± BigQuery/dbt tarafÄ±nda korunur. Power BI model metadata'sÄ± yenilendikten sonra bu tablolar ek gÃ¶rseller iÃ§in kontrollÃ¼ biÃ§imde devreye alÄ±nabilir.

## GÃ¼ncel Visual StandardÄ±

Final rapor ÅŸu gÃ¶rsel tipleriyle sÄ±nÄ±rlÄ±dÄ±r:

- `textbox`
- `slicer`
- `clusteredColumnChart`
- `clusteredBarChart`
- kontrollÃ¼ native tablo

Native card kullanÄ±lmaz. KPI alanlarÄ± Power BI otomatik sayÄ± kÄ±saltmasÄ±na dÃ¼ÅŸmemesi iÃ§in metin tabanlÄ± sunum formatÄ±yla gÃ¶sterilir.

25 hazÄ±r DAX Ã¶lÃ§Ã¼sÃ¼ ÅŸu dosyadadÄ±r:

```text
powerbi/dax/fraud_project_measures.dax
```

Otomatik paket kontrolÃ¼:

```powershell
python scripts\validate_powerbi_report.py
```

Bu kontrol sayfa sayÄ±sÄ±nÄ±, gÃ¶rsel tiplerini, gÃ¶mÃ¼lÃ¼ gÃ¶rsel kaynaklarÄ±nÄ±, ham alan adÄ± referanslarÄ±nÄ±, tooltip kapsamÄ±nÄ±, native baÅŸlÄ±k sÄ±zÄ±ntÄ±sÄ±nÄ±, metin kÄ±rpÄ±lma riskini ve gÃ¼venli alan allowlist'ini doÄŸrular.

## Sayfa BazlÄ± Kurgu

### YÃ¶netici Ã–zeti

- KPI gÃ¶stergeleri: toplam iÅŸlem, sahte iÅŸlem, baz fraud oranÄ±, identity kapsama.
- ÃœrÃ¼n filtresi.
- ÃœrÃ¼ne gÃ¶re sahte iÅŸlem hacmi.
- Risk bandÄ±na gÃ¶re sahte iÅŸlem hacmi.
- Tutar bandÄ±na gÃ¶re sahte iÅŸlem hacmi.
- Bulgu, risk ve aksiyon karar metinleri.

### Risk Konsantrasyonu

- ÃœrÃ¼n filtresi.
- Risk bandÄ± filtresi.
- ÃœrÃ¼n bazlÄ± sahte iÅŸlem hacmi.
- Cihaz tipine gÃ¶re sahte iÅŸlem hacmi.
- Risk bandÄ± sahte iÅŸlem hacmi.
- ÃœrÃ¼n ve risk bandÄ± kanÄ±t tablosu.
- Risk renk standardÄ±.

### Tutar ve Zaman Analizi

- Tutar bandÄ± filtresi.
- Tutar bandÄ±na gÃ¶re sahte iÅŸlem hacmi.
- GÃ¼n iÃ§i sahte iÅŸlem adedi.
- Tutar bandÄ± iÅŸlem hacmi.
- Tutar bandÄ± kanÄ±t tablosu.
- Zaman ve tutar karar metinleri.

### Ã–deme ve Email Segmentleri

- Email grubu filtresi.
- Kart aÄŸÄ±na gÃ¶re sahte iÅŸlem adedi.
- Kart tipine gÃ¶re sahte iÅŸlem adedi.
- Email grubuna gÃ¶re sahte iÅŸlem hacmi.
- Ã–deme segmenti kanÄ±t tablosu.

### Model Skorlama ve Risk BantlarÄ±

- Risk bandÄ± filtresi.
- Risk bandÄ± gÃ¶zlenen fraud oranÄ±.
- Risk bandÄ± sahte iÅŸlem hacmi.
- Risk bandÄ± iÅŸlem tutarÄ±.
- Risk bandÄ± inceleme kanÄ±t tablosu.
- Modelin karar deÄŸil Ã¶nceliklendirme katmanÄ± olduÄŸunu anlatan karar metinleri.

### Veri Kalitesi ve Mimari

- Feature ailesi eksik deÄŸer hacmi.
- Eksik deÄŸer hacmi.
- Profil edilen satÄ±r KPI'Ä±.
- Eksik deÄŸer sinyali KPI'Ä±.
- Lineage: `Kaggle CSV -> BigQuery Raw -> dbt Staging -> dbt Mart -> Power BI DirectQuery`.
- dbt build ve BigQuery row-count kalite mesajÄ±.

## Format KurallarÄ±

- GÃ¶rÃ¼nen baÅŸlÄ±klar TÃ¼rkÃ§e ve yÃ¶netici dilinde olmalÄ±dÄ±r.
- Ham alan adlarÄ± rapor yÃ¼zeyinde gÃ¶rÃ¼nmemelidir.
- Native visual baÅŸlÄ±klarÄ± kapalÄ± olmalÄ±; chart baÅŸlÄ±klarÄ± ayrÄ± panel baÅŸlÄ±ÄŸÄ± olarak verilmelidir.
- Slicer alanlarÄ± Ã§Ä±plak checkbox gÃ¶rÃ¼nÃ¼mÃ¼nde bÄ±rakÄ±lmamalÄ±; baÅŸlÄ±k ÅŸeridi, iÃ§ panel ve vurgu Ã§izgisiyle rapor tasarÄ±mÄ±na baÄŸlanmalÄ±dÄ±r.
- KPI deÄŸerlerinde otomatik `B`, `K`, `M` kÄ±saltmasÄ± gÃ¶rÃ¼nmemelidir.
- YalnÄ±zca iÅŸlevsel panel sistemi kullanÄ±lmalÄ±dÄ±r.
- Renk standardÄ±: kÄ±rmÄ±zÄ± kritik risk, petrol yeÅŸili kontrol/aksiyon, koyu lacivert ana metin, nÃ¶tr gri ikincil metin.
- Ã–nemli chart gÃ¶rsellerinde iÅŸlem tutarÄ± veya sahte iÅŸlem adedi gibi tooltip baÄŸlamÄ± bulunmalÄ±dÄ±r.
- Her sayfa tek ana mesaj taÅŸÄ±malÄ±dÄ±r.
