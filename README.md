# fraud_project

IEEE-CIS Fraud Detection veri seti üzerinde hazırlanmış uçtan uca fraud analitiği projesidir. Çalışma; Kaggle CSV dosyalarının veri ambarına alınması, dbt ile katmanlı veri modelleme, makine öğrenmesi skorlaması ve Power BI yönetici raporuna kadar tekrarlanabilir bir analitik teslim paketi sunar.

## Proje Hikayesi

Analizin ana sorusu şudur: Sahtecilik hangi işlem segmentlerinde yoğunlaşıyor ve operasyon ekipleri bu riski nasıl önceliklendirmeli?

Veri setinde sahtecilik oranı düşük görünse de risk rastgele dağılmaz. Product C, identity kaydı bulunan işlemler, bazı ödeme tipi kombinasyonları, email domain grupları, tutar bantları ve zaman pencereleri belirgin risk ayrışması üretir. Power BI raporu bu ayrışmayı üst yönetim sunumuna uygun şekilde özetler; model skorları ise operasyonel inceleme kuyrukları için risk bandı katmanı sağlar.

## Repo Yapısı

```text
fraud_project/
├── analyses/
├── bigquery/
├── docs/
├── macros/
├── models/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── powerbi/
│   ├── assets/
│   ├── fraud_project.pbix
│   └── README.md
├── profiles/
├── scripts/
├── seeds/
├── snapshots/
├── src/
├── tests/
├── dbt_project.yml
├── packages.yml
└── README.md
```

## Veri Katmanları

- `fraud_project_raw`: Kaggle ham transaction ve identity tabloları, model destek tabloları.
- `fraud_project_staging`: Tip dönüşümü ve standartlaştırılmış alan adları.
- `fraud_project_intermediate`: Transaction ve identity join katmanı, analitik feature üretimi.
- `fraud_project_mart`: Fraud summary, günlük istatistikler, segment ve risk bandı martları.
- `fraud_project_powerbi`: Power BI için final raporlama tabloları.

## Çalıştırma

Local analitik depo ve model skorlarını üretmek:

```powershell
python src\prepare_raw_and_ml.py
dbt run --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target dev
dbt test --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target dev
python src\export_powerbi_and_charts.py
python src\build_fraud_project_pbix.py
```

BigQuery deployment:

```powershell
.\scripts\deploy_bigquery.ps1 `
  -Credentials "C:\Users\MONSTER\Downloads\workintech-working-2378ce4f85e2.json" `
  -ProjectId "workintech-working" `
  -Location "US" `
  -ReportingDataset "fraud_project_powerbi"
```

## Ana Teslimler

- Power BI raporu: `powerbi/fraud_project.pbix`
- Power BI görsel varlıkları: `powerbi/assets/`
- dbt modelleri: `models/`
- BigQuery rehberi: `bigquery/README.md`
- Sunum ve analiz dokümanları: `docs/`

Ham Kaggle dosyaları, servis hesabı JSON dosyası, DuckDB dosyaları ve geçici output klasörleri repoya eklenmez.
