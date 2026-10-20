# Authorized Kaggle research — manual GitHub Actions runbook

This is an **opt-in, Kaggle-only** evidence workflow for the IEEE-CIS historical
fraud project. It does not need Vercel, BigQuery, Google Cloud credentials,
production model promotion or raw-data publication.

## Preconditions (GitHub maintainer)

1. In Kaggle, accept the [IEEE-CIS Fraud Detection competition rules](https://www.kaggle.com/competitions/ieee-fraud-detection/rules) for the Kaggle account that owns the token.
2. Add a fresh Kaggle API token as the GitHub **repository secret** named `KAGGLE_API_TOKEN`. Never paste it in a GitHub issue, PR, command log, documentation, or this chat.
3. The workflow must exist on the repository's **default branch** before GitHub exposes its manual **Run workflow** button.

## One-click execution

1. Visit the [Kaggle Research Evidence workflow](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/kaggle-research-evidence.yml).
2. Click **Run workflow** (button on the right), choose branch `main`.
3. Choose exactly **one** study from the dropdown:
   - `access_check` — credential and IEEE-CIS file download only, no model training.
   - `random_vs_time` (**recommended first**) — complete 590,540-row *train_transaction* random versus chronological holdout with the controlled 150-estimator, restricted numeric-feature comparison; relevant to [issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8).
   - `temporal_hygiene` — full-row, fit-only preprocessing and chronological holdout with 100-estimator/one-fold diagnostic, not the published original 500-estimator baseline.
   - `calibration` — full-row 60/20/20 independent temporal split, 150-estimator LightGBM plus Platt/isotonic/constant-prior; relevant to [issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20).
4. Press the green **Run workflow** button to execute the selected study. Repeat manually for another study only after reviewing the prior run.

The workflow is **never triggered by pushes or pull requests**. It uses
`contents: read`, a 35-minute runner limit, low-thread local CPU training and
temporary competition CSVs. There are no billable BigQuery queries or paid
deployment steps. GitHub Actions usage limits/quotas may still apply.

## Authenticating safely

The job checks only **whether the GitHub secret is nonempty**. That is **not**
proof of Kaggle authentication. It then runs the actual Kaggle competition
download and fails if the account cannot access data.

If the download returns HTTP 401/403 or a competition-rules error, verify
that the Kaggle account accepted the competition terms and regenerate the
token if needed. Do not mask the failure as a model success.

## What you get

On successful completion, open the workflow run's **Artifacts** section and
download its ZIP named `fraud-kaggle-<study>-<run-id>`. Retained **7 days**.

The ZIP contains **only**:

- `source_manifest.json` — competition name, unmodified CSV SHA-256 hashes,
  run ID, exact Git commit, experiment selection, and guardrail flags.
- `research_report.json` — aggregated, reproducible numerical experiment
  metrics (or a no-model credential confirmation report).

No original Kaggle CSV, row-level transaction payload, private credential,
temporary DuckDB store, fitted model or secret is uploaded. Raw files are
removed from runner workspace in a cleanup step even after job failure.

**Evidence interpretation:** a successful `random_vs_time` run is evidence
for a *new* reproducible comparison, **not** proof that a previously missing
Kaggle notebook was recovered or that its claimed historic AUCs were
replicated. A `calibration` run produces *experimental candidate metrics*,
not immediate authorization to relabel published uncalibrated scores as
fraud probabilities. Model promotion requires independent scientific review.

The local DuckDB importer validates expected original train rows:
590,540 `train_transaction`, 144,233 `train_identity`; a different
population blocks temporal experiments rather than quietly changing the
training cohort. Full temporal experiments can exceed 7 GB RAM on free GitHub
runners. If they fail, keep the failure as evidence and run **the same
source/commit-controlled experiment** on a suitably provisioned authorized
machine; do not substitute a smoke sample for full-data acceptance.

## Provenance and closure

Attach only safe result summaries, input SHA-256 and the exact Git run URL
to [issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8)
or [issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20)
after reviewing the actual artifact. Never close these issues solely because
Kaggle access succeeded. Historical report snapshots and production aliases
must remain unchanged by this workflow.
