# Fraud Analytics — BigQuery source revalidation (14 October 2026)

## Source identity and access

- **Authenticated project:** `workintech-working`; the unrelated active default GCP project `data-analiz-490513` does **not** hold the fraud reporting dataset. Never run fraud build scripts against the latter by accident.
- **BigQuery reporting dataset:** `workintech-working:fraud_project_reporting` (US region).
- **Source table checked:** `rpt_executive_kpis`, one row, 168 logical bytes.
- **Table last modified (UTC):** 2026-09-11 02:02:11.021 (BigQuery table metadata, not a claim of a transaction timestamp).
- **Committed offline dashboard snapshot:** `webapp/snapshots/dashboard.json`, with `meta.refreshed_at=2026-09-10T19:41:45Z`, `meta.project_id=workintech-working`, `meta.dataset=fraud_project_reporting`, and `meta.table_count=27`.

## Independent read-only reconciliation

Executed **table metadata and tabledata preview**, not a paid BigQuery analytical query:

```bash
bq show --format=prettyjson workintech-working:fraud_project_reporting.rpt_executive_kpis
bq head --format=prettyjson -n 1 workintech-working:fraud_project_reporting.rpt_executive_kpis
```

| Measure | Live BigQuery table preview | Committed snapshot | Check |
| --- | ---: | ---: | --- |
| Total transactions | 590,540 | 590,540 | Match |
| Fraud transactions | 20,663 | 20,663 | Match |
| Legitimate transactions | 569,877 | 569,877 | Match |
| Total transaction amount | 79,738,948.734985739 | 79,738,948.73498574 | Match (floating-point precision) |
| Fraud transaction amount | 3,083,844.8599999514 | 3,083,844.8599999514 | Match |
| Critical-risk transactions | 5,906 | 5,906 | Match |
| Critical-risk fraud count | 5,710 | 5,710 | Match |

Other scalar KPIs, including baseline fraud rate and product C lift, were also present in both payloads and differ only at floating-point rounding precision.

## What this audit does NOT prove

- The **underlying IEEE-CIS dataset is historic and static**. This is not a live bank event stream or a new season of transactions. The 10 September snapshot generation timestamp remains deliberately unchanged; editing it without regenerating evidence would be misleading.
- Only the executive KPI aggregate row was independently checked against BigQuery in this run. No claim that **all 27** reporting sources were revalidated, rebuilt or freshly ingested.
- No dbt build, BigQuery write, chargeable query, production deployment, new model training or automatic refresh was performed.
- The BigQuery access is based on the user's active gcloud session, whereas `scripts/build_web_snapshot.py` currently requires a service-account credential file; do not place credentials in Git.

## Future refresh acceptance gate

Rebuild only when relevant governed source data or marts genuinely change. Confirm the intended `workintech-working` project and US location, check the dry-run billing estimate and quota, run dbt tests and compare all reporting aggregates, then generate snapshots with valid read-only service-account credentials, review diffs and deploy deliberately. Keep offline-data limitations visible.
