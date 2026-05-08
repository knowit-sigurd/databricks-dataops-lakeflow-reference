# Architecture

A Databricks-native DataOps project using Spark Declarative Pipelines (SDP)
and Databricks Asset Bundles (DAB) for Git-driven pipeline promotion.

## Approach

This project uses platform-native capabilities instead of a custom DataOps framework.

| Concern        | Custom Python framework | This project (SDP)          |
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

The gold join is `left` on `customer_id`. All validated silver customers appear in
`customer_order_summary`. Customers with no orders receive `order_count=0` and
`total_amount=0.0`. An `inner` join would silently exclude inactive customers from
reporting — this is treated as data loss, not a valid filter.

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

Each validation rule carries a `severity` field that determines how violations are
handled at runtime. `quality_mode` (read from `spark.conf.get("quality_mode", "drop")`)
controls the behavior of `critical` rules only. The `expect_for()` helper in each
pipeline file resolves the correct DLT decorator from both inputs.

| Severity         | dev / PR (`quality_mode=drop`) | prod (`quality_mode=fail`) |
|------------------|-------------------------------|---------------------------|
| `critical`       | `expect_or_drop` — row dropped, pipeline continues | `expect_or_fail` — pipeline fails |
| `business_invalid` | `expect_or_drop` — row dropped, pipeline continues | `expect_or_drop` — row dropped, pipeline continues |
| `warning`        | `expect` — row passes through, expectation tracked | `expect` — row passes through, expectation tracked |

Current rule classification:

| Rule                 | Severity         | Field              |
|----------------------|------------------|--------------------|
| `valid_customer_id`  | `critical`       | `customer_id`      |
| `valid_customer_name`| `business_invalid` | `customer_name`  |
| `valid_order_id`     | `critical`       | `order_id`         |
| `valid_customer_id` (orders) | `critical` | `customer_id`   |
| `valid_amount`       | `business_invalid` | `amount`         |

Rejected rows are written to `customers_rejected` / `orders_rejected` with three
diagnostic columns: `rejection_reason` (comma-separated rule names, upper-cased),
`rejection_severity` (highest severity for the row), and `rule_version` (currently `"1.0"`).
A row failing both a `critical` and a `business_invalid` rule gets `rejection_severity = critical`
because `coalesce` picks the first non-null value and rules are ordered critical-first in the dict.

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
| PR     | sdp_pr_<n> | /Volumes/dataops_lab/sdp_pr_<n>/raw | drop         | default |
| dev    | sdp_dev    | /Volumes/dataops_lab/sdp_dev/raw  | drop         | default |
| prod   | sdp_prod   | /Volumes/dataops_lab/sdp_prod/raw | fail         | 0       |

PR-based deployments use `deployment_suffix=pr_<n>` and `target_schema=sdp_pr_<n>`,
giving each PR a fully isolated environment: pipeline name, UC schema, and source volume
are all scoped to `sdp_pr_<n>`. Concurrent PRs cannot share or overwrite each other's
input data or output tables — verified by live concurrent execution (M22, M28).

## Deployment model

Deployment is controlled through GitHub Actions and Databricks Asset Bundles.
Bundle deployment runs first to create the schema, then the volume is provisioned, then
source data is uploaded.

```
PR opened
  → databricks bundle deploy -t dev --var=deployment_suffix=pr_<n> --var=target_schema=sdp_pr_<n>
  → creates pr_<n>_medallion_pipeline and schema dataops_lab.sdp_pr_<n>
  → databricks volumes create dataops_lab sdp_pr_<n> raw MANAGED
  → upload_data.sh dev sdp_pr_<n>
  → databricks bundle run medallion_pipeline --refresh-all
  → validate_counts.py asserts all 7 table row counts via SQL warehouse

PR closed (merged or abandoned)
  → databricks bundle destroy -t dev --var=deployment_suffix=pr_<n>
  → databricks schemas delete --force dataops_lab.sdp_pr_<n>
  → removes pipeline resource, UC schema, tables, and managed raw volume

Merged to main
  → (pauses: GitHub production environment, required reviewer must approve)
  → upload_data.sh prod
  → databricks bundle deploy -t prod --var=deployment_suffix=prod
  → updates prod_medallion_pipeline writing to dataops_lab.sdp_prod
  → prod pipeline execution is operator-triggered, not CI-triggered
```

Dynamic naming logic (suffix, schema) is resolved in GitHub Actions and passed into DAB.
`databricks.yml` stays static — no string manipulation inside bundle configuration.

The `deploy-pr` job is skipped for Dependabot (`if: github.actor != 'dependabot[bot]'`).
Dependabot PRs update dependency manifests only — no pipeline logic changes, no Databricks
deployment needed. GitHub restricts repository secrets for external actors, so any deploy
job that requires secrets would fail silently for Dependabot PRs without this guard.
The `ci` job (lint + tests) still runs on Dependabot PRs: it is credential-free and
verifies the updated dependency resolves correctly before merge.

Pipeline ownership is set at deploy time to the identity that ran `databricks bundle deploy`.
In CI this is the service principal (`DATABRICKS_CLIENT_ID`). SDP pipelines have no `run_as`
field — there is no mechanism to separate deploying identity from pipeline owner. In a
production deployment, the deploying identity should be a dedicated data-pipeline service
principal, not a personal user account.

## Access model

Unity Catalog privileges are not managed by this repo or by `databricks bundle deploy`.
They require a one-time setup by a workspace admin before the pipeline can be operated
or browsed by human users. CI runs under a service principal with its own grants.

### Group-based grants (recommended)

Grant to groups, not individual users. Members of the group inherit access automatically.

| Principal | Privilege | Scope | Purpose |
|-----------|-----------|-------|---------|
| `data-engineers` | `USE CATALOG`, `USE SCHEMA`, `SELECT` | `dataops_lab` catalog | Browse all schemas and tables, sample data in UI |
| `data-analysts` | `USE CATALOG`, `USE SCHEMA`, `SELECT` | Gold tables only | Read-only access to `customer_order_summary` |
| CI service principal | `USE CATALOG`, `USE SCHEMA`, `SELECT`, `CREATE SCHEMA` | `dataops_lab` catalog | Deploy pipeline, run row count assertions |
| CI service principal | `CAN USE` | SQL warehouse | Required for `validate_counts.py` — not granted by default |

Granting `USE SCHEMA` at the catalog level propagates to all current and future schemas,
including dynamically created PR schemas (`sdp_pr_<n>`). Without catalog-level grant,
each new PR schema requires a separate grant — which is not practical.

SQL to set up `data-engineers`:
```sql
GRANT USE CATALOG ON CATALOG dataops_lab TO `data-engineers`;
GRANT USE SCHEMA ON CATALOG dataops_lab TO `data-engineers`;
GRANT SELECT ON CATALOG dataops_lab TO `data-engineers`;
```

### What is not covered here

Workspace-level admin roles, entitlement management, and identity federation (SSO/SCIM)
are IT and platform concerns outside the scope of this DataOps reference. In a client
deployment, group membership would be managed through the identity provider, not
configured manually.

## Deployment approval policy

PR deployments use `--auto-approve` to keep temporary resources synchronized with
the bundle definition without manual intervention.

Production deployments require explicit approval through the GitHub `production`
environment. A required reviewer must approve before `deploy-prod` runs. This creates
an audit trail of who approved each production release and when.

`databricks bundle plan` is run before `bundle deploy` in both jobs, so the resource
diff is visible in CI logs before any changes are applied.

## Development workflow

```
Local dev (VS Code + devcontainer)
  ↓  uv run ruff check / pytest
Feature branch → PR to main
  ↓  CI / ci must pass (lint + tests) — required gate
  ↓  Deploy SDP Pipelines / deploy-pr must pass (deploy + pipeline run + row counts) — required gate
Merge to main
  ↓  deploy-prod triggered, pauses for approval
  ↓  approved → bundle deploy to sdp_prod
Databricks pipeline execution (serverless)
```

Local Spark (via devcontainer) is used for fast iteration and testing transformation logic.
Full SDP pipeline execution requires Databricks — local runs cannot replicate expectations behavior.

## Branch protection

The `main` branch requires a pull request before merging. Direct pushes are blocked.

| Rule | Setting |
|------|---------|
| Require pull request before merging | Enabled — no approval required (solo repo) |
| Require status checks to pass | `CI / ci` and `Deploy SDP Pipelines / deploy-pr` must pass before merge |
| Require branches to be up to date | Enabled |
| Allow bypassing rules | Disabled — applies to admins too |

Both checks are required gates. `CI / ci` (lint + tests, ~1 min) verifies correctness
locally. `Deploy SDP Pipelines / deploy-pr` (deploy + pipeline run + row counts, ~5 min)
verifies the full Databricks execution path. Requiring deploy-pr to complete before merge
eliminates the race condition where `cleanup-pr.yml` runs concurrently with a still-running
`bundle run` and destroys the pipeline mid-execution. If deploy-pr has not completed, the
merge button is blocked — the cleanup workflow then runs against an idle, finished deployment.

## Monitoring and alerting

This repo does not implement push-based alerting. The current observability coverage is:

| Signal | Where to observe |
|--------|-----------------|
| CI failure (lint, tests) | GitHub Actions — email notification on failure |
| PR deployment failure | GitHub Actions — email notification on failure |
| Prod deployment | GitHub Actions — production approval gate + job result email |
| Pipeline execution history | Databricks pipeline UI — event log, update history |
| Data quality metrics | Databricks pipeline UI — expectation pass/fail rates per update |
| Row count correctness | `validate_counts.py` — asserts on every PR before merge |
| Rejected rows (SQL) | `sql/rejection_summary.sql`, `sql/rejected_rows.sql` — queryable via SQL warehouse |
| Event log — update history | `sql/event_log_runs.sql` — update durations and final state per run |
| Event log — table throughput | `sql/event_log_flow_progress.sql` — row counts and dropped records per table per run |

### Event log observability

The SDP event log (`event_log()` TVF) exposes update state transitions, per-table row counts,
and expectation drop counts as queryable SQL. `sql/event_log_runs.sql` and
`sql/event_log_flow_progress.sql` demonstrate both patterns.

Access requires pipeline ownership — `CAN_VIEW` permission is not sufficient. In this repo,
pipelines deployed by the CI service principal (`dataops-lab-sp`) are owned by that SP.
The `event_log()` queries in `sql/` target the dev pipeline, which is deployed locally under
the user's personal account.

`system.lakeflow.pipeline_events` surfaces the same data across all pipelines without
per-pipeline ownership. Accessing it requires `USE SCHEMA` on `system.lakeflow`, which must
be granted by an account admin. Once in place, `system.lakeflow` is the right foundation for
a cross-pipeline quality dashboard.

The `sql/` folder also contains rejection table queries (`rejection_summary.sql`,
`rejected_rows.sql`) which provide business-level rejection reasons per row — complementary
to the event log metrics, which report aggregate counts only.

### What production monitoring would add

In a client production deployment, the gaps to address are:

**Pipeline runtime alerting** — a prod pipeline triggered outside CI (scheduled run,
manual rerun) can fail silently. The platform-native fix is a Databricks notification
destination (webhook) wired to `on-update-failure` in the pipeline settings. This
supports Slack, PagerDuty, and other targets. Configuration lives in workspace admin
settings, not in `databricks.yml`.

**Data quality trending** — Databricks Lakehouse Monitoring can track expectation
pass rates and row count deviation over time, alerting when metrics degrade across
runs rather than just within a single run. Appropriate when pipelines run on a schedule
against changing source data.

**Row count deviation thresholds** — replace the hard-coded counts in
`validate_counts.py` with percentage-based thresholds (e.g. fail if count changes
more than 20% vs previous run). Requires persisting previous counts — typically a
Delta table or an external monitoring store.

### Why not implemented here

This is a reference lab with static fixture data and a single operator. Push
notifications add operational overhead before there is an operational need.
The right time to introduce alerting is when pipelines run on a schedule,
source data changes, and there are consumers who need to know when data is stale
or incorrect.

## Known limitations

- `databricks.yml` variable substitution does not support string manipulation — naming logic must live in CI/CD.
- Each PR deployment creates a dedicated managed UC Volume (`sdp_pr_<n>/raw`) for its source fixtures. The volume is destroyed with the schema on PR close. Full isolation — pipeline, schema, and source volume — is scoped to `sdp_pr_<n>`.
- `upload_data.sh` uses separate fixture files for dev and prod. Dev fixtures (`data/`) contain intentionally bad rows to demonstrate the rejection mechanism. Prod fixtures (`data/prod/`) are clean — all rows pass validation rules, so the prod pipeline completes successfully. In a real project this volume would be populated by Auto Loader, not CI scripts.
- Future: a staging target would require a separate workspace or UC catalog with its own schema namespace and credential scope. Out of scope for this reference lab.
- CI row count assertions use hard-coded expected values derived from static fixture CSVs. In production, replace these with percentage deviation thresholds (e.g. fail if row count changes >20% vs previous run). This requires state persistence for previous counts — typically a Delta table or a monitoring integration. Not applicable here because fixture data never changes between runs.
- `event_log()` queries in `sql/` target the dev pipeline (owned by the local user). The prod pipeline is owned by the CI service principal — its event log is inaccessible to human users without ownership transfer or account admin intervention.
- CI authentication uses a long-lived `DATABRICKS_CLIENT_SECRET` GitHub secret. The platform-native improvement is OIDC workload identity federation: GitHub Actions proves its identity via a short-lived cryptographic token, and Databricks issues a scoped access token in exchange — no stored secret, nothing to rotate. Configuring this requires Databricks account admin access (`accounts.cloud.databricks.com`) to set a federation policy on the service principal. That access is not available in this workspace. In a client deployment with a dedicated platform team, OIDC federation should be the default credential model for all CI/CD integrations.
- UC schemas and volumes are created by manual SQL during setup (see `docs/setup.md`). DAB supports declaring schemas and volumes as managed resources with inline grants, which would make the prod schema reproducible from `bundle deploy` without manual SQL. Not implemented here because `bundle destroy` removes all resources in a target — declaring `sdp_dev` in the dev target would cause `cleanup-pr.yml` to drop it on every PR close. Only fixed, long-lived schemas in targets that are never destroyed programmatically are safe to declare in DAB. In this repo that is the prod target only, which reduces the improvement to a single schema. Documented as a pattern; the constraint is real.
- This reference workspace runs on AWS. All DLT/SDP pipeline code, DAB configuration structure, UC Volumes, and CI/CD workflows are cloud-agnostic. The `medallion_operational_job` currently has no cloud-specific config (see below).
- `medallion_operational_job` is a single-task job (pipeline trigger only). Row-count assertions are a CI concern only (`scripts/validate_counts.py` on every PR). Adding a post-pipeline assertion task to the job requires either cluster creation rights (not available in this workspace) or `python_script_task` (Databricks serverless task compute, not supported by the Terraform provider bundled with CLI v0.298.0). In a client deployment with cluster creation rights or a newer CLI, a second task using `spark_python_task` or `python_script_task` can be added to run assertions and write a run-summary row to a persistent Delta table.

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

The change from `DoubleType` to `DecimalType(10,2)` for `amount` is an example of a
controlled type change: safe here because the explicit `StructType` from M6 makes it
a single reviewed line, no downstream consumers are broken, and the new type is
strictly more precise than the old one.

### Future production hardening

Handling unexpected columns at ingest (schema drift guard), Auto Loader schema evolution
mode, and schema registry integration are production patterns not implemented in this
reference. They are appropriate when source schemas are truly unknown or when multiple
upstream teams write to the same volumes.

## Future enrichment: Auto Loader bronze

This repo ingests source data from static CSV files uploaded by `upload_data.sh` before
each pipeline run. In a production deployment the correct pattern is Auto Loader
(`cloudFiles` source format), which monitors a cloud storage location for new files
and processes them incrementally as they arrive — no upload script, no manual trigger.

**What would change:**

- Bronze tables switch from `dlt.read_files()` or manual CSV reads to `dlt.read_stream()`
  with `format="cloudFiles"` and a schema hint or schema location
- `upload_data.sh` and the "Upload source data" CI step are removed
- The pipeline becomes event-driven: new files landing in the volume trigger processing
  automatically on the next scheduled or continuous run
- CI would need a different validation strategy — row count assertions against static
  fixture counts would no longer apply to a streaming bronze source

**Why not implemented here:**

This reference repo uses static fixture data to demonstrate data quality enforcement
predictably. Auto Loader adds operational realism but removes the ability to assert
exact row counts in CI, which is a core demonstration in the current design. The two
patterns serve different purposes: static fixtures for controlled quality demos, Auto
Loader for production ingestion pipelines. A production implementation would use Auto
Loader from the start and validate with deviation thresholds rather than hard-coded counts.