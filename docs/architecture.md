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

Pipelines are defined declaratively in Python using the `dlt` library.
Each pipeline follows a two-layer pattern:

```
Raw data (inline / source)
    ↓  @dlt.table
Bronze table  (customers_bronze / orders_bronze)
    ↓  @dlt.table + @dlt.expect_or_*
Silver table  (customers_silver / orders_silver)
```

Execution order is derived from `dlt.read()` dependencies, not from explicit job sequencing.
Each pipeline is independent and manages its own DAG internally.

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
Schema and quality behavior are scoped per target.

| Target | Schema   | quality_mode | Retries |
|--------|----------|--------------|---------|
| dev    | sdp_dev  | drop         | default |
| test   | sdp_dev  | drop         | default |
| prod   | sdp_prod | fail         | 0       |

PR-based deployments use `deployment_suffix=pr_<n>` and write to `sdp_dev`,
giving each PR isolated pipeline names without schema isolation.

## Deployment model

Deployment is controlled through GitHub Actions and Databricks Asset Bundles.

```
PR opened
  → GitHub Actions resolves target=dev, deployment_suffix=pr_<n>
  → databricks bundle deploy -t dev --var=deployment_suffix=pr_<n>
  → creates pr_<n>_customer_pipeline and pr_<n>_orders_pipeline

Merged to main
  → GitHub Actions resolves target=prod, deployment_suffix=prod
  → databricks bundle deploy -t prod --var=deployment_suffix=prod
  → updates prod_customer_pipeline and prod_orders_pipeline
```

Dynamic naming logic (suffix, schema) is resolved in GitHub Actions and passed into DAB.
`databricks.yml` stays static — no string manipulation inside bundle configuration.

## Development workflow

```
Local dev (VS Code + devcontainer)
  ↓  uv run ruff check / pytest
CI (GitHub Actions)
  ↓  lint + smoke tests pass
Deploy (databricks bundle deploy)
  ↓
Databricks pipeline execution (serverless)
```

Local Spark (via devcontainer) is used for fast iteration and testing transformation logic.
Full SDP pipeline execution requires Databricks — local runs cannot replicate expectations behavior.

## Known limitations

- PR-scoped pipelines are not automatically removed after merge — manual cleanup required.
- Rejected rows are not persisted by default; SDP provides aggregated metrics only.
- `databricks.yml` variable substitution does not support string manipulation — naming logic must live in CI/CD.
