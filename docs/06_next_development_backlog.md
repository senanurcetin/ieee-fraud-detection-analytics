# Next Development Backlog

This document defines the next iteration after the BI-style web report release.

## Completed Baseline

1. The active presentation layer is the Vercel-hosted web dashboard.
2. Static report artifacts and legacy presentation paths are outside the production story.
3. The FastAPI API serves governed reporting tables from `fraud_project_reporting`.
4. The web dashboard includes:
   - Executive Fraud Overview.
   - Fraud Trend Analysis.
   - Transaction Amount Analysis.
   - Customer Risk Analysis.
   - Masked Address & Distance Analysis.
   - Behavioral Pattern Analysis.
   - Feature Importance Analysis.
   - Model Performance Analysis.
   - Key Insights & Recommendations.
5. Every page supports:
   - Primary Analysis.
   - Supporting Visuals.
   - Chart-level drill-through.
   - Segment-level drill-through where a visual mark represents a comparable segment.
6. The public dashboard language is English-first.

## Next Improvements

1. Screenshot refresh
   - Regenerate the public README screenshot assets from the production dashboard after each design milestone.
   - Keep screenshots aligned with the current page names and visual story.

2. Presentation polish
   - Continue reducing main-layer visual density when a page feels report-heavy.
   - Keep diagnostic charts available in Supporting Visuals for Q&A.
   - Validate that heatmaps, mixed line/bar charts, and long labels do not overlap at desktop widths.

3. Drill-through depth
   - Add more nested peer groups where reporting tables already support comparable cuts.
   - Avoid comparing unrelated segment families in the same drill-through view.

4. Model explanation
   - Add optional calibration evidence to the existing model registry if governed probability scoring becomes in scope.
   - Keep feature importance and feature contribution artifacts visible in documentation.

5. External enrichment
   - Add country, IP, merchant-location, or user-age analysis only if real enrichment fields are provided.
   - Keep IEEE-CIS native address and distance fields framed as masked proxy signals.

## Acceptance Criteria

- Production dashboard returns live data from `fraud_project_reporting`.
- No visible public UI contains non-English labels.
- No visible public UI contains legacy presentation-tool references.
- No primary chart is blank under the default filter context.
- Heatmap and mixed line/bar visual labels remain readable.
- Every interactive control changes the visible analysis or export state.
- README and docs describe the web dashboard as the only active presentation layer.
