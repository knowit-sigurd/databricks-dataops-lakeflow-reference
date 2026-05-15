# Setup

First-time configuration for the data engineering team.

**Prerequisite:** a workspace admin must have completed
[docs/platform-prerequisites.md](platform-prerequisites.md) before starting these steps.
The platform team provisions the service principal, Unity Catalog resources, and SQL
warehouse access. The steps below require only GitHub repository admin access and a
Mac with Docker Desktop.

## 1. Configure GitHub secrets

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Value |
|---|---|
| `DATABRICKS_HOST` | Workspace URL, e.g. `https://dbc-xxxxxxxx-xxxx.cloud.databricks.com` |
| `DATABRICKS_CLIENT_ID` | SP Client ID — obtain from platform team |
| `DATABRICKS_CLIENT_SECRET` | SP OAuth secret — obtain from platform team |
| `DATABRICKS_WAREHOUSE_ID` | Warehouse ID — obtain from platform team (e.g. `0bd7cc78c0abd6d9`) |

## 2. Configure the GitHub production environment

`Settings → Environments → New environment`

1. Name it exactly `production`.
2. Under `Required reviewers`, add at least one reviewer.
3. Save.

This is the approval gate that blocks `deploy-prod` until a human approves each production release.

## 3. Configure branch protection

`Settings → Branches → Add branch ruleset` targeting `main`.

| Rule | Setting |
|---|---|
| Require a pull request before merging | Enabled |
| Require status checks to pass | `CI / ci` and `Deploy SDP Pipelines / deploy-pr` |
| Require branches to be up to date before merging | Enabled |
| Do not allow bypassing the above settings | Enabled |

The two required checks will not appear in the status check search until they have run at
least once. Open a test PR first, let both checks complete, then add them as required.

## 4. Configure local development

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

## 5. Upload fixture data and run a first deploy

```bash
# Inside the devcontainer
make upload
make deploy
```

Run `make help` to see all available targets.

Then open a PR to trigger the full CI + deploy-pr pipeline. Both the `CI / ci` and
`Deploy SDP Pipelines / deploy-pr` checks must pass before you can add them as required
status checks in branch protection (step 3).
