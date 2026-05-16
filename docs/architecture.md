# Architecture

A Databricks-native DataOps project using Spark Declarative Pipelines (SDP)
and Declarative Automation Bundles (DAB) for Git-driven pipeline promotion.

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
customers_bronze     → customers_silver ↘
                                          → customer_order_summary
orders_bronze        → orders_silver    ↗

customers_cdc_bronze → customers_current   (SCD1 via apply_changes())
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

Deployment is controlled through GitHub Actions and Declarative Automation Bundles.
The UC schema and managed volume are provisioned first via the Databricks CLI, source data
is uploaded, then bundle deploy creates the pipeline and job resources.

```
PR opened (code change)
  → databricks schemas create sdp_pr_<n> dataops_lab
  → databricks volumes create dataops_lab sdp_pr_<n> raw MANAGED
  → upload_data.sh dev sdp_pr_<n>
  → databricks bundle deploy -t dev --var=deployment_suffix=pr_<n> --var=target_schema=sdp_pr_<n>
    → creates pr_<n>_medallion_pipeline and pr_<n>_medallion_operational_job
  → stop_pipeline.py (waits for IDLE before triggering a run)
  → databricks bundle run medallion_pipeline --refresh-all
  → validate_counts.py asserts all 7 table row counts via SQL warehouse

PR opened (docs-only: changes only in docs/, README.md, .github/PULL_REQUEST_TEMPLATE.md, Makefile, uv.lock, .devcontainer/)
  → deploy-pr skipped — reported as "skipped" by GitHub, satisfies required status check
  → completes in ~7s

PR closed (merged or abandoned, code change)
  → databricks bundle destroy -t dev --var=deployment_suffix=pr_<n>
  → databricks schemas delete --force dataops_lab.sdp_pr_<n>
  → removes pipeline resource, UC schema, tables, and managed raw volume

PR closed (docs-only: docs/, README.md, .github/PULL_REQUEST_TEMPLATE.md, Makefile, uv.lock, .devcontainer/)
  → cleanup skipped — nothing was deployed, nothing to destroy

Merged to main (code change)
  → (pauses: GitHub production environment, required reviewer must approve)
  → upload_data.sh prod
  → databricks bundle deploy -t prod --var=deployment_suffix=prod
  → updates prod_medallion_pipeline writing to dataops_lab.sdp_prod
  → prod pipeline execution is operator-triggered, not CI-triggered

Merged to main (docs-only)
  → deploy-prod skipped — no approval prompt, no wait
```

Dynamic naming logic (suffix, schema) is resolved in GitHub Actions and passed into DAB.
`databricks.yml` stays static — no string manipulation inside bundle configuration.

The `deploy-pr` job is skipped in two cases. First, for Dependabot PRs
(`if: github.actor != 'dependabot[bot]'`): Dependabot updates dependency manifests only,
GitHub restricts secrets for external actors, and any deploy would fail silently without
this guard. Second, for docs-only PRs: a `changes` job runs first and queries the GitHub
API for the PR's changed files; if all files are under `docs/`, `README.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
`Makefile`, `uv.lock`, or `.devcontainer/`, `deploy-pr` is skipped. GitHub reports a skipped job
as "skipped", which satisfies the required status check. The `ci` job (lint + tests) runs
in both cases.

Pipeline and job ownership defaults to the identity that ran `databricks bundle deploy`.
In CI this is `dataops-lab-sp`, the dedicated service principal. DAB supports an explicit
`run_as` field on pipeline and job resources (available since CLI 0.241.0), which pins the
run identity independently of who deployed. This repo does not set `run_as` because prod is
always CI-deployed under `dataops-lab-sp` — the effective behavior is already correct. In a
multi-team deployment where engineers can deploy to shared targets, `run_as` should be
declared explicitly to prevent pipeline ownership drifting to individual user accounts:

```yaml
# databricks.yml — prod target pipeline/job resources
run_as:
  service_principal_name: dataops-lab-sp
```

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
  ↓  make ci (lint + test) / make validate / make deploy / make run / make assert
Feature branch → PR to main
  ↓  CI / ci must pass (lint + tests) — required gate
  ↓  Deploy SDP Pipelines / deploy-pr — required gate
       code change: deploy + pipeline run + row counts (~5 min)
       docs-only:   skipped, satisfies required check (~7s)
Merge to main
  ↓  code change: deploy-prod triggered, pauses for approval → bundle deploy to sdp_prod
  ↓  docs-only:   deploy-prod skipped, no approval prompt
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
locally. `Deploy SDP Pipelines / deploy-pr` verifies the full Databricks execution path for
code changes (~5 min: deploy + pipeline run + row counts); for docs-only PRs it is skipped
in ~7s and GitHub treats "skipped" as satisfying the required check. Requiring deploy-pr to
complete before merge eliminates the race condition where `cleanup-pr.yml` runs concurrently
with a still-running `bundle run` and destroys the pipeline mid-execution. If deploy-pr has
not completed, the merge button is blocked — the cleanup workflow then runs against an idle,
finished deployment.

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
- UC schemas (`sdp_dev`, `sdp_prod`) are declared as DAB-managed resources in the `platform` target with `lifecycle.prevent_destroy: true`. The `platform` target has its own isolated Terraform state (`root_path: ~/.bundle/dataops-lab-sdp/platform`). Schemas are in that target's `resources` block only — not in the global `resources:` block — so they never enter `dev` or `prod` Terraform state. `bundle destroy -t dev` (run by `cleanup-pr.yml` on every PR close) has no knowledge of these schemas and cannot touch them. `bundle destroy -t platform` fails with a `prevent_destroy` error. No automated workflow ever runs `bundle destroy -t platform` — it is a platform-admin-only surface. UC volumes remain manually provisioned (see `docs/platform-prerequisites.md`). In a production multi-team setup, platform resources belong in a separate bundle with independent CI permissions and a separate Terraform backend; the single-bundle approach here is the correct trade-off for a reference repo.
- This reference workspace runs on AWS. All DLT/SDP pipeline code, DAB configuration structure, UC Volumes, and CI/CD workflows are cloud-agnostic. The `medallion_operational_job` currently has no cloud-specific config (see below).
- `medallion_operational_job` has two tasks: `run_pipeline` (pipeline trigger) and `assert_output` (threshold-based validation via `scripts/assert_job_output.py`). The assertion task uses `spark_python_task` with `environment_key` (serverless compute — no cluster creation rights required). CI uses `scripts/validate_counts.py` with exact fixture counts on every PR; the job task uses threshold checks appropriate for production operations (bronze non-empty, gold non-empty when silver has rows, no critical rejections). The two scripts are intentionally separate: CI validates deterministic fixture data; the job validates operational health.

## CDC pattern: customers_current

`cdc_pipeline.py` demonstrates how to handle change data capture events using
`apply_changes()` — the DLT-native SCD implementation.

```
customers_cdc_bronze (streaming) → customers_current (SCD1)
```

The CDC fixture (`data/customers_cdc.csv`) is uploaded to a dedicated `cdc/`
subdirectory under the raw volume (`{source_path}/cdc/`). Separating it from
the batch source files is required: `spark.readStream.csv()` reads all CSV files
in the target directory, so mixing CDC events with batch customer/order files
would apply the wrong schema to the wrong data.

`customers_cdc_bronze` is a streaming table (defined with `spark.readStream`).
`apply_changes()` requires a streaming source — this is the distinction from the
batch bronze tables (`customers_bronze`, `orders_bronze`), which are materialized
views defined with `spark.read`.

`customers_current` is an SCD Type 1 table: it reflects only the latest known
state of each customer. Deletes remove the row entirely. History is not retained.
The key parameters:

| Parameter | Value | Purpose |
|---|---|---|
| `keys` | `["customer_id"]` | Primary key for upsert/delete matching |
| `sequence_by` | `sequence_num` | Ordering column — higher value wins on conflict |
| `apply_as_deletes` | `change_type = 'DELETE'` | Identifies tombstone records |
| `except_column_list` | `["change_type", "sequence_num"]` | CDC metadata stripped from target |
| `stored_as_scd_type` | `1` | Current state only; no history table |

`customers_current` is a standalone demo table — it is not wired into gold. In a
production setup the decision of which customer truth (batch silver or CDC current)
feeds downstream consumers is an architectural choice that depends on latency,
consistency, and consumer requirements.

**Not implemented:** SCD Type 2 (`stored_as_scd_type=2`) would retain full history
in a DLT-managed `__apply_changes_storage_*` table. Real-world CDC feeds would come
from Debezium, a Kafka topic, or a Databricks-native CDC source — not a fixture CSV.

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

### Bronze ingestion contract

`customers_bronze` and `orders_bronze` carry two metadata columns added at ingest time:

- `_source_file` — full path of the source file, using `_metadata.file_path` (the UC-native
  column for file metadata; `input_file_name()` is blocked in Unity Catalog)
- `_ingested_at` — pipeline execution timestamp via `current_timestamp()`

These columns are appended with `.withColumn()` after the CSV read and are not part of the
`StructType` schema definition. They answer the core ingestion traceability questions: where
did this row come from, and when was it loaded?

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

## Auto Loader demo: orders_autoloader_pipeline

`orders_autoloader_pipeline` demonstrates production-grade file ingestion using Auto Loader
(`cloudFiles` format). It is a standalone pipeline — separate from `medallion_pipeline`,
not part of the CI gate, and run manually to show three patterns.

### Tables

```
orders_autoloader_bronze  (streaming, cloudFiles)
  → orders_autoloader_silver   (clean rows, valid_order_id enforced)
  → orders_autoloader_rescued  (malformed rows captured by _rescued_data)
```

### Pattern 1: Streaming bronze ingest

Auto Loader monitors `/Volumes/dataops_lab/{schema}/raw/autoloader/` for new CSV files and
processes them incrementally. This is a subdirectory of the existing `raw` volume — Auto
Loader requires a directory path within an existing UC Volume, not a separate volume.
`cloudFiles.schemaHints` pins the known column types (`amount DECIMAL(10,2)`, etc.).
`cloudFiles.schemaLocation` persists the inferred schema between runs so Auto Loader does
not re-scan all files on restart.

### Pattern 2: Schema evolution

`cloudFiles.schemaEvolutionMode=addNewColumns` means that when `orders_evolved.csv`
(which adds a `region` column) is uploaded and the pipeline re-runs, Auto Loader detects
the new column, adds it to the bronze schema, and continues — no pipeline change required.

To demonstrate:
```bash
make upload-autoloader           # uploads orders_v1.csv (4 columns)
make run-autoloader              # run 1 — bronze has 4 columns
databricks fs cp data/autoloader/orders_evolved.csv \
  dbfs:/Volumes/dataops_lab/sdp_dev/raw/autoloader/ --overwrite -t dev
make run-autoloader              # run 2 — bronze schema evolves to 5 columns
```

### Pattern 3: Rescued data

`rescuedDataColumn=_rescued_data` means that a row whose `amount` value cannot be cast
to `DECIMAL(10,2)` is not dropped and does not fail the pipeline. The raw row is written
to bronze with `_rescued_data` populated as JSON. `orders_autoloader_rescued` surfaces
these rows for inspection.

To demonstrate:
```bash
databricks fs cp data/autoloader/orders_malformed.csv \
  dbfs:/Volumes/dataops_lab/sdp_dev/raw/autoloader/ --overwrite -t dev
make run-autoloader
-- Query: SELECT order_id, _rescued_data FROM sdp_dev.orders_autoloader_bronze
--        WHERE _rescued_data IS NOT NULL
```

### Why the fixture pipeline is unchanged

`medallion_pipeline` uses static CSV fixtures for predictable CI row count assertions.
Replacing it with Auto Loader would require abandoning exact-count CI validation —
Auto Loader is event-driven and the row count depends on what files have been uploaded.
The two pipelines serve different purposes: `medallion_pipeline` demonstrates quality
enforcement with deterministic CI; `orders_autoloader_pipeline` demonstrates production
ingestion patterns. Both are necessary parts of the reference.
