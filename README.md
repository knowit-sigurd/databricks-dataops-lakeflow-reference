# databricks-dataops-lab-sdp

A Databricks-native DataOps project using Lakeflow / Spark Declarative Pipelines (SDP)
and Databricks Asset Bundles (DAB) to explore Git-driven pipeline promotion.

## Project structure

```
pipelines/          # DLT pipeline definitions
tests/              # Smoke tests (pytest)
scripts/            # Local dev utilities
.github/workflows/  # CI and deploy pipelines
databricks.yml      # Bundle config (targets: dev, test, prod)
```

## How it works

Pipelines are defined declaratively in Python using the `dlt` library and deployed
as Databricks Asset Bundles. Promotion is controlled entirely through Git.

```
PR opened   →  deploys pr_<number>_* pipelines to dev  (quality_mode: drop)
Merged to main  →  deploys prod_* pipelines to prod    (quality_mode: fail)
```

Schemas are also environment-scoped:

| Target | Schema   | On bad rows                        |
|--------|----------|------------------------------------|
| dev/PR | sdp_dev  | Drop row                           |
| prod   | sdp_prod | Fail pipeline (no retries)         |


## Local development workflow

Development is performed inside the VS Code devcontainer.

Recommended local checks before creating a PR:

```bash
uv run ruff check .
uv run pytest
databricks bundle validate -t dev
databricks bundle plan -t dev

## CI/CD

| Trigger          | Workflow       | What happens                         |
|------------------|----------------|--------------------------------------|
| Pull request     | CI + Deploy    | Lint, test, deploy `pr_<n>` to dev   |
| Push to main     | Deploy         | Deploy `prod` target to production   |
| Manual dispatch  | Deploy         | Deploy to chosen target (dev/test)   |

Databricks credentials are stored as GitHub secrets:
`DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`.

## Pipelines

| Pipeline          | Bronze table     | Silver table     | Quality check       |
|-------------------|------------------|------------------|---------------------|
| customer_pipeline | customers_bronze | customers_silver | non-null id + name  |
| orders_pipeline   | orders_bronze    | orders_silver    | non-null amount     |

## Cleanup

PR-scoped pipelines (`pr_<n>_*`) are not automatically removed after merge.
Manual cleanup in the Databricks workspace is currently required.
