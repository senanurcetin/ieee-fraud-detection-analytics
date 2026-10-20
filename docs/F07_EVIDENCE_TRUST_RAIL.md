# F07 — NEXUS evidence provenance rail

> Current scope: full-source F03/F04 research has measured canonical results; model promotion and BigQuery parity remain separate. The 19 October release passed exact-SHA/HTTPS and container checks. Playwright is disabled at the owner's request. Use [release status](RELEASE_STATUS.md) for the current gates.

The public dashboard and secondary Decision Studio now disclose source history and
the model-score contract alongside charts, not hidden in an unrelated FAQ.

## Read-only contract

`GET /api/evidence-status` reads the **committed** dashboard snapshot only.
It never queries BigQuery, refreshes a reporting mart, or infers recency from
the API request time. It reports the source `meta.refreshed_at` in UTC,
elapsed calendar days, the 27 report groups and 24 unique physical reporting
tables, and the scope of historic readiness PASS values.

The source-parity verdict stays `not_verified_against_current_bigquery`
regardless of old snapshot readiness scores. A timestamp less than 30 days old
is still `historical_dated`, *not live*. Missing, naive, malformed or future
timestamps are `unavailable`/`timestamp_unverified`, never silently set
to today's date. The source timestamp represents snapshot construction, not
banking transactions' real dates; IEEE-CIS `TransactionDT` is relative.

This is portfolio research on masked IEEE-CIS records, not a real-time fraud
stream or a customer identity/credit/payment enforcement system.

## Model evidence

- The current `predicted_fraud_probability` source is an uncalibrated
  **ranking score**. No unverified calibrated-probability wording is introduced.
- Model explanation is `global_importance_heuristic` unless a genuine,
  locally validated TreeSHAP artifact with matching model version exists.
- Full-source F03/F04 experiments have canonical measured evidence. BigQuery parity, published-model promotion and any real-data F05/F06 claims require separate evidence; a green CI does not establish them.

## Frontend behavior

The source/model trust rail is visible above the primary nine-page dashboard.
The secondary Decision Studio has its own matching provenance disclosure.
Both display explicit unavailable provenance when the evidence endpoint
is inaccessible. The control uses text nodes, not innerHTML, and remains
visible at narrow widths and during data source errors.

The existing BI navigation, threshold selector, filters, export behavior and
historical snapshot content are unchanged.

## Acceptance gates

```bash
pytest -q tests/python/test_f07_evidence_status.py
ruff check webapp/main.py tests/python/test_f07_evidence_status.py
```

Synthetic FastAPI tests verify reported dates, missing/future timestamps,
read-only warehouse isolation, public bounded response and both UI contracts.
Visual/browser smoke tests and official production deployment remain separate
from those source-level tests.
