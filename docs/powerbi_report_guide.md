# Power BI Rapor Rehberi

Ana dosya:

```text
powerbi/fraud_project_v2.pbix
```

## Final Durum

`fraud_project_v2.pbix`, BigQuery DirectQuery veri modelini koruyan TÃ¼rkÃ§e yÃ¶netici sunumu raporudur. Rapor 6 sayfadan oluÅŸur ve yalnÄ±zca native Power BI gÃ¶rselleriyle yapÄ±landÄ±rÄ±lmÄ±ÅŸtÄ±r.

Son otomatik paket doÄŸrulamasÄ±:

- Sayfa sayÄ±sÄ±: 6
- Visual container sayÄ±sÄ±: 349
- Query-bound native visual sayÄ±sÄ±: 27
- Slicer sayÄ±sÄ±: 6
- KontrollÃ¼ native kanÄ±t tablosu sayÄ±sÄ±: 4
- Tooltip destekli analiz gÃ¶rseli sayÄ±sÄ±: 14
- GÃ¶mÃ¼lÃ¼ gÃ¶rÃ¼ntÃ¼ visual sayÄ±sÄ±: 0
- KayÄ±tlÄ± gÃ¶rsel kaynaÄŸÄ±: 0
- PBIX zip bÃ¼tÃ¼nlÃ¼ÄŸÃ¼: PASS
- BaÅŸlÄ±k kÄ±rpÄ±lma kontrolÃ¼: PASS
- Native visual baÅŸlÄ±ÄŸÄ± sÄ±zma kontrolÃ¼: PASS
- Otomatik Power BI paket kontrolÃ¼: `python scripts/validate_powerbi_report.py` PASS

## Sayfa AkÄ±ÅŸÄ±

### 1. YÃ¶netici Ã–zeti

Ana mesaj: Fraud riski az sayÄ±da segmentte yÃ¶netilebilir hale geliyor.

Ä°Ã§erik:

- Toplam iÅŸlem, sahte iÅŸlem, baz fraud oranÄ± ve identity kapsama KPI'larÄ±.
- ÃœrÃ¼n filtresi.
- ÃœrÃ¼n, risk bandÄ± ve tutar bandÄ± bazÄ±nda sahte iÅŸlem hacmi.
- Bulgu, kanÄ±t ve karar panelleri.

### 2. Risk Konsantrasyonu

Ana mesaj: ÃœrÃ¼n, cihaz ve risk bandÄ± operasyon Ã¶nceliÄŸini belirliyor.

Ä°Ã§erik:

- ÃœrÃ¼n ve risk bandÄ± filtreleri.
- ÃœrÃ¼n/risk bandÄ± kanÄ±t tablosu.
- ÃœrÃ¼n, cihaz tipi ve risk bandÄ± bazÄ±nda sahte iÅŸlem hacmi.
- Risk renk standardÄ±.
- Bulgu, kanÄ±t ve aksiyon panelleri.

### 3. Tutar ve Zaman Analizi

Ana mesaj: Tutar ve saat pencereleri doÄŸrusal olmayan risk sinyali veriyor.

Ä°Ã§erik:

- Tutar bandÄ± filtresi.
- Tutar bandÄ± kanÄ±t tablosu.
- Tutar bandÄ±, iÅŸlem saati ve iÅŸlem hacmi grafikleri.
- Bulgu, kanÄ±t ve aksiyon panelleri.

### 4. Ã–deme ve Email Segmentleri

Ana mesaj: Ã–deme ve email kÄ±rÄ±lÄ±mlarÄ± izlenebilir operasyon segmentleri Ã¼retiyor.

Ä°Ã§erik:

- Email grubu filtresi.
- Ã–deme segmenti kanÄ±t tablosu.
- Kart aÄŸÄ±, kart tipi ve email grubu bazÄ±nda sahte iÅŸlem hacmi.
- Bulgu, kanÄ±t ve aksiyon panelleri.

### 5. Model Skorlama ve Risk BantlarÄ±

Ana mesaj: Model skoru karar deÄŸil, inceleme kuyruÄŸu Ã¶nceliÄŸidir.

Ä°Ã§erik:

- Risk bandÄ± filtresi.
- Risk bandÄ± inceleme kanÄ±t tablosu.
- GÃ¶zlenen fraud oranÄ±, sahte iÅŸlem hacmi ve iÅŸlem tutarÄ± grafikleri.
- Risk renk standardÄ±.
- Bulgu, kanÄ±t ve karar panelleri.

### 6. Veri Kalitesi ve Mimari

Ana mesaj: Veri kalitesi ve lineage rapor gÃ¼venilirliÄŸini kanÄ±tlÄ±yor.

Ä°Ã§erik:

- dbt build, reconciliation ve lineage kalite kapÄ±sÄ± panelleri.
- Feature ailesi bazÄ±nda eksik deÄŸer hacmi.
- Profil edilen satÄ±r ve eksik deÄŸer sinyali KPI'larÄ±.
- Lineage: `Kaggle CSV -> BigQuery Raw -> dbt Staging -> dbt Mart -> Power BI DirectQuery`.

## Format StandardÄ±

- GÃ¶rÃ¼nen baÅŸlÄ±klar TÃ¼rkÃ§e ve yÃ¶netici seviyesinde olmalÄ±dÄ±r.
- Ham alan adlarÄ± rapor yÃ¼zeyinde gÃ¶rÃ¼nmemelidir.
- Native visual baÅŸlÄ±klarÄ± kapalÄ± kalmalÄ±dÄ±r; gÃ¶rÃ¼nen baÅŸlÄ±klar ayrÄ± panel baÅŸlÄ±ÄŸÄ±dÄ±r.
- Slicer alanlarÄ± Ã§Ä±plak checkbox gÃ¶rÃ¼nÃ¼mÃ¼nde bÄ±rakÄ±lmamalÄ±dÄ±r.
- KPI deÄŸerleri otomatik sayÄ± kÄ±saltmasÄ± Ã¼retmemelidir.
- Her sayfa tek ana mesaj taÅŸÄ±malÄ±dÄ±r.
- Karar panelleri kÄ±sa, sayÄ±sal ve aksiyon odaklÄ± olmalÄ±dÄ±r.

## Kabul Kriteri

- Rapor Power BI Desktop iÃ§inde aÃ§Ä±lÄ±r.
- DirectQuery modeli `your-gcp-project.fraud_project_powerbi` veri katmanÄ±nÄ± kullanÄ±r.
- 6 sayfanÄ±n tamamÄ± sunum anlatÄ±sÄ±nÄ± eksiksiz verir.
- Her sayfada veri modeline baÄŸlÄ± native visual vardÄ±r.
- Rapor iÃ§inde proje dÄ±ÅŸÄ± Ã¼retim izi, geÃ§ici not veya sunum dÄ±ÅŸÄ± teknik dil bulunmaz.
- `python scripts\validate_powerbi_report.py` PASS dÃ¶ner.
