# Databricks DataOps Reference Implementation

An executable slice of a Databricks-native DataOps operating model — built to accelerate
architectural decisions, not to serve as a complete production template.

The repo demonstrates one vertical: Git-driven pipeline promotion, schema-per-PR isolation,
declarative data quality, CDC with `apply_changes()`, and a production approval gate — all
using platform-native Databricks capabilities without a custom framework. Every pattern has
been live-verified in a real workspace. The gaps are documented deliberately: Auto Loader
ingestion, multi-pipeline orchestration, and full governance are out of scope here, and that
boundary is the starting point for a client conversation.

For a deeper look at the design decisions, environment model, data quality strategy, and deployment approval policy, see [docs/architecture.md](docs/architecture.md).

To demonstrate the repo to a client, see [docs/demo-guide.md](docs/demo-guide.md) (30-minute technical walkthrough for a data engineering lead) or [docs/demo-guide-exec.md](docs/demo-guide-exec.md) (10-minute executive overview).

For first-time workspace setup, see [docs/platform-prerequisites.md](docs/platform-prerequisites.md) (platform team) and [docs/setup.md](docs/setup.md) (data engineering team). For operational procedures (prod trigger, full refresh, cleanup recovery), see [docs/runbook.md](docs/runbook.md).

## Project structure

```
pipelines/          # SDP pipeline definitions (customer, orders, gold, CDC, Auto Loader) + logic modules
mutators/           # DAB Python mutators (set_run_context.py — adds deployed_at tag at deploy time)
tests/              # Transformation unit tests (pytest)
scripts/            # Utilities (upload_data.sh, stop_pipeline.py, validate_counts.py, assert_job_output.py, cleanup_orphaned_pipeline.py)
contracts/          # Data contracts (customer_order_summary.yml — verified by operational job)
fixtures/           # Expected row counts for CI assertions (expected_counts.json)
sql/                # Observability queries (event log, rejection tables)
data/               # Dev fixture CSVs (intentionally bad rows for rejection demo)
data/prod/          # Prod fixture CSVs (clean — all rows pass validation)
docs/               # Architecture, learning log, demo guides
.github/workflows/  # CI and deploy workflows (ci.yml, deploy.yml, cleanup-pr.yml, cleanup-stale.yml, failure-demo.yml)
.github/            # Dependabot config (weekly pip + actions updates) + PR template
databricks.yml      # Bundle config (targets: dev, prod, platform)
Makefile            # Dev lifecycle commands (lint, test, deploy, run, assert, clean)
```

## How it works

Pipelines are defined declaratively in Python using the `pyspark.pipelines` API and deployed
as Declarative Automation Bundles. Promotion is controlled entirely through Git.

```
PR opened       →  deploys pr_<n>_medallion_pipeline to sdp_pr_<n>  (quality_mode: drop)
Merged to main  →  deploys prod_medallion_pipeline to sdp_prod       (quality_mode: fail)
```

Each PR gets a fully isolated environment: pipeline name, UC schema, and source volume are
all scoped to `sdp_pr_<n>`. Schema and volume are destroyed on PR close.

## What this is (and isn't)

This is a **decision accelerator**, not a production template. Use it to answer:

- Do we agree on DAB for CI/CD and environment isolation?
- Do we agree on SDP expectations as the quality contract?
- Do we agree on PR-scoped schemas for developer isolation?
- Do we agree on operator-approved production promotion?
- Do we agree on service-principal run identity for automated pipelines?

Each of those is a real architectural choice. This repo makes them executable and debatable.
What it does not cover — Auto Loader for streaming ingestion, multi-pipeline orchestration,
full UC governance, OIDC federation — is documented in `docs/architecture.md` under each
relevant section.

## CI/CD

| Trigger | Workflow | What happens |
|---|---|---|
| Pull request (code change) | CI + Deploy | Lint, test, deploy `pr_<n>` to `sdp_pr_<n>`, run pipeline, assert counts |
| Pull request (docs-only) | CI only | Lint and tests run; deploy skipped — completes in ~7s |
| PR closed | Cleanup | Destroy pipeline, drop `sdp_pr_<n>` schema and managed volume |
| Push to main | Deploy | Approval gate → deploy `prod` target to `sdp_prod` |
| Manual dispatch | Deploy | Deploy dev bundle only |

See [docs/architecture.md](docs/architecture.md) for the full deployment model and branch protection rules.

## Pipeline

```
customers_bronze → customers_silver ↘
                                      → customer_order_summary
orders_bronze    → orders_silver    ↗
```

## Dev container

The development environment is based on the [databricks-dev-container](https://github.com/Knowit-Objectnet/databricks-dev-container) — a community devcontainer for Databricks development. Contributions that improve the experience are welcome.

## Local development workflow

```bash
make ci        # lint + test (mirrors CI)
make validate  # validate bundle config
make upload    # upload fixture data to UC volume
make deploy    # deploy bundle to dev
```

Run `make help` to see all available targets.
