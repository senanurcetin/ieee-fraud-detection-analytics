# Archived Power BI Prototype Guide

This document is retained for historical context only. The project no longer uses Power BI as the primary presentation layer.

## Current Reporting Standard

The main reporting deliverable is the live web dashboard:

```text
https://fraud-project-web.vercel.app
```

The dashboard reads dbt-built BigQuery reporting tables through the FastAPI API in `webapp/` and provides the executive analytics experience used for the final presentation.

## Archived Asset

```text
powerbi/fraud_project_v2.pbix
```

The PBIX file is kept as an archived BI prototype. It is not required for the live presentation and should not be treated as the source of truth for analysis.

## Why It Was Replaced

- The web dashboard is easier to publish and share publicly.
- The analytics interface can include custom visuals that are difficult to maintain in a PBIX package.
- BigQuery access is controlled server-side through Vercel environment variables.
- The presentation can be opened from a browser without local desktop dependencies.

## Active Documentation

Use the live dashboard guide for the current reporting layer:

```text
docs/live_web_dashboard_guide.md
```
