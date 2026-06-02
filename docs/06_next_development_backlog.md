# Next Development Backlog

This document defines the next technical iteration after making the live web dashboard the primary reporting and presentation layer.

## Completed Baseline

1. Static presentation dependencies were removed from the active reporting path.
2. The FastAPI dashboard API was expanded to cover 18 BigQuery reporting tables.
3. The web dashboard includes:
   - Global filters for metric, segment family, and operational priority.
   - Segment comparison panel.
   - Drill-through drawer with copy-ready insight text.
   - Pareto and fraud contribution waterfall charts.
   - Identity and product coverage matrix.
   - Relative hour and amount-decimal heatmap.
   - Payment and email risk cuts.
   - Threshold what-if simulation.
   - Capacity and cost operating assumptions.
   - Feature importance and feature-family treemap.
   - Drift indicators, data quality contract, and readiness gate.
4. The public dashboard language is English-first.

## Next Improvements

1. Production verification
   - Validate the production API contract and dashboard UI after each deployment.
   - Confirm that the production environment reads `fraud_project_reporting`.

2. Deeper segment drill-down
   - Add mini-trends for selected segments where reporting data is available.
   - Add comparable peer segments for the selected risk driver.

3. Meeting-ready export
   - Improve print CSS after screenshot review.
   - Add one-page executive brief generation from the active filters.

4. Model explainability
   - Add feature family commentary and documented treatment of masked Vesta features.
   - Add a precision-recall focused explanation for imbalanced fraud data.

5. Operational threshold simulation
   - Expand the cost model with analyst hourly cost, SLA target, and queue backlog.
   - Add sensitivity bands for conservative, balanced, and aggressive review policies.

## Acceptance Criteria

- Production dashboard returns live data.
- No visible public UI contains non-English labels.
- No chart is blank under the default filter context.
- Every interactive control changes the visible analysis or export state.
- Dashboard screenshots in the README reflect the current web UI.
- The web dashboard remains the only active presentation layer.
