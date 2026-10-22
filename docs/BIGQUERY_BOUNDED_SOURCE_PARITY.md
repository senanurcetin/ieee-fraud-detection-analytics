# F02-R / Issue #9 — bounded BigQuery source parity without SQL

> **Current evidence:** [21 October completed validation](research/COMPLETED_VALIDATION_2026-10-21.md) supersedes earlier open source/calibration gates for the bounded historical release. Earlier measurements and limitations below retain their original dates.

The authorized fraud reporting dataset is
`workintech-working.fraud_project_reporting` in the `US` region.
Previously verified project metadata (15 Oct 2026) found 24 physical
reporting tables mapped to 27 dashboard groups.

**This script does not use a ChatGPT BigQuery connector.** It runs in an
independently authorized network-connected Python environment.

## Safety contract

`scripts/verify_reporting_tables_bigquery_readonly.py`:

- Uses BigQuery `get_dataset`, `list_tables`, `get_table` and bounded
  `list_rows` only; **no SQL QueryJobs**, dbt jobs, writes, dataset mutation,
  raw training transactions or source data export.
- Refuses a different project/dataset/region from the committed fraud snapshot.
- Never retrieves `fact_train_transactions` or derived aggregations.
- Compares the up-to-10,000-row direct reporting tables with the committed
  snapshot using the existing deterministic auditor. Reports only field
  names, group status, row counts, and hashed differences.
- Explicitly **skips five derived and two filtered groups**. A positive
  result is `DIRECT_TABLES_MATCH_PARTIAL_ONLY`, **not** full 27-group
  parity, refreshed data, source lineage, model calibration or live feeds.
- On missing datasets, unreadable metadata, absent source columns, row caps,
  incomplete pagination, or per-table read errors, fails closed.
- Does not print credential JSON, raw rows, HTTP error messages or
  absolute credential paths. It never changes snapshot timestamps.

## Run from authorized Python / Colab / Cloud Shell

Run only from an account authorized to read these tables. Install the pinned
`google-cloud-bigquery` package from `webapp/requirements.txt` or your
approved environment.

If using a **locally stored**, private JSON credential file (never upload or
commit it as a GitHub file), for example:

```bash
python -m scripts.verify_reporting_tables_bigquery_readonly \
  --credentials-file /private/credentials/workintech.json \
  --project workintech-working \
  --dataset fraud_project_reporting \
  --output outputs/research/bigquery_direct_parity.json
```

The verifier now also accepts keyless Application Default Credentials with
`--use-adc`; the older `--credentials-file` option remains available.
Both paths request the `bigquery.readonly` OAuth scope. For GitHub runners,
use [manual keyless BigQuery workflow and WIF setup](archive/BIGQUERY_KAGGLE_WORKPLAN_2026-10-17.md)
rather than uploading a long-lived service-account JSON key.

For example, from a **separately authenticated** environment with ADC:

```bash
python -m scripts.verify_reporting_tables_bigquery_readonly \\
  --use-adc --project workintech-working --dataset fraud_project_reporting \\
  --output outputs/research/bigquery_direct_parity.json
```

The `outputs/` directory is gitignored; inspect the generated JSON locally
before sharing. The report should not contain any private row values.

A `DIRECT_TABLES_MATCH_PARTIAL_ONLY` exit code of zero means only that the
direct table projections matched. A nonzero exit means some direct group was
incomplete, unavailable, too large or different; stop before refreshing a
public snapshot. Read the per-group status and compare source schema.

## Still required to close Issue #9

1. Reconstruct the five derived/aggregated dashboard groups and the two
   filtered groups under the exact `webapp/main.py TABLE_QUERIES` contract.
   This may require cost-aware authorized SQL; obtain explicit cost approval
   and check dry-run bytes first. No such jobs are started here.
2. Explain any differences in `segment_watchlist`, `review_strategy`,
   `report_narrative` and `report_readiness`; the 15 Oct verification
   found differences in those historically published groups.
3. Establish source lineage and table modification evidence; re-run dbt
   builds/tests only when appropriate and authorized.
4. Preserve `2026-09-10` snapshot timestamps unless a genuinely new
   report artifact was generated, quality-assured and published.
5. Keep real IEEE-CIS ML/calibration acceptance Issues #8/#20 separate.

## Historical execution limitation — 17 October 2026

As of 17 Oct 2026 the account's BigQuery plugin is disabled by admin,
the authorized remote Windows device has exhausted Desktop Commander
monthly calls, and this assistant's local container cannot resolve
`oauth2.googleapis.com` or `bigquery.googleapis.com` DNS. A prior private
service-account file exists in the user's Library, but this chat has not
used, published or copied its key. **No BigQuery source read had been performed in that earlier environment.**


## Current verified execution — 20 October 2026

Local authorization now succeeds. [Current evidence](research/BIGQUERY_READ_ONLY_VALIDATION_2026-10-20.md) records 16 direct matches, four strict text differences explained by the existing public copy transformation, and seven skipped groups. Full 27-group parity remains unverified. The `--explain-public-copy` option adds an independent presentation diagnostic without changing strict verdicts or exit codes. No SQL jobs or source writes were used.
