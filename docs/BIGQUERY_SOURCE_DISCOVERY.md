# Fraud reporting: read-only BigQuery source discovery

> **Status update, 22 October 2026:** the authorized source is `workintech-working.fraud_project_reporting` in US. Issue #9 is closed for the [completed dated 27-group reconciliation](research/COMPLETED_VALIDATION_2026-10-21.md). Earlier discovery findings and blockers below describe their original investigation, not current release status.

## Current evidence and scope

The published dashboard JSON snapshot is historical, with a recorded refresh timestamp of **2026-09-10T19:41:45Z** (see issue #9). The expected fraud_project_reporting dataset was not found in the previously checked default project data-analiz-490513. This absence does not establish that the dataset has been deleted or that the snapshot is inaccurate. Establish the source GCP project and dataset location before changing reporting figures or refresh timestamps.

The dbt production profile in config/dbt/profiles.yml obtains its project from GCP_PROJECT_ID, its dataset from DBT_DATASET (default fraud_project_staging), and its BigQuery location from BIGQUERY_LOCATION (default US). Its default maximum_bytes_billed setting is not a substitute for checking costs and authorization before production execution.

## Safe discovery

With authenticated local Google Cloud CLI and BigQuery CLI, run:

~~~bash
python scripts/discover_reporting_source.py
~~~

Or limit inspection to a named project:

~~~bash
python scripts/discover_reporting_source.py --project data-analiz-490513
~~~

The command invokes only gcloud projects list --format=json and bq ls --format=prettyjson --project_id=... to inspect metadata for accessible projects. It performs zero SQL queries, no model execution, no dataset creation, no storage writes, and no snapshot regeneration. A nonzero return code indicates that no reporting candidate was found (1) or discovery was unavailable (2). It does not print CLI stderr or credentials.

**Do not paste Google Cloud credentials or service-account keys into GitHub or chat.** If a candidate dataset is found, verify its actual lineage, location and authorization, then estimate bytes via a BigQuery dry-run before any paid query.

## Release acceptance — issue #9

1. Identify the authorized GCP project and region holding raw/staging/mart/reporting datasets. Metadata discovery alone is not proof of correct provenance.
2. Verify underlying IEEE-CIS source identity, dbt lineage and source row counts against the committed historical snapshot.
3. Produce a query plan/dry-run estimate; check quotas and obtain explicit cost approval before billable queries or writes.
4. Run validated dbt models/tests; regenerate the snapshot only when source evidence supports it; reconcile figures.
5. Release a new snapshot with its actual refresh timestamp, or retain the historical snapshot if the competition dataset is unchanged.

This read-only script does not independently certify that reporting values are current or that the dataset is linked to real-time banking transactions.

## Service-account JSON option (no gcloud login required)

An authorized person may supply their existing Google Cloud service-account file directly to the **read-only metadata** check without any shell account switching:

~~~bash
python scripts/discover_reporting_service_account.py --credentials-file /private/path/workintech-key.json
~~~

The command uses OAuth with BigQuery **read-only** scope and lists dataset names in the service-account's project, or a specified `--project` for which it has IAM access. It performs no SQL, no storage writes, and **does not log or commit the JSON key**. Do not paste private keys in notebook cells, CI environment outputs, GitHub comments, or shared folders. The 
service account's `project_id` field identifies its parent project but **does not establish** that the IEEE-CIS reporting datasets live in that project.

A ChatGPT sandbox without outbound OAuth/BigQuery network connectivity cannot authenticate this credential or verify IAM permissions, even if the JSON file parses correctly. Dataset presence/freshness remains unverified until a trusted network-enabled execution returns a report. Revoke/rotate any key exposed through chat after the work.
