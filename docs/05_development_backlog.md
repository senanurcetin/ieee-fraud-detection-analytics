# Development Backlog

Bu backlog, canlÄ± web analitik katmanÄ±nÄ±n kalan geliÅŸtirme alanlarÄ±nÄ± gÃ¶sterir. Ana hedef, dashboard'u Ã¼st yÃ¶netim sunumu ve portfÃ¶y gÃ¶sterimi iÃ§in daha etkileÅŸimli, aÃ§Ä±klanabilir ve gÃ¼venilir tutmaktÄ±r.

## P0 - Sunum ve Veri GÃ¼veni

1. Vercel production doÄŸrulamasÄ±
   - `/api/dashboard?refresh=true` endpoint'i 18 tabloyu dÃ¶ndÃ¼rmeli.
   - Toplam iÅŸlem sayÄ±sÄ± 590.540 olarak gÃ¶rÃ¼nmeli.
   - `rpt_report_readiness` 6/6 PASS olmalÄ±.

2. Dashboard gÃ¶rsel kontrolÃ¼
   - MasaÃ¼stÃ¼ 1440px ve mobil 390px gÃ¶rÃ¼nÃ¼mleri kontrol edilmeli.
   - BaÅŸlÄ±k kÄ±rpÄ±lmasÄ±, taÅŸan metin ve boÅŸ chart olmamalÄ±.
   - Slicer, tooltip, drill-through ve threshold slider akÄ±ÅŸÄ± Ã§alÄ±ÅŸmalÄ±.

3. README ekran gÃ¶rÃ¼ntÃ¼leri
   - YÃ¶netici Ã¶zeti, segment analizi, model simÃ¼lasyonu ve kalite sayfasÄ± gÃ¼ncel web arayÃ¼zÃ¼nden alÄ±nmÄ±ÅŸ olmalÄ±.

## P1 - Analitik Derinlik

1. Segment karÅŸÄ±laÅŸtÄ±rma modu
   - Ä°ki segmentin fraud oranÄ±, lift, fraud payÄ± ve iÅŸlem payÄ± yan yana karÅŸÄ±laÅŸtÄ±rÄ±lmalÄ±.

2. Dynamic threshold policy
   - Threshold slider yalnÄ±zca model eÄŸrisini deÄŸil, Ã¶nerilen operasyon politikasÄ±nÄ± da gÃ¼ncellemeli.

3. Explainability sayfasÄ±
   - Feature importance yanÄ±nda SHAP benzeri iÅŸ yorumlarÄ± ve feature family katkÄ±sÄ± sunulmalÄ±.

4. Fraud contribution waterfall
   - Product, identity, payment, email ve amount eksenlerinin fraud hacmine katkÄ±sÄ± kademeli gÃ¶sterilmeli.

## P2 - Operasyonel Olgunluk

1. Alert simulation
   - Fraud rate drift, kritik bant hacmi ve veri kalite dÃ¼ÅŸÃ¼ÅŸÃ¼ iÃ§in uyarÄ± senaryolarÄ± gÃ¶rselleÅŸtirilmeli.

2. Export story
   - Dashboard JSON export yanÄ±nda executive summary PDF/PNG export akÄ±ÅŸÄ± eklenmeli.

3. Monitoring runbook
   - Vercel, BigQuery ve dbt hata durumlarÄ±nda kontrol edilecek adÄ±mlar dokÃ¼mante edilmeli.

## P3 - ÃœrÃ¼nleÅŸme

1. Multi-dataset template
   - AynÄ± dashboard iskeleti farklÄ± fraud veri setlerine uygulanabilir hale getirilmeli.

2. Tenant-ready architecture note
   - Ãœcretsiz katman sÄ±nÄ±rlarÄ± korunarak Ã§oklu mÃ¼ÅŸteri mimarisi iÃ§in dataset izolasyonu planlanmalÄ±.

3. Payment-independent validation
   - Stripe varsayÄ±mÄ± olmadan, waitlist ve Merchant of Record uyumlu Ã¼rÃ¼n doÄŸrulama akÄ±ÅŸÄ± tasarlanmalÄ±.
