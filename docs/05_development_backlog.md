# 05 - DetaylÄ± GeliÅŸtirme Backlog'u

Bu liste, projenin portfÃ¶y ve Ã¼st yÃ¶netim sunumu seviyesinde korunmasÄ± iÃ§in kalan iÅŸleri Ã¶nceliklendirir. Son iterasyonda ana rapor native Power BI gÃ¶rsellerine taÅŸÄ±ndÄ±ÄŸÄ± iÃ§in backlog artÄ±k bakÄ±m, doÄŸrulama ve kontrollÃ¼ geniÅŸletme odaÄŸÄ±ndadÄ±r.

## P0 - Kritik

1. Power BI Desktop aÃ§Ä±lÄ±ÅŸ testi
   - `powerbi/fraud_project_v2.pbix` Power BI Desktop'ta aÃ§Ä±lmalÄ±.
   - 6 sayfanÄ±n tamamÄ±nda hata placeholder'Ä± olmadÄ±ÄŸÄ± kontrol edilmeli.
   - KPI metinleri, slicer, clustered column chart, clustered bar chart ve kanÄ±t tablolarÄ± doÄŸru gÃ¶rÃ¼nmeli.
   - AÃ§Ä±lÄ±ÅŸ Ã¶ncesi `python scripts/validate_powerbi_report.py` PASS vermeli.

2. DirectQuery veri modeli kontrolÃ¼
   - Rapor `your-gcp-project.fraud_project_powerbi` veri katmanÄ±na baÄŸlÄ± kalmalÄ±.
   - Slicer seÃ§imleri sayfa gÃ¶rsellerini bozmamalÄ±.
   - BigQuery baÄŸlantÄ± yetkisi onaylandÄ±ktan sonra gÃ¶rseller boÅŸ dÃ¶nmemeli.

3. Format kontrolÃ¼
   - KPI alanlarÄ±nda otomatik kÄ±saltma gÃ¶rÃ¼nmemeli; deÄŸerler sunum formatÄ±nda kalmalÄ±.
   - Grafik baÅŸlÄ±klarÄ±nda ham alan adÄ± gÃ¶rÃ¼nmemeli.
   - Grafik baÅŸlÄ±klarÄ± TÃ¼rkÃ§e ve yÃ¶netici seviyesinde kalmalÄ±.

## P1 - GÃ¼Ã§lÃ¼ Analitik

1. Segment lift anlatÄ±mÄ±
   - Product C lift.
   - Identity lift.
   - Risk bandÄ± lift.
   - Email domain lift.
   - Payment segment lift.

2. Risk katkÄ±sÄ± analizi
   - Fraud share ve transaction share birlikte gÃ¶sterilmeli.
   - Sadece fraud rate'e bakÄ±lmamalÄ±; kÃ¼Ã§Ã¼k hacimli segmentlerin yanÄ±ltÄ±cÄ± etkisi aÃ§Ä±klanmalÄ±.

3. Zaman drift analizi
   - GÃ¼nlÃ¼k fraud rate.
   - 7 gÃ¼nlÃ¼k hareketli ortalama.
   - Drift flag.
   - Hacim ile risk trendinin birlikte okunmasÄ±.

4. Model izleme
   - Risk bandÄ± daÄŸÄ±lÄ±mÄ±.
   - Critical ve High bantlarÄ±nda fraud capture.
   - Feature importance.
   - Model skorlarÄ±nÄ±n operasyonel kullanÄ±mÄ±.

## P2 - dbt ve Veri Kalitesi

1. dbt kalite kapÄ±sÄ±
   - `dbt build --target prod` final kalite komutu olarak kullanÄ±lmalÄ±.
   - 73 data test ve singular QA testleri korunmalÄ±.
   - Test baÅŸarÄ±sÄ±zsa Power BI final raporu yenilenmemeli.

2. Power BI veri kontratÄ±
   - `pbi_quality_contract` ve `pbi_report_readiness` tablolarÄ± BigQuery tarafÄ±nda PASS kalmalÄ±.
   - Beklenen ve gerÃ§ekleÅŸen satÄ±r sayÄ±larÄ± final kontrollerinde izlenmeli.

3. dbt docs
   - `dbt docs generate` her final build sonrasÄ± Ã§alÄ±ÅŸtÄ±rÄ±lmalÄ±.
   - Exposure: `fraud_project_v2`.
   - Kritik modellerde aÃ§Ä±klamasÄ±z kolon kalmamalÄ±.

## P3 - Sunum Kalitesi

1. GÃ¶rsel tasarÄ±m
   - Kurumsal bankacÄ±lÄ±k paleti kullanÄ±lmalÄ±.
   - AÅŸÄ±rÄ± renkli veya amatÃ¶r hissi veren tasarÄ±mdan kaÃ§Ä±nÄ±lmalÄ±.
   - Risk renkleri tutarlÄ± olmalÄ±: Critical kÄ±rmÄ±zÄ±, High koyu turuncu, Elevated amber, Low yeÅŸil/gri.

2. Sayfa dÃ¼zeni
   - 1280x720 canvas standardÄ± korunmalÄ±.
   - Ãœst satÄ±r KPI, orta alan ana grafik, alt alan detay/aksiyon mesajÄ± olacak ÅŸekilde dÃ¼zenlenmeli.
   - BaÅŸlÄ±klar kÄ±sa, grafik etiketleri okunabilir olmalÄ±.

3. YÃ¶netici dil kontrolÃ¼
   - Teknik jargon minimumda tutulmalÄ±.
   - Her sayfada "ne oldu, neden Ã¶nemli, ne yapÄ±lmalÄ±" yapÄ±sÄ± kurulmalÄ±.
   - GÃ¶rÃ¼nÃ¼r hiÃ§bir yerde geliÅŸtirme aracÄ± izi, geÃ§ici sunum dili veya proje iÃ§i teknik not olmamalÄ±.

## P4 - Teslim ve PortfÃ¶y

1. GitHub temizlik
   - Ham CSV, DuckDB, credential ve geÃ§ici output dump commitlenmemeli.
   - README proje hikayesini net anlatmalÄ±.
   - `powerbi/fraud_project_v2.pbix` ana teslim olarak kalmalÄ±.

2. Sunum akÄ±ÅŸÄ±
   - 3 dakikalÄ±k kÄ±sa yÃ¶netici anlatÄ±mÄ± hazÄ±rlanmalÄ±.
   - 10 dakikalÄ±k teknik walkthrough hazÄ±rlanmalÄ±.
   - dbt lineage ve BigQuery dataset yapÄ±sÄ± gÃ¶sterilebilir olmalÄ±.

3. Final kabul
   - Power BI aÃ§Ä±lÄ±r.
   - BigQuery baÄŸlantÄ±sÄ± Ã§alÄ±ÅŸÄ±r.
   - dbt build geÃ§er.
   - Rapor 6 dolu sunum sayfasÄ±ndan oluÅŸur.
   - Analiz hikayesi savunulabilir ve profesyoneldir.
