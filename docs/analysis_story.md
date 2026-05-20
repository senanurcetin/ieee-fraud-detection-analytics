# Analiz Hikayesi

## Ana Soru

Sahtecilik hangi segmentlerde yoğunlaşıyor ve BI ekibi bunu nasıl izlemeli?

## Temel Bulgular

1. Sahtecilik nadir ancak yoğunlaşmış durumda: baz oran 3.50%.
2. Ürün riski eşit dağılmıyor: Product C sahtecilik oranı 11.69%, Product W ise 2.04%.
3. Identity kaydı risk sinyalidir: identity kaydı olan işlemlerde oran 7.85%, olmayan işlemlerde 2.09%.
4. Tutar riski doğrusal değildir: <$25 ve $250+ bantları orta tutarlı işlemlere göre daha yüksek risk taşır.
5. Ödeme özellikleri ayrıştırıcıdır: kredi kartı kombinasyonları debit kart kombinasyonlarına göre daha yüksek risk gösterir.
6. Model, izleme ve önceliklendirme katmanı olarak kullanılmalıdır: Kritik risk bandı baz orana göre çok yüksek lift üretir.

## Önerilen Sunum Akışı

Önce sınıf dengesizliğini gösterin, ardından sahteciliğin rastgele dağılmadığını kanıtlayın. Ürün, identity, tutar, ödeme, email ve zaman kırılımlarıyla ilerleyin. Son bölümde model risk bantlarını nihai karar mekanizması olarak değil, operasyonel önceliklendirme katmanı olarak konumlandırın.
