# Architecture

A Databricks-native DataOps project using Spark Declarative Pipelines (SDP)
and Databricks Asset Bundles (DAB) for Git-driven pipeline promotion.

## Approach

This project uses platform-native capabilities instead of a custom DataOps framework.

| Concern        | Custom framework (v2)  | This project (SDP)          |
|----------------|------------------------|-----------------------------|
| Orchestration  | Custom `run_pipeline`  | Databricks pipeline engine  |
| Validation     | Imperative Python code | `@dlt.expect_or_*`          |
| Observability  | SQL audit table        | Pipeline UI + lineage       |
| Execution      | Notebook / wheel job   | Serverless compute          |
| Deployment     | DAB + GitHub Actions   | DAB + GitHub Actions        |

## Pipeline model

All tables are managed by a single `medallion_pipeline` resource. The three pipeline
files (`customer_pipeline.py`, `orders_pipeline.py`, `gold_pipeline.py`) are included
in the same bundle pipeline so that `dlt.read()` can resolve cross-file dependencies
and Databricks builds one unified DAG.

```
customers_bronze → customers_silver ↘
                                      → customer_order_summary
orders_bronze    → orders_silver    ↗
```

Rejected rows are captured as separate silver-layer tables:

```
customers_bronze → customers_rejected
orders_bronze    → orders_rejected
```

Execution order is derived from `dlt.read()` dependencies, not from explicit job sequencing.

## Code structure

Each pipeline file has a corresponding logic module in `pipelines/`:

| Pipeline entrypoint       | Logic module       | Responsibility                    |
|---------------------------|--------------------|-----------------------------------|
| customer_pipeline.py      | customers.py       | Standardize, validate, enrich     |
| orders_pipeline.py        | orders.py          | Validate, enrich                  |
| gold_pipeline.py          | gold.py            | Join and aggregate                |
| —                         | common.py          | Shared utilities (e.g. derive_region) |

DLT uploads library files as a flat collection, so modules use bare imports
(`from common import ...`) rather than package-qualified imports.

## Data quality

Validation behavior is controlled by the `quality_mode` configuration variable,
which is read at runtime via `spark.conf.get("quality_mode", "drop")`.

| Environment | quality_mode | On invalid row       |
|-------------|--------------|----------------------|
| dev / PR    | drop         | Row silently dropped |
| prod        | fail         | Pipeline fails       |

Production also disables automatic retries to ensure a clear failure signal:

```yaml
pipelines.maxFlowRetryAttempts: "0"
pipelines.numUpdateRetryAttempts: "0"
```

## Environment model

Environments are defined as targets in `databricks.yml`.
Schema, source volume, and quality behavior are scoped per target.

| Target | Schema   | Source volume                     | quality_mode | Retries |
|--------|----------|-----------------------------------|--------------|---------|
| dev    | sdp_dev  | /Volumes/dataops_lab/sdp_dev/raw  | drop         | default |
| test   | sdp_dev  | /Volumes/dataops_lab/sdp_dev/raw  | drop         | default |
| prod   | sdp_prod | /Volumes/dataops_lab/sdp_prod/raw | fail         | 0       |

PR-based deployments use `deployment_suffix=pr_<n>` and write to `sdp_dev`,
giving each PR isolated pipeline names without schema isolation.

## Deployment model

Deployment is controlled through GitHub Actions and Databricks Asset Bundles.
Source data is uploaded to the target volume before bundle deployment.

```
PR opened
  → upload_data.sh dev
  → databricks bundle deploy -t dev --var=deployment_suffix=pr_<n>
  → creates pr_<n>_medallion_pipeline

PR closed (merged or abandoned)
  → databricks bundle destroy -t dev --var=deployment_suffix=pr_<n>
  → removes pr_<n>_medallion_pipeline from workspace

Merged to main
  → upload_data.sh prod
  → databricks bundle deploy -t prod --var=deployment_suffix=prod
  → updates prod_medallion_pipeline
```

Dynamic naming logic (suffix, schema) is resolved in GitHub Actions and passed into DAB.
`databricks.yml` stays static — no string manipulation inside bundle configuration.

## Deployment approval policy

This reference repo uses `--auto-approve` during bundle deployment to keep PR and demo
resources synchronized with the bundle definition.

In client production environments, destructive bundle changes should be reviewed through
`databricks bundle plan`, PR review, and environment protection before deployment.

## Development workflow

```
Local dev (VS Code + devcontainer)
  ↓  uv run ruff check / pytest
CI (GitHub Actions)
  ↓  lint + smoke tests pass
Deploy (upload_data.sh + databricks bundle deploy)
  ↓
Databricks pipeline execution (serverless)
```

Local Spark (via devcontainer) is used for fast iteration and testing transformation logic.
Full SDP pipeline execution requires Databricks — local runs cannot replicate expectations behavior.

## Known limitations

- `databricks.yml` variable substitution does not support string manipulation — naming logic must live in CI/CD.
