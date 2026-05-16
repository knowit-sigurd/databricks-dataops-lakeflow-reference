# Demo Guide — Technical Walkthrough

**Audience:** Data engineering lead  
**Duration:** ~30 minutes  
**Prerequisites:** Workspace access to `dbc-639f4875-165d.cloud.databricks.com`, catalog `dataops_lab` visible, `prod_medallion_pipeline` deployed and IDLE.

---

## Before the demo

Open these in advance so you are not searching during the session:

- Databricks workspace → Workflows → Pipelines
- Databricks SQL editor with `sql/event_log_runs.sql` loaded
- GitHub repo → `.github/workflows/deploy.yml`
- VS Code (or the repo in a browser tab) with `pipelines/customers.py` and `databricks.yml` ready

---

## 1. Architecture overview (5 min)

**What to open:** `docs/architecture.md`, the comparison table at the top.

**What to say:**

Start with this framing before opening any code:

> "This is not a production template — it's a decision accelerator. Everything here has been
> live-deployed in a real Databricks workspace. The point is to make the operating-model
> choices concrete so we can agree or disagree on them with code in front of us, not slides."

Then open `architecture.md` and walk the comparison table. The project uses platform-native
capabilities rather than building a custom DataOps layer. The comparison table makes the point
directly — orchestration, validation, observability, and execution are all handled by
Databricks. The custom code in this repo is transformation logic only.

The pipeline model is a single `medallion_pipeline` resource. Bronze reads from CSV volumes, silver standardises and validates, gold joins and aggregates. The key thing is that `dlt.read()` defines dependencies — there is no explicit job sequencing to maintain.

**Expected questions:**

- *"Why not separate pipelines per layer?"* — A single pipeline means one DAG. Databricks resolves the execution order from `dlt.read()` references. Separate pipelines would require external orchestration to sequence them and would lose the unified lineage view.
- *"How does this differ from a Delta Live Tables notebook?"* — It doesn't at the runtime level. SDP is the current name for DLT. The difference here is structural: logic is separated from pipeline entrypoints, rules are a single source of truth, and everything is deployed via DAB rather than workspace UI.

---

## 2. Code structure and rules (8 min)

**What to open:** `pipelines/customers.py`, then `pipelines/customer_pipeline.py`.

**What to say:**

Open `customers.py` and show `CUSTOMER_RULES`. This dict is the single source of truth for data quality — it drives three things simultaneously: the `@dlt.expect_or_drop` decorators on the silver table, the logic that writes to `customers_rejected`, and the unit tests. Change a rule in one place and all three stay in sync automatically.

```python
CUSTOMER_RULES = {
    "valid_customer_id": "customer_id IS NOT NULL AND customer_id > 0",
    "valid_customer_name": "customer_name IS NOT NULL AND LENGTH(TRIM(customer_name)) > 0",
}
```

Open `customer_pipeline.py` and show how the dict unpacks into decorators. Then show `rejected_customers` back in `customers.py` — it evaluates each rule independently and uses `concat_ws` to capture all failing reasons on a single row. A customer failing two rules gets both reasons, not just the first one.

Then show the `quality_mode` pattern in `customers.py`:

```python
quality_mode = spark.conf.get("quality_mode", "drop")
```

Same code runs in dev and prod. The variable is set in `databricks.yml` per target — `drop` in dev/PR, `fail` in prod. In dev you see the rejections and the pipeline completes. In prod, invalid data stops the pipeline.

**Expected questions:**

- *"What if we need to add a new validation rule?"* — Add one entry to `CUSTOMER_RULES` in `customers.py`. The decorator, the rejection capture, and the tests all pick it up automatically.
- *"Why `concat_ws` for rejection reasons?"* — `CASE WHEN` is first-match-wins. A row failing two rules would only record the first. `concat_ws` evaluates every rule independently and concatenates all failures — so analysts fix all violations at once instead of discovering them one at a time.
- *"How are tests structured?"* — Unit tests run against local PySpark (in the devcontainer). They import the same rule dicts and transformation functions. The pipeline entrypoints (`customer_pipeline.py`) are not unit-tested — those require Databricks. `validate_counts.py` covers end-to-end correctness after a full pipeline run.

---

## 3. Environment and deployment model (5 min)

**What to open:** `databricks.yml`.

**What to say:**

Show the `targets` block. Three targets: `dev`, `prod`, and `platform`. The variables `target_schema`, `source_path`, and `quality_mode` are all scoped per target. The pipeline code is identical — only the runtime configuration differs.

Show the `root_path` under each target. This is DAB state isolation — each PR deployment writes bundle state to a separate path under `~/.bundle/dataops-lab-sdp/dev/pr_<n>/`. Without this, closing any PR would destroy whichever pipeline was last deployed, not the one that PR owned. Verified: two concurrent PRs (pr_66, pr_67) ran simultaneously with fully isolated bundle state, schemas, and pipelines.

Show the `platform` target. It declares the shared UC schemas (`sdp_dev`, `sdp_prod`) as DAB-managed resources with `lifecycle.prevent_destroy: true`. This is the governance boundary: the platform team owns the `platform` target; the data engineering team owns `dev` and `prod`. `bundle destroy -t dev` (run on every PR close) cannot touch these schemas — they are not in the dev target's Terraform state.

Show `git: branch: main` under the `prod` target. Informational annotation — it surfaces in `bundle validate` output. The enforcement is in `deploy.yml`: the prod deploy job only runs on push to `main`.

**Expected questions:**

- *"What prevents someone from deploying to prod from a feature branch?"* — Two layers: `deploy.yml` has `if: github.ref_name == 'main'` on the prod job, and the GitHub `production` environment requires a named reviewer to approve. A local `bundle deploy -t prod` from any branch is still possible — this is a single-operator lab.
- *"How does PR isolation work in practice?"* — Each PR gets `deployment_suffix=pr_<n>`, producing a pipeline named `pr_<n>_medallion_pipeline` writing to schema `sdp_pr_<n>`. When the PR closes, `cleanup-pr.yml` destroys the pipeline and drops the schema. Verified by live execution: closing pr_66 removed only pr_66's pipeline and schema; pr_67 was unaffected until its own PR was closed.

---

## 4. Pipeline run and event log (5 min)

**What to open:** Databricks → Workflows → Pipelines → `prod_medallion_pipeline`.

**What to say:**

Show the pipeline DAG. Point out the execution order flows from bronze through silver to gold — this is derived from `dlt.read()` dependencies, not configured explicitly. Point out the rejection tables (`customers_rejected`, `orders_rejected`) branching off the silver layer.

Show Pipeline details on the right: Creator, Owner, and Run as are all `dataops-lab-sp` — the CI service principal. This is the pipeline identity model: whoever deploys becomes the owner. In a real client deployment this would be a dedicated data-pipeline service principal, not an individual's account.

Switch to the SQL editor. Run `sql/event_log_runs.sql` — show update history with start time, end time, duration, and final state. Then run `sql/event_log_flow_progress.sql` — show per-table row counts per update. Point out that `dropped_records` on the silver tables matches the rejection table counts.

**Expected questions:**

- *"Can we query the event log for the prod pipeline?"* — Not directly as a human user — the CI service principal owns it. `event_log()` requires ownership. In a workspace with `system.lakeflow` enabled (requires account admin), cross-pipeline event data is available without ownership.
- *"What does a failed run look like?"* — `quality_mode=fail` in prod means the pipeline stops on the first invalid row. `pipelines.maxFlowRetryAttempts: 0` and `pipelines.numUpdateRetryAttempts: 0` mean it fails immediately with no automatic retries — a clear signal rather than silent retry loops.

---

## 5. Data quality queries (3 min)

**What to open:** SQL editor with `sql/rejection_summary.sql`, then `sql/rejected_rows.sql`.

**What to say:**

Run `rejection_summary.sql`. The dev schema has intentionally bad rows — one customer and one order that fail validation. Show the rejection reason column: if a row fails multiple rules, all reasons appear comma-separated in a single field.

Run `rejected_rows.sql`. Show the specific `customer_id` and `order_id` of the rejected rows with their reasons. In a production context this is the starting point for a data remediation workflow — the analyst knows exactly which rows to fix and why.

Note that these queries target `sdp_dev` — swap the schema name to `sdp_prod` or `sdp_pr_<n>` for other environments.

**Expected questions:**

- *"How do we alert when rejections spike?"* — Not implemented here. The platform-native path is a Databricks notification destination on `on-update-failure` (webhook to Slack/PagerDuty). For quality trending over time, Databricks Lakehouse Monitoring tracks expectation pass rates across runs. Both are documented in `architecture.md` under "What production monitoring would add."

---

## 6. CI/CD and promotion model (4 min)

**What to open:** GitHub → the repo → `.github/workflows/deploy.yml`, then a recent merged PR.

**What to say:**

Show `deploy.yml`. The `deploy-pr` job runs on every PR with code changes. It uploads data, deploys the bundle, stops any active pipeline, runs `--refresh-all`, then asserts row counts via `validate_counts.py`. This is not a syntax check — it is a full Databricks pipeline execution with correctness validation. For docs-only PRs (changes only in `docs/`, `README.md`, or the PR template), `deploy-pr` is skipped automatically and the PR completes in ~7s.

Open a recent merged PR and show the checks. `CI / ci` (lint + unit tests, ~1 min) and `Deploy SDP Pipelines / deploy-pr` (~5 min for code changes) are both required gates. The merge button is blocked until both pass. This means a PR cannot merge until the pipeline has run successfully on Databricks — unless it is a docs-only PR, in which case deploy-pr is skipped and GitHub treats "skipped" as passing.

Show `deploy-prod`. It only triggers on push to `main` and requires approval through the GitHub `production` environment — a named reviewer must click approve before the deployment runs. Every production release has an audit trail: who approved, when, what commit.

**Expected questions:**

- *"What if the pipeline takes too long on every PR?"* — For code changes it takes ~5 min. That is deliberate: `deploy-pr` is the primary correctness signal. The alternative — skipping the Databricks run — means tests pass but the pipeline might fail in prod. For documentation-only PRs the deploy is skipped automatically and the check completes in ~7s. The race condition that happens when a merge occurs while deploy-pr is still running is exactly why deploy-pr is a required gate.
- *"What happens when a PR is closed without merging?"* — `cleanup-pr.yml` runs automatically. It destroys the bundle and drops the PR schema from Unity Catalog. The catalog stays clean regardless of how many PRs are opened and abandoned.
- *"How do we handle hotfixes?"* — Same path as any change: PR → CI → deploy-pr → merge → prod approval. The process does not have a bypass. In a real setup you would configure a shorter fixture dataset for hotfix branches to reduce the deploy-pr wait time.
