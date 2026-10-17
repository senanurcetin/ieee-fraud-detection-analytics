# Release status and acceptance gates

**Evidence checked:** 18 October 2026 (final GitHub handoff). This is a dated overview, **not** a substitute for current [Actions](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions), [open issues](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues) or the live [Vercel project](https://vercel.com/).

## Project handoff — PAUSED

The owner explicitly paused this project after merging the canonical deterministic real-data research documentation ([PR #42](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/42), merge `0ed99cf7598a63e7383dca6c92d8f854b8d6607c`). Its [exact merged-main CI run #39070386467](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39070386467) passed Python/Ruff/Pytest/security and dbt parse. Both source-fingerprint-matched research jobs in [run #39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816) passed and have been permanently summarized in the [canonical metrics report](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md); temporary GitHub artifact ZIPs are retained for only seven days. The Fraud-specific `Fraud Production Release` condition-watch automation was **disabled at the owner's request**.

**Pause contract:** Do not initiate new Kaggle experiments, paid cloud queries, BigQuery dataset edits/dbt rebuilds, automatic deployments, screenshot refreshes, model registry changes, source snapshot rewrites or renewed production-release monitoring until the owner explicitly resumes. Keep historical demo and NEXUS brand assets unchanged. An existing separately managed multi-project uptime monitor is not a production-release authorization.

**Unresolved acceptance at pause:** [#8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8) missing original public Kaggle notebook; [#20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20) independent production-target calibration/governance approval; [#9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9) missing Fraud repo-scoped WIF variables and current BigQuery parity; [#29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29) unverified exact production Vercel SHA, current nine-page visual acceptance and public HTTP release. No issue is closed by the pause; no public refresh/deployment is implied.

### Resume checklist

1. Review the canonical research report and `main` CI SHA; preserve the `2026-09-10` published historical snapshot until genuine authorized source refresh.
2. Establish Fraud-specific `GCP_WIF_PROVIDER` and `GCP_BIGQUERY_READONLY_SA` Actions variables and repository-scoped Google impersonation/dataset reader rights; use the **manual, read-only** BigQuery verifier, never the completed one-shot research branches.
3. Reconcile direct and derived/filtered BigQuery groups and get explicit cost approval **before** any SQL/dbt write. Avoid treating metadata or 20-group partial agreement as full 27-group parity.
4. Make an independent decision on producing a versioned, externally validated calibrated model. Keep historical 500-estimator ranker and its public score labels separate from the 150-estimator calibration experiment.
5. Verify exact production Vercel commit/HTTP/three-engine browser acceptance only when quota and permission permit a reviewed release; re-enable the release watch only if explicitly requested.


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
| Temporal model calibration acceptance | **Research PASS / production OPEN:** full-data F03 temporal and F04 60/20/20 Platt/isotonic experiments passed in [deterministic replay #39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816); [canonical deterministic measured evidence](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md) | Do not promote until queue metrics, model/feature scope, prospective validation and independent governance review ([issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20)) |

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
