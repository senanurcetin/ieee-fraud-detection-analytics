# Noncommercial development plan

Development resumed at the owner's request on **18 October 2026**. This plan supersedes the paused engineering backlog, while preserving dated scientific evidence and all open external acceptance gates.

**19 October verification constraint:** At the owner's request, continued development and final validation do not use Playwright. Existing browser tests are retained as source; no new browser automation or browser workflow dispatch is part of this continuation. Python/API/SQL tests, JavaScript syntax checks, static assets and direct HTTP checks provide the current acceptance evidence.

## Purpose and scope

IEEE Fraud Intelligence is an English-language research and portfolio application for analysts, ML practitioners and reviewers exploring historical IEEE-CIS fraud concentration and decision thresholds. It supports evidence-based investigation of masked competition data. It does not process payments or make customer decisions.

There is **no monetization, subscription, payment integration or commercial launch** in scope. The operating budget is **$0**. The existing Python/FastAPI, static JavaScript, DuckDB, dbt and versioned snapshot architecture is retained because it already supports offline use and avoids a replacement application or database service.

## Delivery sequence and acceptance

| Stage | Work | Acceptance |
|---|---|---|
| Reconstruct | Inspect main, previous handoff, workflows and current data contracts | Preserve source dates, model limitations and uncommitted work |
| Brand | Compare approved Drive logo with tracked SVG and follow NEXUS palette | Exact SVG hash match; locally served official logo only |
| Backend | Make health checks network-free; validate and recover snapshot cache | Tests for unavailable/malformed/replaced snapshots and zero cloud calls |
| Private explanations | Close SQLite writers/readers before atomic artifact rotation | Round-trip, failure and retained-handle lifecycle regressions |
| Research | Make CSV import transactional and validate join keys | Failed validation preserves previous research tables; duplicate/null/orphan identities rejected |
| Interface | Improve Decision Studio loading, error recovery and keyboard navigation | Earlier dated browser evidence retained; continuation uses source contracts and JavaScript syntax checks |
| Documentation | Maintain one current plan and release status; separate dated records | Working local links, clear folder map, redundant closure checklist removed |
| Verification | Run Python, lint, dbt parse and direct HTTP checks | Record only observed results in release status; distinguish local from hosted release |

## Modular architecture and folder ownership

```text
.github/workflows/   CI and explicit research/release entry points
config/dbt/          connection profiles; credentials stay outside Git
src/                 shared data preparation, modeling and explanations
scripts/             import, audit, experiment and release commands
models/              staging / intermediate / marts / reporting SQL
tests/python/        deterministic API, pipeline and evidence regression tests
tests/browser/       actual dashboard and Studio browser journeys
webapp/              FastAPI application and explanation store
  snapshots/         versioned historical reporting JSON, no raw competition CSV
  static/            dashboard, Studio, styles and approved logo favicon
docs/                maintained references and canonical research evidence
  archive/           dated superseded acceptance and preliminary reports
  assets/            official identity and dated screenshots/evidence
infra/bigquery/      optional infrastructure definitions; no automatic apply
```

Backend modules and research scripts remain independently testable. The public interface consumes aggregate snapshot contracts; credentials and raw competition records stay outside public routes. Reuse shared code rather than adding a new service for every experiment.

## Zero-cost operation and scale triggers

| Resource | Default control | Trigger and response |
|---|---|---|
| Public requests | Serve committed aggregates; no per-view BigQuery calls | If free hosting limits are reached, keep the downloadable local demo available and reduce optional payloads |
| BigQuery | Optional read-only metadata/table inspection; no SQL in local acceptance | Missing WIF/ADC or unverified quota blocks cloud verification; never upgrade billing to complete a check |
| Kaggle | Explicit authorized download only; no scheduled training | Verify terms/credentials before a full run; preserve source SHA and deterministic ordering |
| ML compute | Synthetic regression fixtures and existing measured evidence | Re-run full training only for a defined scientific question on available free compute |
| GitHub Actions | Local checks first; manual cloud/release workflows | Avoid repeated workflow dispatches and duplicate deployment loops |
| Storage | Keep raw CSV, DuckDB, model outputs and caches out of Git | Growth in snapshots requires payload measurement and aggregation before adding storage |
| Branding | Tracked official SVG, no remote font/logo dependency | Confirm provenance before replacing artwork |

Free-tier eligibility and remaining capacity must be checked in the relevant provider before a future cloud action. No fixed provider allowances or always-free operation are guaranteed by this plan. The project works without a custom domain, cloud credentials or an LLM API.

## External acceptance boundaries

Current BigQuery parity, original public Kaggle notebook recovery and calibrated-model promotion remain separate gates. Exact production Vercel SHA/HTTPS passed on 19 October for `2c54bb3`; later releases require their own checks. Local tests alone cannot close external gates. Keep the 10 September 2026 published snapshot and its provenance until an authorized, independently reconciled refresh exists. No automatic release monitor is re-enabled by this development work.

See [release status](RELEASE_STATUS.md), [architecture](architecture.md), [brand provenance](BRAND_IDENTITY.md) and [canonical research](research/KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md).
