# Development Backlog

This backlog tracks the remaining non-blocking work after the web dashboard became the only active presentation layer.

## Completed in the Current Release

1. Production web report
   - Vercel production URL: `https://fraud-project-web.vercel.app`.
   - The public dashboard is English-first and web-only.
   - The report uses nine BI-style analytical pages.

2. Presentation structure
   - Every report page has a focused **Primary Analysis** layer.
   - Diagnostic charts are preserved under **Supporting Visuals** instead of crowding the main story.
   - Customer Risk Analysis now uses a full-width payment x email heatmap to avoid layout spillover.
   - Behavioral Pattern Analysis keeps relative-hour risk as the primary story and moves diagnostic scatter/heatmap views into supporting visuals.

3. Interaction model
   - Global slicers filter relative day, product, amount band, email group, identity status, and risk band.
   - Data marks open segment-level drill-through.
   - Visual cards open chart-level drill-through.
   - Same-family drill-through replaces row-heavy tables.
   - Threshold simulation recalculates capture, precision, workload, missed exposure, and net benefit proxy.

4. Data and governance
   - BigQuery `fraud_project_reporting` remains the production source of truth.
   - dbt build and reporting readiness checks are documented.
   - Credential files, raw CSV files, DuckDB files, and large temporary outputs remain out of Git.

## Remaining Non-Blocking Improvements

1. Screenshot refresh
   - Refresh README screenshots after each visual redesign.
   - Priority screenshots: Executive Overview, Customer Risk Analysis, Masked Address & Distance Analysis, Model Performance.

2. Optional visual refinement
   - Continue reducing visual density if presentation feedback shows a page is still overloaded.
   - Preserve hidden diagnostics under Supporting Visuals when they are useful for Q&A.

3. Data enrichment only when real fields exist
   - Do not add maps, country risk, user age, or IP-location visuals until a real enrichment source is available.
   - Continue labeling address and distance fields as masked proxy signals.

4. Long-term model monitoring
   - Add recurring drift automation only after a recurring data feed exists.
   - Extend the existing model registry with calibration tracking if the project evolves beyond portfolio scope.

## Current Completion Estimate

The project is estimated at **95% complete** for portfolio and classroom presentation use.

The remaining 5% is not a blocker for presentation. It is mostly screenshot refresh, optional visual polish, and future enrichment/monitoring work that requires data not present in IEEE-CIS.
