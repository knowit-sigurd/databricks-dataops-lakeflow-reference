# Platform Prerequisites

What a workspace admin or platform team must provision before the data engineering
team can onboard. Requires Databricks workspace admin access. Done once per workspace
— not per repo or per engineer.

## 1. Create a service principal

In the Databricks workspace admin console (`Settings → Identity and Access → Service principals`):

1. Create a new service principal. Suggested name: `dataops-lab-sp`.
2. Generate an OAuth secret (`Generate secret`). Save the Client ID and Client Secret — the secret is shown once.
3. Add the SP as a workspace user.

## 2. Configure Unity Catalog

`sdp_dev` and `sdp_prod` schemas are declared as DAB-managed resources in the `platform`
target of `databricks.yml` with `lifecycle.prevent_destroy: true`. After the catalog and
schemas are created below, run `databricks bundle deploy -t platform` once to bring them
under bundle management. This protects both schemas from accidental destruction — even a
manual `bundle destroy -t platform` will fail safely. The catalog and volumes must still
be created manually; DAB does not manage them.

Run the following SQL in a SQL warehouse. Replace `<sp-application-id>` with the SP's Client ID from step 1.

```sql
-- Catalog and schemas
CREATE CATALOG IF NOT EXISTS dataops_lab;
CREATE SCHEMA IF NOT EXISTS dataops_lab.sdp_dev;
CREATE SCHEMA IF NOT EXISTS dataops_lab.sdp_prod;

-- Volumes for fixture data
CREATE VOLUME IF NOT EXISTS dataops_lab.sdp_dev.raw;
CREATE VOLUME IF NOT EXISTS dataops_lab.sdp_prod.raw;

-- Service principal privileges
GRANT USE CATALOG ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT USE SCHEMA ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT SELECT ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT CREATE SCHEMA ON CATALOG dataops_lab TO `<sp-application-id>`;
```

If your workspace has a `data-engineers` group provisioned, grant read access:

```sql
GRANT USE CATALOG ON CATALOG dataops_lab TO `data-engineers`;
GRANT USE SCHEMA ON CATALOG dataops_lab TO `data-engineers`;
GRANT SELECT ON CATALOG dataops_lab TO `data-engineers`;
```

Granting at catalog level propagates to all current and future schemas, including
dynamically created PR schemas (`sdp_pr_<n>`). Without catalog-level grants, each
new PR schema requires a separate grant — not practical at scale.

## 3. Grant SQL warehouse access

The SP needs `CAN USE` on the SQL warehouse used for row count assertions:

`SQL Warehouses → <warehouse> → Permissions → Add → <sp-application-id> → CAN USE`

Note the warehouse ID from the URL (e.g. `0bd7cc78c0abd6d9`) and share it with the
data engineering team — they need it for a GitHub secret.

## Authentication model

### Current: OAuth client secret

CI authenticates via `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` stored as
GitHub secrets. This works but requires manual rotation when the secret expires.

### Production recommendation: OIDC workload identity federation

GitHub Actions can prove its identity via a short-lived cryptographic token instead of
a stored secret. Databricks issues a scoped access token in exchange — nothing to rotate,
no long-lived credential in GitHub. Configuring this requires Databricks **account admin**
access (`accounts.cloud.databricks.com`) to set a federation policy on the service
principal. In a client deployment with a dedicated platform team, OIDC federation should
be the default credential model for all CI/CD integrations.

Not implemented in this reference workspace — account admin access is not available.
