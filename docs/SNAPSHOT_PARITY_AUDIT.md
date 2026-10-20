# F02 — Deterministic reporting snapshot parity audit

> **20 October source update:** [Current read-only validation](research/BIGQUERY_READ_ONLY_VALIDATION_2026-10-20.md) verifies local access and explains the four direct-group text differences through the existing public-copy contract. Seven derived/filtered groups remain unverified; full parity is not certified.

## Scope and verified source-map finding (17 October 2026)

The historical web snapshot at \`webapp/snapshots/dashboard.json\` reports **27 dashboard data groups**. \`webapp/main.py::BIGQUERY_TABLES\` maps those groups to exactly **24 unique BigQuery source table names**. The reported 27-vs-24 count is not, by itself, a missing-table error: \`payment_email_matrix\`, \`proxy_product_matrix\`, \`proxy_cross_matrix\`, and \`niche_drilldown\` are derived from the **same** \`fact_train_transactions\` source. This accounts exactly for the three-count difference. It does **not** prove that all tables currently exist, have correct schemas or match the published snapshot.

The actual project and region were verified separately on 15 October 2026 as \`workintech-working\` / \`US\`; see \`docs/BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md\`. The snapshot remains dated **2026-09-10T19:41:45Z** and must not be relabeled as fresh.

## Optional authenticated inventory — BigQuery metadata APIs, no SQL

On an **authorized network-enabled machine**, run the standalone metadata inventory. It requires an existing read-only service-account credential and can run without gcloud login:

~~~bash
python -m scripts.inventory_reporting_bigquery \
  --credentials-file /private/workintech-service-account.json \
  --project workintech-working \
  --dataset fraud_project_reporting \
  --output outputs/fraud_bigquery_inventory.json
~~~

It calls **get_dataset, list_tables and get_table** only, using the BigQuery read-only OAuth scope. It does not use query jobs or download any table rows. It compares the 24 expected table names and their location to the historical snapshot's declared project/dataset, and reports table metadata, row counts, modification timestamps and field names. A green \`INVENTORY_MATCH\` verifies mapping and metadata presence **only**, never current data content or model validity. Access/egress policies still apply. A missing table or wrong project/region produces a nonzero exit; exceptions never print credentials or credential paths.

This command could not be run against the owner's Windows environment during the 17 October development session because remote desktop operations were blocked by the connector's monthly usage limit. No new BigQuery metadata from that session is claimed. A fresh report must be produced after authorized access is available.

## Run offline — no SQL jobs or credentials

Inventory the source mapping and all historical group row counts:

~~~bash
python scripts/audit_reporting_snapshot.py --output outputs/fraud_parity_inventory.json
~~~

This exits **1** with \`comparison_status=NOT_RUN\` because there is no independent current-source payload. A nonzero exit is intentional and must not be turned into a green parity gate.

Once an authorized maintainer has independently exported the *same 27 grouped reporting outputs* into a JSON object matching the \`/api/dashboard\` payload format, compare it:

~~~bash
python scripts/audit_reporting_snapshot.py \
  --current-json /private/current_reporting_payload.json \
  --output outputs/fraud_parity_comparison.json
~~~

The comparator uses **no Google Cloud API, no BigQuery query job, no data mutation, no dbt build, no credential handling and no outbound network**. It never changes the committed historical snapshot. Compare output in a private workspace; do not publish unreviewed data to a public issue or repo.

The **current JSON must come from an independently authorized source**. Copying or reformatting the historical snapshot, or replacing only its \`refreshed_at\` timestamp, is not source validation. The auditor reports \`same_published_payload\` and always marks \`provenance_verdict=UNVERIFIED_EXTERNAL_SOURCE\`, even when its structural diff is empty.

## Why table dumps alone cannot cover all 27 groups

\`webapp/main.py::TABLE_QUERIES\` applies the published SQL logic:

- Four \`fact_train_transactions\` groups are **derived SQL aggregates** and cannot be compared directly with raw \`list_rows\` output.
- \`data_quality\` groups and aggregates \`rpt_data_quality_scorecard\`.
- \`model_risk_bands\` filters to \`split='train'\`.
- \`feature_importance\` limits the report to its first 15 ranked features.
- The remaining groups read reporting tables using explicit ordering and public copy-normalization. Some risk/strategy/narrative/readiness **text fields are deliberately rewritten** by \`normalize_public_row\`; raw table strings cannot be naively compared to the published API strings.

For a **full release-ready** parity result, use the *exact source query-and-normalization contract* to produce a fresh, separately approved \`/api/dashboard?refresh=true\` payload. That runs BigQuery SQL; first obtain explicit cost/billing authorization and review a dry-run byte estimate. In the F01 branch, the live refresh route is protected by an internal header token. Do not bypass authorization or submit real secrets via browser JavaScript, GitHub issues or chat.

## Comparator behavior

- Considers **all 27 groups**, all rows and their union of field names; no first-row approximation.
- Full-row multiset comparison is **order independent** and detects duplicate row count differences.
- Normalizes numeric values to **6 decimal places**, preserving strings, booleans and null separately. This is a comparison tolerance, not a data rewrite.
- If each row has a unique natural reporting key, records differences by key and field. Missing or duplicate keys fall back to the complete multiset comparison.
- Records historical/current row counts, missing and new fields, changed-field counts, and at most five sample key/value **hashes**. Does not print raw row values.
- Compares source project, dataset, portfolio transaction count and labeled fraud count metadata.
- Hashes entire JSON inputs for traceability, never fabricates runtime freshness or source authentication.

\`comparison_status\` can be \`NOT_RUN\`, \`INCOMPLETE\`, \`DIFF\`, or \`STRUCTURAL_MATCH\`. \`STRUCTURAL_MATCH\` is **not** a proof of present-day BigQuery source provenance or approved model validation. Reports never claim to close issue #9 automatically.

## Release acceptance for issue #9

1. Record independently verified BigQuery project, US location, IAM scope, source SHA/lineage and actual reporting-table inventory (no secrets in artifacts).
2. Obtain appropriate cost approval and **BigQuery dry-run** evidence before any SQL jobs.
3. Export all 27 transformed groups from the real source under that approved plan. Preserve query versions, commit SHA, and actual source metadata.
4. Run this auditor. Resolve **every** \`DIFF\` and \`INCOMPLETE\` status, including \`segment_watchlist\`, \`review_strategy\`, \`report_narrative\` and \`report_readiness\`.
5. Run dbt and API tests under the same authorized source before deciding whether a new snapshot is needed. Preserve historical timestamps if no actual rebuild occurs.
6. Release only after provenance is reviewed and the deployed app's snapshot/version is verified. No green default CI job substitutes for these steps.

### Data-free CI verification

~~~bash
python -m pytest -q tests/python/test_snapshot_parity_audit.py tests/python/test_bigquery_reporting_inventory.py tests/python/test_snapshot_evidence_consistency.py
python -m ruff check scripts/audit_reporting_snapshot.py scripts/inventory_reporting_bigquery.py tests/python/test_snapshot_parity_audit.py tests/python/test_bigquery_reporting_inventory.py
~~~

All tests operate on the committed historical JSON and synthetic records only.
