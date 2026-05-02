# databricks-dataops-lab-sdp

A Databricks-native DataOps project using Lakeflow / Spark Declarative Pipelines (SDP)
and Databricks Asset Bundles (DAB) to explore Git-driven pipeline promotion.

## Project structure

```
pipelines/          # DLT pipeline definitions (customer, orders, gold)
tests/              # Smoke tests (pytest)
scripts/            # Local dev utilities (upload_data.sh)
.github/workflows/  # CI and deploy pipelines
databricks.yml      # Bundle config (targets: dev, test, prod)
```

## How it works

Pipelines are defined declaratively in Python using the `dlt` library and deployed
as Databricks Asset Bundles. Promotion is controlled entirely through Git.

```
PR opened       →  deploys pr_<number>_medallion_pipeline to dev  (quality_mode: drop)
Merged to main  →  deploys prod_medallion_pipeline to prod        (quality_mode: fail)
```

Schemas are also environment-scoped:

| Target | Schema   | Source volume                      | On bad rows                |
|--------|----------|------------------------------------|----------------------------|
| dev/PR | sdp_dev  | /Volumes/dataops_lab/sdp_dev/raw   | Drop row                   |
| prod   | sdp_prod | /Volumes/dataops_lab/sdp_prod/raw  | Fail pipeline (no retries) |


## Local development workflow

Development is performed inside the VS Code devcontainer.

Recommended local checks before creating a PR:

```bash
uv run ruff check .
uv run pytest
databricks bundle validate -t dev
databricks bundle plan -t dev
```

To upload source data to the dev volume:

```bash
scripts/upload_data.sh dev
```

## CI/CD

| Trigger          | Workflow       | What happens                                  |
|------------------|----------------|-----------------------------------------------|
| Pull request     | CI + Deploy    | Lint, test, deploy `pr_<n>` to dev            |
| PR closed        | Cleanup        | Destroy `pr_<n>_medallion_pipeline` from dev  |
| Push to main     | Deploy         | Deploy `prod` target to production            |
| Manual dispatch  | Deploy         | Deploy to chosen target (dev/test)            |

The deploy workflow uploads source data to the target volume before running `bundle deploy`.

Databricks credentials are stored as GitHub secrets:
`DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`.

## Pipeline

All tables are managed by a single `medallion_pipeline` resource with one DAG:

```
customers_bronze → customers_silver ↘
                                      → customer_order_summary
orders_bronze    → orders_silver    ↗
```

| Layer  | Table                  | Description                        |
|--------|------------------------|------------------------------------|
| Bronze | customers_bronze       | Raw customer data                  |
| Bronze | orders_bronze          | Raw orders data                    |
| Silver | customers_silver       | Validated, enriched customers      |
| Silver | customers_rejected     | Rejected customer rows with reason |
| Silver | orders_silver          | Validated, enriched orders         |
| Silver | orders_rejected        | Rejected order rows with reason    |
| Gold   | customer_order_summary | Customer order aggregation         |

## Deployment

This reference repo uses `--auto-approve` during bundle deployment to keep PR and demo
resources synchronized with the bundle definition.

In client production environments, destructive bundle changes should be reviewed through
`databricks bundle plan`, PR review, and environment protection before deployment.

## Cleanup

When a PR is closed (merged or abandoned), the `cleanup-pr.yml` workflow automatically runs
`databricks bundle destroy` against the `dev` target with the matching `deployment_suffix`.
This removes the `pr_<n>_medallion_pipeline` from the Databricks workspace without requiring
manual intervention.


## Final milestone status

Repo now have:

✔ SDP pipelines
✔ Local dev
✔ CI
✔ CD
✔ PR-based pipelines
✔ Prod pipeline
✔ Data ingestion
✔ Gold layer
✔ Rejected rows
✔ Automatic cleanup