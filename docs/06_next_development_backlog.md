# Next Development Backlog

Bu dokÃ¼man, son iterasyonda canlÄ± web dashboard ana raporlama katmanÄ± haline getirildikten sonra izlenecek teknik geliÅŸtirme sÄ±rasÄ±nÄ± tanÄ±mlar.

## Tamamlanan Son Ä°terasyon

1. Eski statik rapor baÄŸÄ±mlÄ±lÄ±ÄŸÄ± ana sunum katmanÄ±ndan Ã§Ä±karÄ±ldÄ±.
2. FastAPI dashboard API'si 18 BigQuery raporlama tablosunu kapsayacak ÅŸekilde geniÅŸletildi.
3. Web dashboard'a geliÅŸmiÅŸ analitik yetenekler eklendi:
   - global slicer
   - drill-through paneli
   - Ã¶zel tooltip
   - Pareto analizi
   - decomposition tree
   - identity/product coverage matrisi
   - relatif saat ve amount-decimal heatmap
   - threshold what-if simÃ¼lasyonu
   - feature treemap
   - veri kalite kontratÄ±
4. README ve QA dokÃ¼manlarÄ± web dashboard'u ana teslim olarak gÃ¶sterecek ÅŸekilde gÃ¼ncellendi.

## SÄ±radaki GeliÅŸtirmeler

1. Public deployment smoke test
   - Production URL Ã¼zerinden API kontratÄ± ve ana dashboard ekranÄ± kontrol edilmeli.

2. Segment drill-down derinleÅŸtirme
   - Drill paneline trend, hacim, fraud payÄ± ve Ã¶nerilen aksiyon aynÄ± anda eklenmeli.

3. YÃ¶netici sunumu export'u
   - Her sekme iÃ§in PNG export ve tek sayfalÄ±k executive brief Ã§Ä±ktÄ±sÄ± hazÄ±rlanmalÄ±.

4. Model explainability
   - Feature importance tablosu iÅŸ birimi diliyle yorumlanmalÄ±.
   - MaskelenmiÅŸ Vesta Ã¶zellikleri â€œobservational signalâ€ olarak etiketlenmeli.

5. Operasyonel eÅŸik simÃ¼lasyonu
   - False positive maliyeti, false negative maliyeti ve inceleme kapasitesi kullanÄ±cÄ± girdisi olarak simÃ¼le edilmeli.

## Kabul Kriterleri

- Dashboard production URL'i veri dÃ¶ndÃ¼rÃ¼r.
- GÃ¶rÃ¼nÃ¼r arayÃ¼zde boÅŸ chart yoktur.
- TÃ¼m interaktif kontroller veri durumunu deÄŸiÅŸtirir.
- README ekran gÃ¶rÃ¼ntÃ¼leri gÃ¼ncel web arayÃ¼zÃ¼nÃ¼ gÃ¶sterir.
- Web dashboard proje iÃ§indeki tek aktif sunum katmanÄ±dÄ±r.
