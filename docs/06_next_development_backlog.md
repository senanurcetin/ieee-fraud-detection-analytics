# Next Development Backlog

Bu doküman, son iterasyonda canlı web dashboard ana raporlama katmanı haline getirildikten sonra izlenecek teknik geliştirme sırasını tanımlar.

## Tamamlanan Son İterasyon

1. Power BI bağımlılığı ana sunum katmanından çıkarıldı.
2. FastAPI dashboard API'si 18 BigQuery raporlama tablosunu kapsayacak şekilde genişletildi.
3. Web dashboard'a Power BI benzeri analitik yetenekler eklendi:
   - global slicer
   - drill-through paneli
   - özel tooltip
   - Pareto analizi
   - decomposition tree
   - identity/product coverage matrisi
   - relatif saat ve amount-decimal heatmap
   - threshold what-if simülasyonu
   - feature treemap
   - veri kalite kontratı
4. README ve QA dokümanları web dashboard'u ana teslim olarak gösterecek şekilde güncellendi.

## Sıradaki Geliştirmeler

1. Public deployment smoke test
   - Production URL üzerinden API kontratı ve ana dashboard ekranı kontrol edilmeli.

2. Segment drill-down derinleştirme
   - Drill paneline trend, hacim, fraud payı ve önerilen aksiyon aynı anda eklenmeli.

3. Yönetici sunumu export'u
   - Her sekme için PNG export ve tek sayfalık executive brief çıktısı hazırlanmalı.

4. Model explainability
   - Feature importance tablosu iş birimi diliyle yorumlanmalı.
   - Maskelenmiş Vesta özellikleri “observational signal” olarak etiketlenmeli.

5. Operasyonel eşik simülasyonu
   - False positive maliyeti, false negative maliyeti ve inceleme kapasitesi kullanıcı girdisi olarak simüle edilmeli.

## Kabul Kriterleri

- Dashboard production URL'i veri döndürür.
- Görünür arayüzde boş chart yoktur.
- Tüm interaktif kontroller veri durumunu değiştirir.
- README ekran görüntüleri güncel web arayüzünü gösterir.
- Power BI yalnızca arşivlenmiş prototip olarak anılır.
