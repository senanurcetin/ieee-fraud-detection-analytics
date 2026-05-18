# 06 - Sonraki Geliştirme Backlog'u

Bu liste, son geliştirme iterasyonundan sonra kalan işleri ve öncelikleri gösterir. Mevcut durum artık boş rapor değildir; `fraud_project_v2.pbix` içinde 6 sayfa, 35 visual container ve yeni yönetici analiz görselleri vardır.

## Bu Iterasyonda Tamamlananlar

1. Power BI karar destek veri katmanı güçlendirildi
   - `pbi_segment_watchlist`: ürün, identity, tutar, ödeme ve email segmentlerini tek risk öncelik listesinde birleştirir.
   - `pbi_review_strategy`: risk bantlarını operasyon kuyruğu, günlük inceleme hacmi ve yönetim notu ile eşler.
   - `pbi_threshold_simulation`: model skor eşiğine göre inceleme yükü, fraud yakalama oranı ve kesinlik/geri çağırma dengesini gösterir.
   - `pbi_report_readiness`: veri, anlatı, risk ve model operasyon hazırlığını PASS/FAIL formatında özetler.

2. dbt kalite kapsamı genişletildi
   - Model sayısı 29'a çıktı.
   - Data test sayısı 67'ye çıktı.
   - Yeni Power BI modelleri için row-count, accepted values, unique, not null ve range testleri eklendi.
   - Prod hedefte yeni modeller ve testler başarıyla çalıştı.

3. Power BI rapor içeriği güçlendirildi
   - `17_executive_control_panel.png`: yönetici KPI kontrol paneli.
   - `18_segment_watchlist.png`: operasyonel segment izleme listesi.
   - `19_model_threshold_simulation.png`: model eşik simülasyonu.
   - `20_qa_readiness_scorecard.png`: sunum öncesi kalite ve hazırlık skor kartı.
   - `21_executive_decision_matrix.png`: üst yönetim aksiyon matrisi.
   - `22_review_strategy_matrix.png`: model skorundan operasyon kuyruğuna geçiş stratejisi.
   - `24_risk_funnel.png`: inceleme hacmi ve fraud yakalama hunisi.
   - `25_dbt_quality_gate.png`: dbt ve BigQuery kalite kapısı.
   - `fraud_project_v2.pbix` bu görsellerle yeniden üretildi.

4. Rapor sayfa yapısı güncellendi
   - Yönetici Özeti: KPI kontrol paneli, Product C lift, identity lift, risk bandı lift ve segment izleme listesi.
   - Risk Konsantrasyonu: segment izleme listesi ve ana risk kırılımları.
   - Model Skorlama: eşik simülasyonu, feature importance ve risk bantları.
   - Veri Kalitesi: hazırlık skor kartı, missingness ve mimari görseli.

## P0 - Kalan Kritik İşler

1. Power BI Desktop açılış kontrolü
   - `powerbi/fraud_project_v2.pbix` Power BI Desktop'ta açılmalı.
   - 6 sayfanın tamamı kontrol edilmeli.
   - Yeni görsellerin kırpılmadığı, üst üste binmediği ve okunabilir olduğu doğrulanmalı.

2. Native visual dönüşümü
   - Mevcut rapor açılabilir ve sunuma hazır statik analiz görselleri içerir.
   - Final profesyonel eşik için ana grafikler Power BI native visual'a çevrilmelidir.
   - Öncelik sırası:
     - Yönetici KPI kartları.
     - Segment izleme tablosu.
     - Product/identity lift bar chart.
     - Threshold simulation line chart.
     - QA readiness table.

3. DirectQuery model kontrolü
   - Power BI modelinde `fraud_project_powerbi` datasetindeki yeni tablolar görünmeli:
     - `pbi_segment_watchlist`
     - `pbi_review_strategy`
     - `pbi_threshold_simulation`
     - `pbi_report_readiness`
   - Görünmüyorsa Power BI Desktop içinden BigQuery navigator ile bu tablolar eklenmelidir.

4. Tam dbt kalite kapısı
   - Finalden önce yalnız seçili modeller değil, tam build çalıştırılmalıdır:

```powershell
dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod
dbt docs generate --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod
```

## P1 - Analitik Derinlik

1. Yönetici aksiyon katmanı
   - Segment izleme listesi her satır için önerilen operasyon aksiyonu içeriyor.
   - Power BI'da bu alan tablo tooltip'i veya detay tablosu olarak gösterilmeli.

2. Model kapasite senaryosu
   - Threshold simülasyonu üzerinden üç karar senaryosu hazırlanmalı:
     - Geniş izleme
     - Dengeli operasyon
     - Dar kritik kuyruk
   - Her senaryoda beklenen fraud capture ve operasyon yükü açıklanmalı.

3. Segment risk kontrolü
   - Küçük hacimli segmentlerin yanıltıcı etkisini azaltmak için `transaction_count >= 1000` filtresi korunmalı.
   - Sunumda fraud rate tek başına değil, fraud share ve transaction share ile birlikte anlatılmalı.

## P2 - Power BI Format Kalitesi

1. Sayfa hizalama
   - Tüm sayfalarda 1280x720 canvas korunmalı.
   - Üst başlık, orta analiz alanı ve alt aksiyon alanı aynı grid mantığıyla hizalanmalı.

2. Sayı formatları
   - Fraud rate, fraud share, workload share ve capture rate yüzde formatında olmalı.
   - İşlem sayıları binlik ayraçla gösterilmeli.
   - Lift değerleri `x` formatında gösterilmeli.

3. Kurumsal tema
   - Lacivert ana renk, kırmızı risk, petrol yeşili kalite/başarı ve nötr gri destek rengi korunmalı.
   - Aşırı dekoratif veya demo hissi veren görsel kullanılmamalı.

## P3 - Sunum ve Portföy

1. 3 dakikalık yönetici anlatımı
   - Problem büyüklüğü.
   - Riskin nerede yoğunlaştığı.
   - Modelin operasyon kuyruğuna nasıl çevrildiği.
   - Veri kalitesi ve güvenilirlik kanıtı.

2. 10 dakikalık teknik walkthrough
   - Kaggle raw data.
   - BigQuery dataset katmanları.
   - dbt lineage ve testler.
   - Power BI DirectQuery raporlama katmanı.
   - Model skorlaması ve eşik dengesi.

3. GitHub sunum kanıtları
   - README içine mimari özet ve rapor sayfa listesi korunmalı.
   - Büyük ham veri ve credential dosyaları repo dışında kalmalı.
   - Power BI raporu ana teslim dosyası olarak `powerbi/fraud_project_v2.pbix` kalmalı.

## Kabul Eşiği

Final kabul için aşağıdaki maddeler aynı anda sağlanmalıdır:

- BigQuery `fraud_project_powerbi` datasetinde tüm `pbi_*` tabloları dolu.
- dbt full build ve docs generate başarılı.
- Power BI dosyası açılıyor.
- 6 sayfa boş değil.
- Yönetici Özeti ilk 30 saniyede ana mesajı veriyor.
- Model sayfası operasyonel karar desteğini açık anlatıyor.
- Veri Kalitesi sayfası veri güvenilirliğini kanıtlıyor.
