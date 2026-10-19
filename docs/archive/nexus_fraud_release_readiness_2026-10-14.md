# NEXUS Fraud — Release Readiness Audit (14 October 2026)

> **Retrospective release note — 14 October 2026:** The audit below was written while PR #4 was still a draft. PR #4 subsequently merged (`9f201bb`); Vercel production and **12/12 live Chromium browser tests** passed. README image update PR #5 and documentation reconciliation PR #6 were also merged. The original `draft` and `production unchanged` statements below are **historical at the time of that pre-release audit**, not present-day blockers. Dataset reporting snapshot date (10 September 2026) remains unchanged and is not a live bank feed.

---

**Candidate:** [draft PR #4](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/4), `design/nexus-fraud-chart-hierarchy-20261013`  
**Production:** unchanged; this audit does **not** approve or trigger a merge.  
**Evidence scope:** reproducible local Windows FastAPI server with the committed, governed BigQuery reporting snapshot. Local testing is not a GitHub-hosted CI run.

## Verified

| Check | Result | Evidence |
| --- | --- | --- |
| Python tests | PASS | **36/36 passed** in the full local `python -m pytest -q`; repeated under an isolated FastAPI **0.136.3** installation with exit code 0. |
| Static lint | PASS | `python -m ruff check .`: All checks passed. |
| Compile | PASS | `python -m compileall -q webapp`. |
| dbt parse | PASS | DuckDB adapter, `dbt parse --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev`. |
| Dependency scan | PASS | Unignored `pip-audit -r requirements.txt` on the **final FastAPI-aligned requirements** reported **no known vulnerabilities**. Removed the old PYSEC-2024-277 ignore from CI. |
| Chromium regressions | PASS | All **11** scenarios in `tests/browser/test_fraud_dashboard.py` passed locally. |
| Cross-engine tests | PASS | **Chromium, Firefox and WebKit**, each at 1440px and 375px, across all nine main and supporting views; no empty visual containers, document overflow or uncaught JavaScript errors. |
| Exports | PASS | CSV download/parse across engines, UTF-8 BOM, test-only spreadsheet formula injection escaping. Chromium produced valid PDF bytes; inspected a prior full-page print with four nonempty text pages. |
| Accessibility interaction | PASS FOR TESTED PATHS | Explicit Inspect button can be operated with keyboard. Focus enters dialog, is trapped while open and returns when Escape closes it. Not a certified WCAG audit. |
| Snapshot consistency | PASS | Independent checks reconcile 590,540 portfolio transactions, 118,108 holdout transactions, 4,064 holdout fraud cases, precision/recall/workload/FPR, calibration ECE and validation risk-band totals. |
| Qualitative and quantitative labeling | PASS FOR TESTED VIEWS | ROC/PR displayed paths are based on 16 published holdout thresholds; full holdout AUC metrics are not falsely presented as area under those sparse paths. No synthetic drill action scores. |

## Dataset and model caveats that must remain visible

- `webapp/snapshots/dashboard.json` reports `refreshed_at=2026-09-10T19:41:45Z`. This is an **historical reporting snapshot**, not current transaction monitoring. The app now makes snapshot age visible. A rebuild is needed only when the governed marts/source evidence change, but it cannot be claimed live.
- The IEEE-CIS training dataset is observational and masked. No invented identities, geography, deployed investigations, or real customer outcomes.
- Model holdout performance must not be mistaken for deployed causal effects. Holdout Brier error exceeds the constant-risk baseline; the interface flags unreliable probability calibration.
- Hypothetical review costs, net benefits and missed monetary amounts are explicitly labeled as scenario estimates and proxies. No actual loss or chargeback cost field was supplied.
- CSV exports read page-level reporting groups; not every chart uses reaggregated records under every slicer. Do not market each CSV as a row-perfect reconstruction of every active filter.

## External blockers: **NOT CLOSED**

1. **Vercel deployment quota.** Latest branch SHA cannot receive a new hosted preview today. A direct API deployment attempt returned HTTP **402** / `api-deployments-free-per-day` (over 100 deployments) with `retryAfter=86400` seconds. GitHub's Vercel commit status also reports build-rate-limit failure and another pending deployment check. No plan upgrade was authorized or made.
2. **Preview protection.** The existing Vercel project has deployment protection enabled for preview aliases. Any future preview needs an authorized team session or an explicit owner decision about exposure; do not remove SSO/protection merely to obtain a public link.
**Free-tier build conservation:** submitted a Vercel project `commandForIgnoringBuildStep` rule that ignores commits with `[skip ci]` but allows ordinary commits to build. Vercel accepted the settings update. The project read endpoint does not expose this field, so its actual effect is **not independently verified**; it cannot remove today's hard API deployment quota. A future intentionally deployable, non-skipped release commit (or an explicitly overridden manual release) is needed after quota reset.

3. **GitHub-hosted CI.** No successful GitHub Actions run is attached to the draft's tip SHA because development commits used `[skip ci]` to conserve the user's quota. Local parity checks have passed but are **not** a substitute for a required GitHub-hosted CI status.
4. **Owner's visual sign-off and production release.** Neither design approval nor production merge/deploy has occurred.

## Safe next release gate

1. After the Vercel daily quota resets, create **one preview deployment** against the exact current PR tip SHA (no paid plan upgrade), verify it reaches `READY`, and verify its project/version and environment. Do not use an old READY deployment to claim the new revision is published.
2. Access the preview through the owner's authorized Vercel session and repeat smoke tests against that exact URL. Deployment protection should stay on unless the owner explicitly changes it.
3. Complete the intended GitHub Actions gates within the user's approved Actions budget; do not mark CI green from local results alone.
4. Obtain visual approval from the owner. Only then merge PR #4 and verify the real production site and current data provenance.
5. If governed BigQuery marts are rebuilt, regenerate `webapp/snapshots` with the authorized credential path and repeat the offline consistency suite. Never create substitute benchmark metrics.

## Reproduction commands

```powershell
# From repository root; Python and dependencies already installed
python -m ruff check .
python -m pytest -q
python -m compileall -q webapp
dbt parse --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
python -m pip_audit -r requirements.txt

# In a separate terminal:
python -m uvicorn webapp.main:app --host 127.0.0.1 --port 8891

$env:FRAUD_E2E_BASE_URL="http://127.0.0.1:8891"
python -m unittest discover -s tests/browser -p test_fraud_dashboard.py -v
python -m unittest discover -s tests/browser -p test_fraud_release_acceptance.py -v
```

**Current decision:** Keep PR #4 **draft**, retain production unchanged, and do not pay to bypass the Vercel limit.

### Dependency pin parity

The repository root and `webapp/requirements.txt` and `pyproject.toml` all pin FastAPI **0.136.3**. Since the local global environment was 0.136.1, the full 36-test suite was also run successfully against FastAPI **0.136.3** installed into an isolated temporary QA directory. No global Python environment upgrade was made.

## Final gate — risk cohort and preview consistency

During inspection of the actual protected Vercel preview, a cross-filtered risk-band drill showed missing cohort counts as zero. The dashboard now reads the governed `model_risk_bands.observed_fraud_count` and `observed_fraud_rate` fields, marks their `train` split explicitly, and preserves holdout and daily charts as separately scoped evidence. For the Critical training cohort, the published snapshot contains **5,710 labeled frauds in 5,906 transactions (96.68%)**. No segment monetary amount is published: exposure, capture dollars and net-benefit scenario read **Not reported / Unavailable**, never fabricated $0.

An accidental duplication of the HTML script/markup during an intermediate edit was removed by rebuilding from the single-document, previously validated revision. Exactly one `</html>` and one `renderDrillThrough` remain. Node syntax and the dedicated desktop/mobile risk-filter regression passed locally. The production release candidate must obtain **new GitHub-hosted CI** and **new Vercel READY preview** statuses for its exact tip commit; passing results attached to earlier commits cannot substitute.

Deployment protection remains enabled. Only user-authorized preview access was used for the live smoke test. No paid upgrade, production merge or unapproved data replacement has occurred.
