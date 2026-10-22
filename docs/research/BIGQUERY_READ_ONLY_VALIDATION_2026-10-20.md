# BigQuery read-only validation — 20 October 2026

> **Current evidence:** [21 October completed validation](COMPLETED_VALIDATION_2026-10-21.md) supersedes earlier open source/calibration gates for the bounded historical release. Earlier measurements and limitations below retain their original dates.

## Source and method

Authorized access to `workintech-working.fraud_project_reporting` in `US` succeeded using the owner's local service-account file. The key remains outside Git; no credential content or credential path is included in the evidence. OAuth refresh and dataset metadata returned successfully.

The bounded verifier used dataset/table metadata and `tabledata.list` only. It submitted **zero SQL jobs**, performed no writes, and downloaded no raw fraud transactions. Each reporting source was bounded to 10,000 rows; 890 aggregate reporting rows were read during the strict comparison. Published snapshot metadata remains `2026-09-10T19:41:45Z`.

## Results

[Strict comparison evidence](evidence/bigquery_direct_parity_2026-10-20.json) records:

| Scope | Result |
|---|---|
| Direct report groups with matching fields/schema | 16 |
| Direct groups with textual differences | 4 |
| Derived/filtered groups skipped | 7 |
| Full 27-group parity | **Not certified** |

The four strict differences were investigated separately through the existing `webapp.main.normalize_public_row` presentation contract. [Diagnostic evidence](evidence/bigquery_public_copy_2026-10-20.json) shows all four match the committed public report after normalization:

| Group | Strict differing fields | Rows |
|---|---|---:|
| `segment_watchlist` | `recommended_action` | 20 |
| `review_strategy` | `review_priority` | 3 of 4 |
| `report_narrative` | `analytical_focus`, `executive_message`, `recommended_action` | 9 |
| `report_readiness` | `check_name`, `readiness_area` | 7 of 8 |

No numeric-field differences were detected in these direct comparisons. This is evidence of a presentation transformation, not raw-table equality. The strict verifier deliberately retains `DIFF_DIRECT` and exit code 1 even when the separate presentation comparison matches. Source modification dates for the four inspected tables are 11 September, later than the historical snapshot timestamp; no freshness inference or retroactive timestamp change is made.

## Reproduce without SQL

```bash
python -m scripts.verify_reporting_tables_bigquery_readonly   --credentials-file /private/credentials/workintech.json   --project workintech-working --dataset fraud_project_reporting   --explain-public-copy --output outputs/qa/bigquery_parity.json
```

`--use-adc` is an alternative to the private local credential file. The optional diagnostic calls the same application copy normalization, retains the strict result, and reports hashes/field counts instead of source row values. Synthetic tests verify numeric changes remain differences and diagnostic normalization cannot turn strict source failure into certification.

## Remaining boundary

Issue #9 remains open for five derived and two filtered groups. Four derived groups require fact-level aggregation; this bounded read does not inspect that raw fact table. This execution does not establish dbt lineage, current model calibration, or a live feed. Repository-scoped keyless WIF/ADC automation remains separate from successful local authorization. See [read-only runbook](../BIGQUERY_BOUNDED_SOURCE_PARITY.md) and [release status](../RELEASE_STATUS.md).
