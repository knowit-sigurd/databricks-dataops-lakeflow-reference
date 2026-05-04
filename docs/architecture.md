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

| Target | Schema     | Source volume                     | quality_mode | Retries |
|--------|------------|-----------------------------------|--------------|---------|
| PR     | sdp_pr_<n> | /Volumes/dataops_lab/sdp_dev/raw  | drop         | default |
| dev    | sdp_dev    | /Volumes/dataops_lab/sdp_dev/raw  | drop         | default |
| prod   | sdp_prod   | /Volumes/dataops_lab/sdp_prod/raw | fail         | 0       |

PR-based deployments use `deployment_suffix=pr_<n>` and `target_schema=sdp_pr_<n>`,
giving each PR an isolated pipeline name and an isolated Unity Catalog schema.

All PR deployments share `/Volumes/dataops_lab/sdp_dev/raw` as the source volume.
This is deliberate: source data is static CSV fixtures that do not vary between PRs.
Input isolation is not needed; output isolation (schema-per-PR) prevents contention.

## Deployment model

Deployment is controlled through GitHub Actions and Databricks Asset Bundles.
Source data is uploaded to the target volume before bundle deployment.

```
PR opened
  → upload_data.sh dev
  → databricks bundle deploy -t dev --var=deployment_suffix=pr_<n> --var=target_schema=sdp_pr_<n>
  → creates pr_<n>_medallion_pipeline writing to dataops_lab.sdp_pr_<n>

PR closed (merged or abandoned)
  → databricks bundle destroy -t dev --var=deployment_suffix=pr_<n>
  → databricks schemas delete dataops_lab.sdp_pr_<n>
  → removes pipeline resource and UC schema

Merged to main
  → upload_data.sh prod
  → databricks bundle deploy -t prod --var=deployment_suffix=prod
  → updates prod_medallion_pipeline writing to dataops_lab.sdp_prod
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
- Source volume is shared across all PR deployments (`sdp_dev/raw`). This is intentional: source data is static CSV fixtures. Isolation is on the output side (schema-per-PR).
- `upload_data.sh prod` seeds fixture CSVs into `sdp_prod/raw` during prod deploy. This is a demo convenience. In a production project, this volume would be populated by Auto Loader or a separate data ingestion process — not by CI deployment scripts.
- Future: a staging target would require a separate workspace or UC catalog with its own schema namespace and credential scope. Out of scope for this reference lab.
- CI row count assertions use hard-coded expected values derived from static fixture CSVs. In production, replace these with percentage deviation thresholds (e.g. fail if row count changes >20% vs previous run). This requires state persistence for previous counts — typically a Delta table or a monitoring integration. Not applicable here because fixture data never changes between runs.

This repo currently uses the legacy dlt Python module, which remains supported in Lakeflow SDP.
Migration to pyspark.pipelines is tracked as future API modernization, not required for this milestone.

## Schema evolution

Schema changes are categorized by the risk they carry for downstream consumers.

| Change type         | Safe? | Policy                                                                          |
|---------------------|-------|---------------------------------------------------------------------------------|
| New nullable column | Yes   | Add to bronze `StructType`. Promote to silver/gold only by explicit code change. |
| Renamed column      | No    | Breaking change. Requires compatibility mapping or migration.                   |
| Dropped column      | No    | Breaking change. Requires downstream impact analysis before removal.            |
| Type change         | No    | Breaking change. Requires explicit casting or validation.                       |

### Promotion gates

Bronze `StructType` is the contract between source and pipeline. Any column not declared
there is silently dropped at ingest — it never reaches silver or gold.

Silver inherits all columns from bronze unless a transformation explicitly removes them.
`enrich_customers` uses `withColumn`, not `select`, so new bronze columns flow through
to `customers_silver` automatically once declared in the schema.

Gold uses an explicit `.select()`. This is the deliberate promotion gate: a column in
silver only reaches `customer_order_summary` if it is named there. `customer_email` is
available in `customers_silver` for operational consumers but is not a business output
metric, so it is not promoted to gold.

### Future production hardening

Handling unexpected columns at ingest (schema drift guard), Auto Loader schema evolution
mode, and schema registry integration are production patterns not implemented in this
reference. They are appropriate when source schemas are truly unknown or when multiple
upstream teams write to the same volumes.