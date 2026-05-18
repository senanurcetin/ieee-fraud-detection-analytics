select
    1 as page_order,
    'Yönetici Özeti' as page_name,
    'Fraud düşük frekanslı ancak belirli segmentlerde yüksek yoğunluklu bir risktir.' as executive_message,
    'Product C, identity kaydı ve kritik model bandı üst yönetim için ana risk göstergeleridir.' as analytical_focus,
    'Kritik ve yüksek risk bantları operasyonel inceleme kuyruğunda önceliklendirilmelidir.' as recommended_action
union all
select
    2,
    'Risk Konsantrasyonu',
    'Risk ürün, identity ve cihaz kırılımlarında homojen dağılmamaktadır.',
    'Product ve identity lift metrikleri risk konsantrasyonunu görünür kılar.',
    'Yüksek lift üreten segmentler için ayrı izleme ve kontrol kuralları tanımlanmalıdır.'
union all
select
    3,
    'Tutar ve Zaman Analizi',
    'Fraud davranışı tutar ve zaman ekseninde doğrusal değildir.',
    'Tutar bantları, günlük drift ve hareketli ortalama birlikte okunmalıdır.',
    'Drift bayrağı oluşan dönemlerde operasyon kapasitesi ve kural setleri gözden geçirilmelidir.'
union all
select
    4,
    'Ödeme ve Email Segmentleri',
    'Ödeme tipi ve email domain grupları operasyonel segment üretir.',
    'Kart ağı, kart tipi ve purchaser email grupları hacim ve fraud payıyla birlikte değerlendirilmelidir.',
    'Yüksek hacimli ve yüksek lift üreten email/payment segmentleri takip listesine alınmalıdır.'
union all
select
    5,
    'Model Skorlama ve Risk Bantları',
    'Model skorları kararın kendisi değil, inceleme önceliği katmanıdır.',
    'Risk bandı lift, fraud capture ve feature importance metrikleri modelin iş değerini açıklar.',
    'Critical ve High bantları manuel inceleme, ek doğrulama veya işlem sonrası takip akışına bağlanmalıdır.'
union all
select
    6,
    'Veri Kalitesi ve Mimari',
    'Veri kalitesi ve lineage, fraud raporunun güvenilirlik temelidir.',
    'Eksiklik oranları, dbt testleri ve katmanlı BigQuery mimarisi birlikte sunulmalıdır.',
    'Her rapor yenilemesinde dbt build, row-count ve reconciliation testleri kalite kapısı olmalıdır.'
