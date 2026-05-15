# Setup

Prerequisites and first-time configuration for running this repo in a new Databricks workspace.

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Workspace admin access (required for catalog, schema, and volume creation, and for SP grants)
- GitHub repository (fork or clone of this repo)
- Docker Desktop with the VS Code Dev Containers extension

## 1. Create a service principal

In the Databricks workspace admin console (`Settings → Identity and Access → Service principals`):

1. Create a new service principal. Suggested name: `dataops-lab-sp`.
2. Generate an OAuth secret (`Generate secret`). Save the Client ID and Client Secret — the secret is shown once.
3. Add the SP as a workspace user and assign it `CAN USE` access on at least one SQL warehouse (see step 2).

## 2. Configure Unity Catalog

Run the following SQL in a SQL warehouse. Replace `<sp-application-id>` with the SP's Client ID from step 1.

```sql
-- Catalog and schemas
CREATE CATALOG IF NOT EXISTS dataops_lab;
CREATE SCHEMA IF NOT EXISTS dataops_lab.sdp_dev;
CREATE SCHEMA IF NOT EXISTS dataops_lab.sdp_prod;

-- Volumes for fixture data
CREATE VOLUME IF NOT EXISTS dataops_lab.sdp_dev.raw;
CREATE VOLUME IF NOT EXISTS dataops_lab.sdp_prod.raw;

-- Service principal privileges (required for CI to deploy and assert row counts)
GRANT USE CATALOG ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT USE SCHEMA ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT SELECT ON CATALOG dataops_lab TO `<sp-application-id>`;
GRANT CREATE SCHEMA ON CATALOG dataops_lab TO `<sp-application-id>`;
```

Grant the SP `CAN USE` on the SQL warehouse used for row count assertions:
`SQL Warehouses → <warehouse> → Permissions → Add → <sp-application-id> → CAN USE`

Note the warehouse ID from the URL (e.g. `0bd7cc78c0abd6d9`) — you will need it for GitHub secrets.

If your workspace has a `data-engineers` group provisioned, grant read access:

```sql
GRANT USE CATALOG ON CATALOG dataops_lab TO `data-engineers`;
GRANT USE SCHEMA ON CATALOG dataops_lab TO `data-engineers`;
GRANT SELECT ON CATALOG dataops_lab TO `data-engineers`;
```

Granting at catalog level propagates to all current and future schemas, including dynamically
created PR schemas (`sdp_pr_<n>`). Without catalog-level grants, each new PR schema would
require a separate grant — which is not practical.

## 3. Configure GitHub secrets

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Value |
|---|---|
| `DATABRICKS_HOST` | Workspace URL, e.g. `https://dbc-xxxxxxxx-xxxx.cloud.databricks.com` |
| `DATABRICKS_CLIENT_ID` | SP Client ID from step 1 |
| `DATABRICKS_CLIENT_SECRET` | SP OAuth secret from step 1 |
| `DATABRICKS_WAREHOUSE_ID` | Warehouse ID from step 2 |

## 4. Configure the GitHub production environment

`Settings → Environments → New environment`

1. Name it exactly `production`.
2. Under `Required reviewers`, add at least one reviewer.
3. Save.

This is the approval gate that blocks `deploy-prod` until a human approves each production release.

## 5. Configure branch protection

`Settings → Branches → Add branch ruleset` targeting `main`.

| Rule | Setting |
|---|---|
| Require a pull request before merging | Enabled |
| Require status checks to pass | `CI / ci` and `Deploy SDP Pipelines / deploy-pr` |
| Require branches to be up to date before merging | Enabled |
| Do not allow bypassing the above settings | Enabled |

The two required checks will not appear in the status check search until they have run at
least once. Open a test PR first, let both checks complete, then add them as required.

## 6. Configure local development

**Clone and open the devcontainer:**

```bash
git clone <repo-url>
cd databricks-dataops-lakeflow-reference
code .
# VS Code prompt: "Reopen in Container"
```

**Update devcontainer.json before opening the container:**

Two values in `.devcontainer/devcontainer.json` are set to the original author's identity
and must be updated for your environment:

```json
"DATABRICKS_CONFIG_PROFILE": "your-email@domain.com",
"DATABRICKS_WAREHOUSE_ID": "<your-warehouse-id>"
```

The profile name must match a profile in `~/.databrickscfg` on your Mac (see next step).
The warehouse ID is the same one used for the GitHub secret.

**Configure Databricks CLI auth on your Mac:**

Create or update `~/.databrickscfg`:

```ini
[your-email@domain.com]
host  = https://dbc-xxxxxxxx-xxxx.cloud.databricks.com
```

Then authenticate interactively (run this on your Mac, not inside the container):

```bash
databricks auth login \
  --host https://dbc-xxxxxxxx-xxxx.cloud.databricks.com \
  --profile your-email@domain.com
```

The devcontainer mounts `~/.databrickscfg` read-only, so auth tokens are available inside
the container without any further steps.

**Verify the connection inside the container:**

```bash
databricks auth status
make validate
```

**Run local tests:**

```bash
make ci
```

## 7. Upload fixture data and run a first deploy

```bash
# Inside the devcontainer
make upload
make deploy
```

Run `make help` to see all available targets.

Then open a PR to trigger the full CI + deploy-pr pipeline. Both the `CI / ci` and
`Deploy SDP Pipelines / deploy-pr` checks must pass before you can add them as required
status checks in branch protection (step 5).
