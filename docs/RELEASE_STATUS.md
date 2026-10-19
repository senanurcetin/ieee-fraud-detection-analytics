# Release status and acceptance gates

**Engineering resumed:** 18 October 2026, at the owner's request. This page separates current local verification from dated research and external acceptance. See the [development plan](DEVELOPMENT_PLAN.md) for scope and [Actions](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions) for hosted results.

## Current engineering delivery

The project is an active **noncommercial historical research application** with a $0 operating budget. The earlier pause is superseded for this development work. No release-monitor automation has been re-enabled, and the published data/model artifacts retain their original dates.

This iteration improves offline API reliability, validated transactional research imports, private SQLite artifact rotation on Windows, and Decision Studio loading/error/keyboard behavior. The dbt score contract now rejects null risk bands. The owner-approved Drive transparent logo was rechecked against the tracked SVG: SHA-256 `143788fc114348b03bcef5285c134d63135bd7dbd908380e973596f743c9f45b` matches exactly. One redundant closure checklist was removed; three superseded dated reports moved to `docs/archive/` with links updated.

### Verification for this iteration

**Final local verification: 19 October 2026.** Continued verification follows the owner's instruction not to use Playwright. No browser automation was run during this continuation.

| Check | Observed result | Scope |
|---|---|---|
| Full Python suite | **248 passed**, exit 0; 8 dependency/SHAP warnings | Python 3.11.9, Pytest 9.1.1, plugin autoload disabled, unique temporary directory; includes SQLite lifecycle and API deletion-race regressions |
| Ruff | **PASS** | Repository-pinned Ruff 0.4.10; no blanket exclusions added |
| JavaScript syntax | **PASS** | `node --check webapp/static/risk-decision-studio.js` |
| Python compilation | **PASS** | `python -m compileall -q webapp src scripts` |
| SEO and source-image contracts | **PASS** | `python -m scripts.check_seo_assets` |
| Markdown/archived-link integrity | **PASS** | Included in Python suite; moved evidence remains reachable |
| dbt deps and local parse | **PASS on 18 October** | DuckDB target only; installed dbt 1.11.10 / adapter 1.10.1, not an assertion of pinned CI dependency parity or a full source build |
| Direct local HTTP | **PASS_HISTORICAL_OFFLINE_DEMO** | FastAPI 0.136.3 with pinned web requirements, Python 3.12.13, loopback server; source timestamp remains `2026-09-10T19:41:45Z` |

The earlier **18 October** Chromium dashboard/Studio run passed **16 tests**, including retry and keyboard interaction; desktop/mobile screenshots were inspected at 1440, 375 and 320 pixels. This is dated prior evidence, not a new browser acceptance claim after the owner's 19 October restriction. Existing browser test source is retained, but no browser workflow was dispatched. A new cross-engine result is not claimed.

Local results do not establish hosted CI status, current BigQuery reconciliation, real-data retraining, Docker acceptance on this revision, model promotion or a new production deployment. Check the reviewed commit in GitHub Actions independently. The JUnit report is generated under ignored `outputs/qa/`, not included as source or competition data.

### Existing scientific evidence retained

Canonical deterministic full-data research was merged in [PR #42](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/42), merge `0ed99cf7598a63e7383dca6c92d8f854b8d6607c`. Its [main CI run #39070386467](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39070386467) passed the then-current checks. Both source-fingerprint-matched jobs in [research run #39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816) passed; permanent aggregate metrics remain in the [canonical report](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md). These are dated results, not evidence for the current development branch.

### External dependencies

- **BigQuery:** No standard local ADC file or GCP credential environment was available during inspection. GitHub repository variable listing returned no variables, so Fraud-specific WIF variables are not configured. Repository-scoped WIF setup and all-group parity remain open ([issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9)). No paid query, dataset write or dbt cloud rebuild was performed.
- **Kaggle:** The local credential file is present, but an actual read-only `kaggle competitions files -c ieee-fraud-detection` call returned **401 Unauthorized**. Local authentication needs renewal. The GitHub repository contains a `KAGGLE_API_TOKEN` secret name; its value was not read and its validity was not inferred. Existing full-data research is retained without retraining or redistributing source records. Original public notebook recovery remains open ([issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8)).
- **Model promotion:** Independent governance and production-target calibration remain open ([issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20)). The public ranking score is still uncalibrated.
- **Public deployment:** An exact-SHA Vercel release and current public browser/HTTP attestation remain open ([issue #29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29)). Local acceptance is a separate result.

## Supported scope

The published UI is a **historical, masked IEEE-CIS fraud analytics demonstration**. Its current dashboard snapshot was generated **10 September 2026**. The hosted web application and its real browser tests are not evidence of live financial processing, active fraud alerts, calibrated probability estimates or verified current source parity.

| Gate | Last verified evidence | Closure rule |
|---|---|---|
| Python quality, dependency scan and dbt parse | PR/main CI passed for the preceding engineering release | Exact-head [CI workflow](../.github/workflows/ci.yml) passes; routine CI does **not** build all real-source models |
| Docker/HTTP snapshot demo | Real Compose build, startup and HTTP smoke passed | [Container workflow](../.github/workflows/container-smoke.yml) green on the reviewed source |
| Nine-page report and historical Studio | Chromium, Firefox and WebKit tests passed | [Browser workflow](../.github/workflows/browser-acceptance.yml) green on the reviewed source |
| Public Vercel release | **Open — do not infer from READY** | [Public attestation workflow](../.github/workflows/public-release-smoke.yml) proves exact SHA and actual HTTPS source/UI responses |
| BigQuery source content parity | **Open — partial historical evidence only** | Authorized all-group reconciliation, lineage, real source timestamps and cost gating ([issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9)) |
| Model experiment reproducibility | **Partial PASS — 17 Oct real Kaggle run**: complete 590,540-row new random-vs-time comparison verified in [run #39063907895](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39063907895) | Original lost Kaggle notebook and verified public Kaggle notebook publication remain open ([issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8)) |
| Temporal model calibration acceptance | **Research PASS / production OPEN:** full-data F03 temporal and F04 60/20/20 Platt/isotonic experiments passed in [deterministic replay #39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816); [canonical deterministic measured evidence](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md) | Top-k queue metrics are now measured; production promotion still requires model/feature scope matching, prospective validation and independent governance review ([issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20)) |

The outstanding **production deployment and public HTTP** requirements are tracked in [issue #29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29). Vercel Hobby daily deployment quota prevented an exact-commit rollout on 17 October; never upgrade a paid plan or weaken SSO solely to force green status.

## Primary evidence links

- [Current CI](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/ci.yml) — check commit SHA and conclusion rather than relying on a screenshot.
- [Real browser acceptance](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/browser-acceptance.yml) and [container acceptance](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/container-smoke.yml) — localhost tests only.
- [Production release attestation](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/workflows/public-release-smoke.yml) — public alias and exact SHA; may legitimately fail behind protection or quota.
- [Historical source verification](BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md), [bounded inspection](BIGQUERY_BOUNDED_SOURCE_PARITY.md) and [snapshot parity rules](SNAPSHOT_PARITY_AUDIT.md) — do not conflate 24 physical tables with 27 dashboard groups.

## Release handling

1. Freeze and review a commit; run Python/dbt checks plus browser and container acceptance on **that SHA**.
2. Preserve historical snapshot provenance; do not change `refreshed_at` without an independently verified fresh report.
3. Deploy through existing authorized Vercel controls **only when quota, credentials, and intended target permit**. No secrets in logs or Git.
4. Confirm deployment alias/commit, public HTTP (or explicitly approved protected-auth verification), and no JS/API errors.
5. Record outcomes against the relevant issues; only close a gate after the actual evidence exists.

Any older document claiming all checks PASS refers to a **historical acceptance run**, not a blanket claim of present-day production fraud-model readiness.
