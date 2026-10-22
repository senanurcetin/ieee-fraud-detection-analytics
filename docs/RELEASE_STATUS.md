# Release status and acceptance gates

**Reviewed: 22 October 2026.** This is a noncommercial historical research release. Source and model measurements retain their actual execution dates; documentation review does not refresh data.

## Current delivered evidence

| Area | Decision and evidence |
|---|---|
| Full source reconciliation | **PASS, dated 21 October.** All 27 public groups across 24 sources reconcile; 26 strict matches and one explicitly disclosed floating-aggregation equivalence. [Canonical audit](../webapp/research/source-parity.json). No cloud SQL jobs, cloud writes or raw-record exports. |
| Model calibration and robustness | **PASS for versioned retrospective research.** Full 590,540-row LightGBM500 study; three earlier development windows select Platt before final evaluation. Brier 0.023268 versus raw 0.063165 and prior baseline 0.033247. [Methods, support and uncertainty](research/COMPLETED_VALIDATION_2026-10-21.md). |
| Kaggle publication | **COMPLETE and public.** Original source recovered, independent random/time companion complete, and [LightGBM500 calibration notebook](https://www.kaggle.com/code/senanuretin/ieee-cis-lightgbm500-temporal-calibration) completed as version 2. Repository and downloaded notebook source/digests agree. |
| Public research contract | `/research`, `/api/research/calibration` and `/api/research/source-parity` serve committed aggregate evidence. Invalid, missing or changed evidence fails closed. Historical v2 scores remain uncalibrated. |
| NEXUS identity | Official Drive SVGs match byte-for-byte. Dashboard, Studio and research use the official X. Brand colors and sans-serif typography were compared with the local NEXUS Commerce and MS Capital sources. See [brand provenance](BRAND_IDENTITY.md). |
| Native browser evidence | [22 October Chromium desktop/mobile capture](assets/native_browser_provenance_20261022.json), including six real screenshots, nine dashboard page selections, theme controls and Studio tabs. The record identifies its actual target and normalized source hashes. No Playwright. |

The bounded historical acceptance for issue #9 and issue #20 is supported by the [completed validation report](research/COMPLETED_VALIDATION_2026-10-21.md). It does not establish prospective customer-data validation, operational scoring approval or automatic payment interventions.

## Source and model separation

The dashboard serves **historical JSON snapshots**, built **10 September 2026** (`2026-09-10T19:41:45Z`). The published `lightgbm-v2-v339-missingness-filtered` model's `predicted_fraud_probability` remains an **uncalibrated ranking score**.

`lightgbm-v3-temporal-calibrated-20261021` is a new, separately evaluated fit with training-only preprocessing and distinct calibration/evaluation windows. Its probability mapping applies only to its own scores. The historical v2 weights, dashboard observations and snapshot timestamps were not replaced. Research acceptance is not live transaction monitoring, verified customer identity, prevented loss, or a production banking-model sign-off.

## Engineering and deployment verification

The last already merged revision, [PR #46](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/46), is `b280568df8db6ef095e2220d64a9bec1b096d675`:

- [Main CI](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39494241953): 256 tests, Ruff, compilation, dependency audits and dbt parse passed.
- [Exact public HTTPS/SHA attestation](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39494268807): passed on that revision.
- [Prior Docker smoke](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39245073372): passed on `2c54bb3`; it is not represented as a new revision's container result.

The completion change requires its own PR CI and merged-main checks. Its PR/check records are the authoritative revision-specific results; the earlier counts above are explicitly historical. Full-source dbt rebuilding is not part of metadata-only push/PR CI.

## Browser and zero-cost release policy

The current noncommercial presentation acceptance uses installed Chromium through native CDP. Firefox/WebKit coverage and print/download edge cases are not claimed by that limited native acceptance. The prior tri-engine Playwright workflow remains disabled under the owner's instruction. Earlier browser records retain their dates; no new cross-engine result is inferred.

Public routes never perform cloud queries or training. Authorized full source reconciliation uses bounded tabledata reads and local in-memory SQL. Raw competition records and credentials remain outside Git and public APIs. Training uses free Kaggle CPU. There is no payment integration, paid-plan activation, billing change or recurring release-monitor automation.

## Navigation

[Completed validation](research/COMPLETED_VALIDATION_2026-10-21.md) · [Documentation index](README.md) · [Architecture](architecture.md) · [Published historical model](model_validation_evidence.md) · [Kaggle notebooks](../notebooks/README.md) · [Public attestation method](PUBLIC_RELEASE_ATTESTATION.md)
