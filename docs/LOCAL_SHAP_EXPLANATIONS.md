# F05 — Verified instance-level TreeSHAP (offline-first)

## Problem

The pre-existing \`/api/enterprise/cases/{id}/explain\` combines **global**
LightGBM feature importance rankings with human-readable observations about
a transaction. It was *not* local TreeSHAP: a high global feature ranking does
not show the signed effect of that feature for an individual transaction, and
simple price thresholds cannot prove causal effects.

The new F05 path explicitly distinguishes the existing heuristic from
**real local model attribution**, verifies mathematical additivity and keeps
the model training artifacts private. IEEE-CIS transaction attributes are masked
and historical. Raw ranking scores are **not** calibrated fraud probabilities.

## Producing real local attributions

The next **authorized full-data** execution of the existing local pipeline

~~~bash
python src/prepare_raw_and_ml.py
~~~

fits the LightGBM model and selects a sample of the *temporal validation
holdout* (bounded by \`SHAP_SAMPLE_SIZE\`, default 20,000). It builds TreeSHAP
on the *actual trained model* and preserves the exact sampled TransactionIDs.

New output on the local filesystem:

~~~text
outputs/tables/local_shap_explanations.sqlite
~~~

For each sample row it records:

- Model version, source split, transaction ID and evidence format version
- True binary-class local TreeSHAP **signed feature contributions** in
  LightGBM **raw-margin/log-odds space**; top 8 only, no original feature values
- SHAP base value, all-feature contribution sum, top/omitted contribution sums,
  model raw margin and verified additivity residual (tolerance 0.001)
- Uncalibrated ranking score, **explicitly not a validated probability**
- Explanation limitations and redacted metadata

The pipeline checks that the sum of the base raw margin and **all** signed
feature contributions reconstructs the actual LightGBM raw margin, and checks
that its sigmoid matches \`predict_proba\`. Invalid or nonfinite measurements
fail rather than fabricate local explanations.

The SQLite file is written as a local private artifact through atomic
replacement. \`outputs/tables/\` is Git-ignored. **Do not commit the artifact,
case-level data, labels, customer identifiers or model secrets.**

The global SHAP chart remains unchanged. This new local output is sampled
on the *validation holdout* only, not on all historical cases; not every
\`TransactionID\` is expected to have a verified local attribution.

## Protected read API

Configure the authorized application server with:

~~~text
WEB_INTERNAL_REFRESH_TOKEN=<strong-server-side-secret>
WEB_LOCAL_SHAP_DB_PATH=/private/fraud/local_shap_explanations.sqlite
~~~

Then an **internal**, authenticated request may read a precomputed case:

~~~bash
curl -H "X-Internal-Refresh-Token: $WEB_INTERNAL_REFRESH_TOKEN" \
  "http://127.0.0.1:8000/api/enterprise/cases/123456/local-explanation"
~~~

This endpoint is NOT a public case API. It returns:

- HTTP 403 if the internal token is missing or invalid.
- HTTP 503 if no private artifact exists, is unreadable, has the wrong model
  version / split, or fails the additivity evidence gate.
- HTTP 404 for cases not represented in the measured validation sample.
- HTTP 200 with verified local contribution data only when all gates pass.

The endpoint does **not** run BigQuery, retrain LightGBM, perform expensive
SHAP computations, mutate data or silently replace a missing explanation
with a global heuristic. A secret never belongs in browser JavaScript,
public websites, a query string, CI logs or version control.

The existing \`/api/enterprise/cases/{id}/explain\` retains its historical
compatibility but explicitly marks \`is_local_shap=false\`,
\`explanation_type=global_importance_heuristic\` and
\`calibrated_probability=false\`. It remains protected by F01's warehouse
access gate in BigQuery mode.

## Offline CI acceptance

~~~bash
pytest -q tests/python/test_local_shap.py
ruff check src/local_shap.py src/prepare_raw_and_ml.py \
  webapp/main.py tests/python/test_local_shap.py
~~~

Tests cover raw-margin SHAP additivity including **a trained synthetic
LightGBM model**, wrong SHAP class format, score mismatches, duplicates,
invalid inputs, private artifact atomicity, authorization, missing cases,
incorrect model versions, and absence of warehouse fallback.

## Release gates

- [ ] Run the existing full IEEE-CIS pipeline in an authorized local
  environment; record model/dataset digest, training environment and version.
- [ ] Verify the actual measured sample cohort and that base SHAP margin plus
  full signed contributions reconstruct every corresponding raw margin.
- [ ] Match any published cohort to the released model version, ensure access
  controls and artifact retention policies meet the intended use case.
- [ ] Prove that the legacy global heuristic remains clearly labeled rather
  than presented as instance-specific model explanation.
- [ ] Only then consider a product-grade review UI with real attribution
  breakdowns; do not invent explanation data for unsampled transactions.

Passing synthetic CI validates the contract but **does not mean** full-data
local explanations were generated or the historical dashboard was refreshed.
