# Fraud Risk Intelligence — BigQuery and Kaggle acceptance plan (17 October 2026)

> **Paused as of 18 October 2026:** The owner suspended further project work. The F03/F04 work below is already supported by [canonical real-data evidence](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md). BigQuery source parity, full reporting reconciliation, model promotion and public Vercel release remain unverified. This plan is retained for later resumption only; do not auto-run manual workflows. See [pause handoff](RELEASE_STATUS.md).

This page is an **execution plan**, not an assertion that the source and model
release gates have passed. It replaces assumptions with exact access, data
quality and reproducibility checks and preserves the public September historical
snapshot until approval.

## Evidence already verified

- Main commit `a30a603ac1cddd4e6924212457a4e1b4f1dc982e` passed Python/dbt
  CI. Prior exact-main Docker and three-engine browser tests passed.
- Kaggle workflow [#39063907895](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39063907895)
  downloaded full IEEE-CIS competition data and successfully tested all
  **590,540 train transactions**. Random-vs-chronological 80/20 ROC-AUC:
  **0.920220 vs 0.893140**, AP: **0.619111 vs 0.485269**. Details and
  source SHA: [full-source evidence](KAGGLE_FULL_SOURCE_VALIDATION_2026-10-17.md).
- Historic GCP inspection confirmed **`workintech-working`**,
  **`fraud_project_reporting`**, location **US**. There are 24 physical
  reporting tables behind 27 dashboard groups. This is **not** proof of
  present-day row parity; [see source evidence](BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md).
- As of this audit, ChatGPT's provider-native BigQuery plugin reports
  `DISABLED_BY_ADMIN`. No BigQuery API call can be made **inside** this
  assistant session merely because an account is connected elsewhere.

## Ordered stages and explicit acceptance criteria

| Stage | Work | Acceptance artifact | Blocker / risk |
|---|---|---|---|
| F02-A | Keyless GitHub OIDC -> workload identity; read-only BigQuery source | Actual manual workflow run, confirmed federation & dataset access | Repo-specific WIF impersonation must be allowed |
| F02-B | Compare 20 direct report groups with bounded list_rows; skip five derived + two filtered | Sanitized JSON, source table status and diff hashes, zero SQL jobs | 7 unverified groups, no unconditional snapshot refresh |
| F03 | Temporal hygiene training on actual Kaggle IEEE-CIS, fold-fitted encodings and V missingness | Full-row provenance JSON, chronological holdout/CV metrics | Manual Kaggle `temporal_hygiene` workflow selection |
| F04 | Platt vs isotonic and constant-prior on disjoint time windows | Full-row Brier, ECE, log loss, AP/ROC and reliability bins | Manual Kaggle `calibration` selection; no promotion without review |
| F02-C | Resolve derived/filtered report group mappings and discrepant report narrative | Field-level contract evidence and authorized cost/dry-run gates | Separate approval before billable SQL/dbt |
| F08 | Exact-head production release, historical data labeling and browser acceptance | Vercel SHA, public HTTP test and current dashboard review | Vercel quota and protection |

## Keyless BigQuery workflow

We use the manually dispatched
[BigQuery Read-Only Source Parity](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/bigquery-source-parity.yml).
It has no `push` or `pull_request` trigger. It uses GitHub OIDC and the
Google-maintained `google-github-actions/auth@v2` action, **not a JSON private
key**. OIDC requests a temporary identity and impersonates a read-only
service account. The scanner receives ADC with the
`https://www.googleapis.com/auth/bigquery.readonly` OAuth scope.

### Prerequisites for *this specific Fraud GitHub repository*

Under GitHub repo **Settings -> Secrets and variables -> Actions ->
Variables -> New repository variable**, configure:

- `GCP_WIF_PROVIDER`: the **fully qualified** Google Workload Identity
  Federation provider resource name (e.g. `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER`). Use the *actual*
  number and existing provider, never substitute a guessed value.
- `GCP_BIGQUERY_READONLY_SA`: the exact email of the approved
  read-only service account. This is a **non-secret repository variable**,
  not its JSON private key.

### Previously established GCP identity and exact Fraud repository scope

The owner's earlier WorkinTech federation setup was named pool `nexus-gha`,
provider `nexus-main`, service account
`nexus-bq-readonly@workintech-working.iam.gserviceaccount.com`.
These are **historical setup identifiers, not evidence of current live IAM**.
Obtain the actual numeric Google Cloud project number from the provider
details; the complete provider variable has form
`projects/<ACTUAL_PROJECT_NUMBER>/locations/global/workloadIdentityPools/nexus-gha/providers/nexus-main`.

The actual Fraud GitHub repository numeric ID is **`1242336340`**
(verified from GitHub repository metadata). Earlier e-commerce WIF setup
notes scoped the provider to repository ID `1217831974`, main ref and
`workflow_dispatch`, with a similarly restricted impersonation binding.
Therefore **do not assume** that the Fraud repository can impersonate this
service account. The pool/provider attribute condition, if still restricted
to the old repository, must explicitly permit the Fraud ID **without deleting
the old ID**, while maintaining `refs/heads/main` and
`workflow_dispatch` constraints. The service account must separately
authorize `roles/iam.workloadIdentityUser` for the *Fraud* mapped GitHub
principal `attribute.repository_id/1242336340` (assuming that provider
attribute mapping is still in place). Dataset reader IAM must also cover
`workintech-working.fraud_project_reporting`.

Use the **existing manual workflow on `main`** for this GCP access.
The single-use research branch is `push`-triggered and **must not be
added to the GCP trust policy** just to bypass these restrictions.

The service account must have the minimal dataset permissions to
`get_dataset`, `list_tables`, `get_table` and bounded `list_rows` on
`workintech-working.fraud_project_reporting`. Its IAM WIF
`roles/iam.workloadIdentityUser` binding must **explicitly trust the subject
of `senanurcetin/ieee-fraud-detection-analytics`**; a binding restricted
to a different GitHub repo will not work. Prefer repo-scoped principal and
provider attribute conditions, never organization-wide wildcard grants.

A previously created federation pool or principal for an **e-commerce**
repository does not automatically authorize Fraud. If provider policy or IAM
is missing, the workflow fails rather than attempting privilege escalation.

Use **Actions -> BigQuery Read-Only Source Parity -> Run workflow -> main**.
An error at authentication is **BLOCKED**, not a verified source.
A successful read-only inspection can return
`DIRECT_TABLES_MATCH_PARTIAL_ONLY` (20 direct groups matched), or fail with
`DIRECT_TABLES_UNRESOLVED` (mismatches, schema changes, access/errors).
Both states are **partial**; neither means a live bank fraud system.

### Safety

- Uses only BigQuery `get_dataset`, `list_tables`, `get_table`,
  bounded `list_rows` with no SQL query or refresh.
- Each direct table is refused if metadata has more than 10,000 rows.
  Never downloads raw fraud transaction facts.
- Reports are sanitized JSON with counts/status/schema and hashed diff
  examples, not row values. Retention: 7 days.
- Files are removed from the runner after execution. `main` snapshot's
  `2026-09-10` historical refresh timestamp remains unchanged.
- BigQuery read-only API calls may use quotas; **zero SQL query jobs is not
  the same as a blanket guarantee of zero cloud charges**. Do not enable
  new billable services or execute SQL without explicit approval.

## Kaggle follow-up

The first `random_vs_time` run and the F03 `temporal_hygiene` / F04
`calibration` full-source runs **have now completed** as separately evidenced:
[canonical deterministic temporal and calibration measurements](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md).
The user-authorized initial run [#39067832865](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39067832865) executed both studies; BigQuery auth was **skipped** because both Fraud WIF repository variables were empty. Later, independent deterministic full-source repeat [#39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816) successfully ran F03 and F04, and verified **identical input row fingerprints across both runner jobs**. Use the latter for canonical numerical model metrics; it made no BigQuery API calls. Repeats of the research studies remain manual via the standard opt-in workflow below. Select each explicitly from
[Kaggle Research Evidence](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/kaggle-research-evidence.yml)
on `main`:

1. `temporal_hygiene`: 100 estimators, full-row feature fitting and
   chronological validation with one CV window.
2. `calibration`: 150 estimators, nonoverlapping train-calibration-final
   windows; Platt, isotonic and constant-prior comparison.

Do not silently turn protected Kaggle downloads into push/PR triggers or
report subsets as 590,540-row results. If the GitHub runner runs out of memory
or time, retain the failed-run evidence and use an authorized larger compute
environment with the same full source hash and exact Git SHA. Uploaded
experiment reports contain only aggregate results; the original CSV stays
in the ephemeral runner.

## Scientific and release decisions

- Favor chronological model validation when deploying into future time
  periods, but avoid assuming the current 0.02708 random-vs-time AUC gap
  proves a specific leakage mechanism.
- Accept calibrated fraud probabilities **only after** the full disjoint
  temporal experiment and independent scientific review, not from synthetic
  test fixtures.
- BigQuery source-parity acceptance does not replace model calibration.
  Neither acceptance automatically refreshes historical published data or
  bypasses [production attestation](PUBLIC_RELEASE_ATTESTATION.md).
- Track source parity in [issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9),
  missing original Kaggle notebook/research in [#8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8),
  calibration in [#20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20),
  and public deployment in [#29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29).
