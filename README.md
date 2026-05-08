# databricks-dataops-lakeflow-reference

A reference architecture for Databricks-native DataOps using Lakeflow / Spark Declarative
Pipelines (SDP) and Databricks Asset Bundles (DAB). Demonstrates Git-driven pipeline
promotion, schema-per-PR isolation, data quality enforcement, and a production approval gate
— all using platform-native capabilities without a custom framework.

For a deeper look at the design decisions, environment model, data quality strategy, and deployment approval policy, see [docs/architecture.md](docs/architecture.md).

To demonstrate the repo to a client, see [docs/demo-guide.md](docs/demo-guide.md) (30-minute technical walkthrough for a data engineering lead) or [docs/demo-guide-exec.md](docs/demo-guide-exec.md) (10-minute executive overview).

For first-time workspace setup, see [docs/setup.md](docs/setup.md). For operational procedures (prod trigger, full refresh, cleanup recovery), see [docs/runbook.md](docs/runbook.md).

## Project structure

```
pipelines/          # SDP pipeline definitions (customer, orders, gold) + logic modules
tests/              # Transformation unit tests (pytest)
scripts/            # Utilities (upload_data.sh, stop_pipeline.py, validate_counts.py, cleanup_orphaned_pipeline.py)
fixtures/           # Expected row counts for CI assertions (expected_counts.json)
sql/                # Observability queries (event log, rejection tables)
data/               # Dev fixture CSVs (intentionally bad rows for rejection demo)
data/prod/          # Prod fixture CSVs (clean — all rows pass validation)
docs/               # Architecture, learning log, demo guides
.github/workflows/  # CI and deploy workflows (ci.yml, deploy.yml, cleanup-pr.yml)
.github/            # Dependabot config (weekly pip + actions updates) + PR template
databricks.yml      # Bundle config (targets: dev, prod)
```

## How it works

Pipelines are defined declaratively in Python using the `pyspark.pipelines` API and deployed
as Databricks Asset Bundles. Promotion is controlled entirely through Git.

```
PR opened       →  deploys pr_<n>_medallion_pipeline to sdp_pr_<n>  (quality_mode: drop)
Merged to main  →  deploys prod_medallion_pipeline to sdp_prod       (quality_mode: fail)
```

Schemas are also environment-scoped:

| Target     | Schema     | Source volume                      | On bad rows                |
|------------|------------|------------------------------------|----------------------------|
| PR         | sdp_pr_<n> | /Volumes/dataops_lab/sdp_pr_<n>/raw | Drop row                   |
| dev        | sdp_dev    | /Volumes/dataops_lab/sdp_dev/raw   | Drop row                   |
| prod       | sdp_prod   | /Volumes/dataops_lab/sdp_prod/raw  | Fail pipeline (no retries) |

Each PR gets a fully isolated environment: pipeline name, UC schema, and source volume are all scoped to `sdp_pr_<n>`. Schema and volume are destroyed on PR close. Verified by concurrent live execution of two PRs (M22).

## Dev container

The development environment is based on the [databricks-dev-container](https://github.com/Knowit-Objectnet/databricks-dev-container) — a community devcontainer for Databricks development. Contributions that improve the experience are welcome.

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

| Trigger          | Workflow       | What happens                                                             |
|------------------|----------------|--------------------------------------------------------------------------|
| Pull request     | CI + Deploy    | Lint, test, deploy `pr_<n>` to `sdp_pr_<n>`, run pipeline, assert counts |
| PR closed        | Cleanup        | Destroy pipeline, drop `sdp_pr_<n>` schema and managed volume            |
| Push to main     | Deploy         | Approval gate → deploy `prod` target to `sdp_prod`                       |
| Manual dispatch  | Deploy         | Deploy dev bundle only — pipeline not run, row counts not asserted       |

For PR deployments the workflow order is: bundle deploy (creates schema) → create managed volume → upload source data → run pipeline → assert counts.

Databricks credentials are stored as GitHub secrets:
`DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`, `DATABRICKS_WAREHOUSE_ID`.

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

PR deployments use `--auto-approve` to keep temporary resources synchronized without
manual intervention.

Production deployments require manual approval through the GitHub `production` environment.
A push to `main` triggers the `deploy-prod` job, which pauses and sends a notification
to required reviewers before proceeding. This creates an auditable approval record for
every production release.

## Cleanup

When a PR is closed (merged or abandoned), the `cleanup-pr.yml` workflow automatically:
1. Runs `databricks bundle destroy` to remove `pr_<n>_medallion_pipeline` from the workspace
2. Drops the `dataops_lab.sdp_pr_<n>` Unity Catalog schema and all its tables

## Known limitations

- No staging environment. A true staging target requires a separate workspace or UC catalog.
  Current model: PR → `sdp_pr_<n>`, main → `sdp_prod`. No intermediate environment.
- Dev and prod use separate fixture data. Dev fixtures contain intentionally bad rows to
  demonstrate the rejection mechanism. Prod fixtures are clean so the pipeline completes.
  In a production project the source volume would be populated by Auto Loader, not CI scripts.
- Production deployment runs `bundle deploy` only — it does not trigger the pipeline or assert
  row counts. PR deployments do validate execution (pipeline run + row count assertions).
  Prod pipeline execution is operator-triggered via `prod_medallion_operational_job` in the
  Databricks Workflows UI, or directly from the Pipelines UI for full refresh.
  If prod was previously run against an empty volume, a subsequent incremental run will not
  reprocess gold — DLT's streaming state considers it up to date. Use Full refresh to force
  recomputation after data is loaded for the first time.
- `event_log()` queries in `sql/` target the dev pipeline (owned by the local user). The prod
  pipeline is owned by the CI service principal — `event_log()` requires pipeline ownership,
  not just `CAN_VIEW`. `system.lakeflow` provides cross-pipeline observability but requires
  account admin to grant `USE SCHEMA` access.