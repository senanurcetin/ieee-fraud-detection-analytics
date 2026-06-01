# Production Validation Gate

This document records the release checks required before the public web dashboard is used in a portfolio or executive presentation.

## Live Reporting Contract

| Gate | Expected result | Current status |
|---|---|---|
| API backend | Live BigQuery reporting backend | PASS |
| Reporting dataset | `fraud_project_reporting` | PASS |
| Reporting API groups | Reporting groups plus niche drilldown group | PASS |
| Transaction population | 590,540 transactions | PASS |
| Fraud population | 20,663 labeled fraud transactions | PASS |
| Readiness gate | 6 of 6 checks pass | PASS |

## dbt Release Controls

Local development validation:

```bash
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
```

Latest development result:

```text
PASS=132 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=133
```

Production validation:

```bash
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
```

Latest production result:

```text
PASS=132 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=133
```

Production datasets rebuilt by dbt:

| Dataset | Role | Status |
|---|---|---|
| `fraud_project_staging` | Typed source views | PASS |
| `fraud_project_intermediate` | Joined and engineered feature layer | PASS |
| `fraud_project_mart` | Analytical marts and model support tables | PASS |
| `fraud_project_reporting` | Web-dashboard reporting layer | PASS |

Credential files are never stored in the repository. Use `GOOGLE_APPLICATION_CREDENTIALS` or an equivalent secret manager entry in the deployment environment.

## Release Rule

The dashboard can be presented only when all of the following are true:

1. The public API returns the expected reporting dataset, reporting groups, and niche drilldown group.
2. The reporting population reconciles to 590,540 transactions and 20,663 fraud labels.
3. Readiness checks return 6/6 PASS.
4. The local dbt build passes before commit.
5. Production dbt build is rerun after any material SQL model change.
6. The public dashboard contains no legacy presentation-layer references and no non-English public UI copy.
