# Development Backlog

This backlog tracks the remaining work for the live web analytics layer. The goal is to keep the dashboard credible for an executive banking fraud presentation while preserving a zero-cost, English-first, portfolio-ready delivery model.

## P0 - Presentation and Data Trust

1. Production smoke test
   - `/api/dashboard?refresh=true` must return all reporting groups and the niche drilldown group.
   - Total transactions must remain 590,540.
   - `rpt_report_readiness` must show 6/6 passing checks.

2. Responsive visual review
   - Validate desktop, tablet, and mobile viewports.
   - No clipped titles, overlapping controls, empty charts, or unreadable labels.
   - Slicers, segment comparison, drawer, threshold simulation, and export controls must work end to end.

3. Public portfolio evidence
   - Refresh dashboard screenshots after each major UI iteration.
   - README preview images should show Executive Overview, Segment Explorer, Model Operations, and Data Trust.

## P1 - Analytical Depth

1. Segment comparison mode
   - Compare two segments side by side on fraud rate, lift, fraud share, transaction share, average amount, and priority.
   - Generate a recommendation when one segment has materially higher risk concentration.

2. Dynamic threshold policy
   - Connect the threshold simulation to analyst capacity, false-positive review cost, and false-negative loss assumptions.
   - Surface the recommended threshold and estimated missed fraud exposure.

3. Explainability narrative
   - Extend feature importance with business-readable signal families.
   - Label masked Vesta features as observational signals rather than confirmed business definitions.

4. Fraud contribution waterfall
   - Show how product, identity, payment, email, and amount segments contribute to fraud concentration.
   - Keep the method transparent because segment shares can overlap.

## P2 - Operational Maturity

1. Alert simulation
   - Flag fraud drift, critical queue pressure, high missingness, and readiness failures.
   - Attach a recommended monitoring action to each alert.

2. Export story
   - Keep JSON export for auditability.
   - Use browser print styles for PDF-ready executive views.
   - Keep copy-ready summary text for meetings.

3. Monitoring runbook
   - Document Vercel, BigQuery, dbt, and credential checks.
   - Add a clear recovery path for API errors and stale data.

## P3 - Productization

1. Multi-dataset template
   - Make the dashboard structure reusable for additional fraud datasets.
   - Keep dataset selection environment-driven to avoid paid infrastructure.

2. Tenant-ready architecture note
   - Plan dataset isolation for future multi-tenant usage while staying within cost-controlled public deployment constraints.
   - Avoid assumptions about paid gateways or custom domains.

3. Payment-independent validation
   - Use waitlist, manual onboarding, and Merchant of Record compatible flows for future monetization.
   - Do not depend on Stripe availability.
