# F07 — Read-only historical analyst review workspace

The separate NEXUS Decision Studio's Governance tab now includes a
**bounded historical sample** of masked IEEE-CIS transactions for explanatory
analyst navigation. It is not a ticketing system, an anti-fraud alert engine,
a banking case management product or an automated payment decision workflow.

## Behaviour

- Requests no more than 40 existing cases through
  `GET /api/enterprise/cases?limit=40`, using the already governed
  **committed** `enterprise-cases` snapshot. The underlying API has a
  warehouse gate for missing snapshots; this screen never sends a refresh
  authorization token and cannot bypass it.
- Shows transaction ID, historic risk band, masked product, amount band,
  identity coverage and relative TransactionDT day only.
- Scores are labeled **uncalibrated rankings**, not validated fraud
  probabilities. Fraud outcome labels are deliberately excluded from the
  new read-only panel to avoid presenting a known training label as a
  model-generated risk insight.
- Each row uses a native keyboard-operable button with `aria-pressed`.
  Content is rendered exclusively through DOM `textContent`, not string
  HTML interpolation.
- Missing cases, unavailable snapshot and network failure produce explicit
  unavailable states. No synthetic "cases" are fabricated and no BigQuery
  fallback is initiated by the UI.
- No workflow or transaction records are edited. No external notifications,
  enforcement, credit decisions or audit logs are implied.

The existing server-side `build_transaction_explanation` also labels the
historical class-weighted score correctly as an **uncalibrated ranking**;
its former `fraud probability` text overstated the model calibration
evidence.

## CI acceptance

```bash
pytest -q tests/python/test_f07_case_review.py
ruff check webapp/main.py tests/python/test_f07_case_review.py
node --check webapp/static/risk-decision-studio.js
```

These are integration/source/JavaScript syntax checks, not complete live
cross-browser visual validation. Production UI still requires owner-side
browser smoke tests and the separate real-source snapshot parity work
in issue #9.
