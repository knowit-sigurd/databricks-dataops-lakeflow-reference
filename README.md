# Databricks DataOps Reference Architecture

A reference implementation of Databricks-native DataOps using Lakeflow / Spark Declarative
Pipelines (SDP) and Declarative Automation Bundles (DAB). Demonstrates a Git-driven pipeline
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
as Declarative Automation Bundles. Promotion is controlled entirely through Git.

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

Each PR gets a fully isolated environment: pipeline name, UC schema, and source volume are all scoped to `sdp_pr_<n>`. Schema and volume are destroyed on PR close.

## Dev container

The development environment is based on the [databricks-dev-container](https://github.com/Knowit-Objectnet/databricks-dev-container) — a community devcontainer for Databricks development. Contributions that improve the experience are welcome.

## Local development workflow

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

| Trigger          | Workflow       | What happens                                                                                      |
|------------------|----------------|---------------------------------------------------------------------------------------------------|
| Pull request (code change) | CI + Deploy | Lint, test, deploy `pr_<n>` to `sdp_pr_<n>`, run pipeline, assert counts          |
| Pull request (docs-only)   | CI only     | Lint and tests run; deploy skipped — completes in ~7s                              |
| PR closed        | Cleanup        | Destroy pipeline, drop `sdp_pr_<n>` schema and managed volume (skipped for docs-only PRs)        |
| Push to main     | Deploy         | Approval gate → deploy `prod` target to `sdp_prod` (skipped for docs-only merges)                |
| Manual dispatch  | Deploy         | Deploy dev bundle only — pipeline not run, row counts not asserted                                |

Docs-only is defined as changes exclusively in `docs/`, `README.md`, or `.github/PULL_REQUEST_TEMPLATE.md`. For code PRs the deploy order is: bundle deploy (creates schema) → create managed volume → upload source data → run pipeline → assert counts.

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

## Scope

- **No staging environment.** A true staging target requires a separate workspace or UC catalog.
  Current promotion model: PR → `sdp_pr_<n>`, main → `sdp_prod`. No intermediate environment.
- **Static fixture data.** Source volumes are populated by CI upload scripts, not Auto Loader.
  Dev fixtures contain intentionally bad rows to demonstrate the rejection mechanism; prod
  fixtures are clean. In a production project the source volume would be populated by Auto Loader.
- **Production pipeline is operator-triggered.** `bundle deploy` deploys the pipeline definition
  but does not run it. Execution is triggered manually via `prod_medallion_operational_job` in
  the Databricks Workflows UI, or directly from the Pipelines UI for a full refresh. PR
  deployments do run the pipeline and assert row counts as part of the CI gate.
- **Observability queries require pipeline ownership.** `event_log()` queries in `sql/` work for
  the dev pipeline (owned by the local user). The prod pipeline is owned by the CI service
  principal. Cross-pipeline observability via `system.lakeflow` requires account admin access.

