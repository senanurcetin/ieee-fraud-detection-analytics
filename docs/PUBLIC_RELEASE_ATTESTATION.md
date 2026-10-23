# F08 — Public production release attestation

A Vercel `READY` deployment and green **local** cross-browser/Docker CI
cannot, alone, establish that the active production alias returns valid
historical dashboard content for the intended release commit.

The repository now includes an explicitly **read-only public probe**:
`python -m scripts.verify_public_release --expected-sha <full-40-char-main-sha>`.

It checks exactly `https://fraud-project-web.vercel.app` (not a user-supplied
URL). The verifier never follows redirects (including SSO redirects), sends
no tokens or cookies, makes no paid SQL calls, and limits response bytes.

## Evidence required for PASS_PUBLIC_HISTORICAL_RELEASE

1. `/api/evidence-status` advertises a valid 40-character
   `deployed_git_commit` matching the intended commit **exactly**.
   The runtime sources this value exclusively from
   Vercel's `VERCEL_GIT_COMMIT_SHA` system metadata if provided.
   If that metadata is disabled/unavailable the check **fails**. Do not
   insert fake `VERCEL_GIT_COMMIT_SHA` values or set it to a different
   revision to bypass the check.
2. `/api/dashboard` matches the **committed historical** 27-group
   snapshot, `590540` transactions, `20663` observed fraud labels,
   original source timestamp, and the legacy `source_parity` field describing the absence of a per-request live cloud check. A separate `historical_reconciliation` object exposes the dated 27-group audit when its snapshot/query bindings validate.
3. `/` and `/studio` both return HTTP 200 and contain the required
   historic-trust / Decision Studio elements and navigation links.
4. The report explicitly states that live BigQuery parity, real payment
   processing, and model probability calibration are **not** verified.

A failure to retrieve the public endpoints, an SSO 302/401/403 response, a
mismatched or absent build SHA, incomplete dashboard groups, a missing
Studio source rail or a future/fictional data timestamp blocks acceptance.
No login bypass or SSO policy change is made.

## Continuous acceptance

The separate `.github/workflows/public-release-smoke.yml` job runs on
relevant `main` source changes and can be manually retriggered by an
authorized reviewer. It waits a bounded period for Vercel Git-integrated
deployment propagation, then fails if the production alias cannot prove
the expected commit and historic source contract.

This may fail in environments where Vercel's Deployment Protection covers
the public `.vercel.app` alias. That is an **access-control finding**, not
permission to disable authentication or silently mark release PASS. For
protected deployments, use an explicitly approved, audited alternative
such as Vercel deployment checks with narrowly scoped protected-environment
authorization. Do not expose a bypass secret in public scripts or logs.

## Why keep the local tests?

The local CI suites serve independent purposes:

- `CI` — static code, Python regression, dbt parse and dependency audit.
- `Historical Container Smoke` — actual Docker build, Compose boot and
  localhost HTTP snapshot validation.
- Native Chromium CDP — desktop/mobile dashboard, Studio and research checks using `scripts/capture_browser_evidence_cdp.py`, without Playwright. The older `Historical Browser Acceptance` tri-engine workflow remains disabled; its records are historical.
- `Public Production Attestation` — live public alias, exact reviewed
  commit and strict historical disclosure. This does *not* validate
  private dashboards or full IEEE-CIS retraining.

A green production attestation is **not** a claim of current BigQuery
truth, cardholder identities, fraud model calibration, operational fraud
blocking or a live banking data stream. Issues #9 and #20 are closed for the separately documented [historical reconciliation and versioned calibration](research/COMPLETED_VALIDATION_2026-10-21.md); this HTTPS probe does not perform those studies. Original Kaggle source
recovery and completed public companion execution are documented in
[20 October publication evidence](research/KAGGLE_RECOVERY_2026-10-20.md).
