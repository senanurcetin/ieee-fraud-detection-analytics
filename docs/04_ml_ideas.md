# 04 - ML Fikirleri

## Mevcut Model Yaklaşımı

Projede LightGBMClassifier kullanılmıştır. Model, TransactionDT alanına göre zaman sıralı validasyonla değerlendirilir. Bu yaklaşım, rastgele train-test ayrımına göre gerçek hayattaki fraud izleme senaryosuna daha yakındır.

Mevcut metrikler:

- Validasyon AUC: 0,917
- Average precision: 0,531
- Kullanılan feature sayısı: 206
- Kategorik feature sayısı: 26

## Risk Bantları

Model olasılıkları operasyonel kullanıma uygun risk bantlarına çevrilmiştir:

- Low
- Elevated
- High
- Critical

Bu bantlar, tekil skorların okunmasını kolaylaştırır ve canlı web dashboard üzerinde yönetilebilir bir inceleme kuyruğu yapısı sağlar.

## Geliştirme Fikirleri

1. Threshold optimizasyonu: Fraud operasyon kapasitesine göre precision-recall dengesi optimize edilebilir.
2. Maliyet duyarlı modelleme: False negative ve false positive maliyetleri ayrı tanımlanarak karar eşiği iş hedeflerine bağlanabilir.
3. Feature drift izleme: ProductCD, email domain, tutar bandı ve risk bandı dağılımları periyodik olarak takip edilebilir.
4. Segment bazlı model performansı: Product C, identity bulunan işlemler ve yüksek tutar bantları için ayrı performans kırılımları hesaplanabilir.
5. Açıklanabilirlik: Feature importance raporu genişletilerek SHAP tabanlı model açıklama katmanı eklenebilir.
6. Operasyon geri bildirimi: İnceleme sonucu onaylanan fraud/normal etiketleri model güncelleme sürecine dahil edilebilir.

## Üretim Perspektifi

Model tek başına karar verici olarak konumlandırılmamalıdır. En uygun kullanım, iş kuralları ve segment analizleriyle birlikte çalışan bir risk önceliklendirme katmanıdır. Kritik ve yüksek risk bantları manuel inceleme, ek doğrulama veya işlem sonrası takip süreçlerine yönlendirilmelidir.

## İzleme Metrikleri

- Günlük fraud oranı
- Risk bandı dağılımı
- Model skor ortalaması
- Kritik bant hacmi
- ProductCD bazlı fraud lift
- Email domain fraud oranı
- Veri eksiklik oranı
- Validasyon AUC ve average precision trendi
