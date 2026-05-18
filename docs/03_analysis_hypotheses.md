# 03 - Analiz İçin Hipotezler

## H1 - Ürün Ailesi Riski Ayrıştırır

Product C işlemlerinin fraud oranının portföy ortalamasının üzerinde olması beklenir.

Sonuç: Product C fraud oranı %11,69 ile baz oranın yaklaşık 3,3 katıdır. Ürün ailesi risk izleme için birincil kırılımdır.

## H2 - Identity Kaydı Sadece Veri Tamlığı Değil, Risk Sinyalidir

Identity tablosunda kaydı olan işlemlerin risk profilinin farklılaşması beklenir.

Sonuç: Identity kaydı olan işlemlerde fraud oranı %7,85; olmayan işlemlerde %2,09 seviyesindedir. Identity varlığı fraud skorlama modelinde izlenmesi gereken davranışsal bir sinyaldir.

## H3 - Tutar Riski Doğrusal Değildir

Fraud oranının işlem tutarı arttıkça monoton artması beklenmez; uç tutar bantlarında yoğunlaşma oluşabilir.

Sonuç: `<$25` bandı %6,97, `$250-499` bandı %5,28 ve `$500+` bandı %4,72 fraud oranına sahiptir. Orta tutar bantları daha düşük risk göstermektedir.

## H4 - Email Domain Grupları Operasyonel Segment Üretir

P_emaildomain gruplarının fraud oranı ve hacim açısından ayrışması beklenir.

Sonuç: Hotmail %5,30, Gmail %4,35 fraud oranıyla öne çıkar. Gmail yüksek hacmi nedeniyle toplam risk katkısı bakımından kritik izleme segmentidir.

## H5 - Zaman Penceresi ve Gün İçi Örüntüler Drift Gösterebilir

Fraud oranının gözlem süresi boyunca sabit kalmaması beklenir.

Sonuç: Günlük fraud oranı hareketli ortalamada belirgin dalgalanma üretir. Bu durum fraud izleme panosunda zaman bazlı drift kontrolünü gerekli kılar.

## H6 - Model Risk Bantları Operasyonel Önceliklendirme Sağlar

Model skorları doğrudan karar mekanizması olarak değil, inceleme kuyruğu önceliklendirmesi için kullanılmalıdır.

Sonuç: Kritik risk bandında gözlenen fraud oranı %96,31; yüksek risk bandında %44,39 seviyesindedir. Bu bantlar operasyon ekibi için net önceliklendirme sağlar.

## Sunum İçin Ana Çerçeve

Analiz, "sahtecilik hangi segmentlerde yoğunlaşıyor?" sorusuyla açılmalıdır. Ardından ürün, identity, tutar, ödeme tipi, email ve zaman kırılımlarıyla riskin rastgele dağılmadığı kanıtlanmalı; son bölümde model skorları operasyonel aksiyon katmanı olarak konumlandırılmalıdır.
