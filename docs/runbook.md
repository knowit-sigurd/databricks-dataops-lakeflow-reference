# Runbook

Operational procedures for day-to-day use of this repo.

## Trigger the production pipeline

Production `bundle deploy` runs automatically after a merge to `main`, pending approval.
The pipeline itself is **not** triggered by CI — it is operator-triggered.

After `deploy-prod` completes in GitHub Actions, use either:

**Option A — Operational job (preferred):**
1. `Workflows → Jobs → prod_medallion_operational_job` in the Databricks UI
2. Click `Run now`
3. The job triggers `prod_medallion_pipeline` and completes when the pipeline finishes

**Option B — Pipeline UI directly:**
1. `Workflows → Pipelines → prod_medallion_pipeline`
2. Click `Start` (incremental) or `Full refresh` — see the table below
3. Monitor the run in the pipeline event log

Use Option B when you need `Full refresh` — the operational job always runs incremental.

## Full refresh vs Start (incremental)

| Situation | Use |
|---|---|
| Normal run, data has changed since last run | Start |
| First run after workspace setup | Full refresh |
| Prod was previously run against an empty volume | Full refresh |
| Gold shows 0 rows but silver has data | Full refresh |
| Schema change deployed (new column, type change) | Full refresh |

**Why this matters:** DLT tracks streaming state per table. If a previous run processed 0 rows
(e.g. the volume was empty), the engine considers those tables current and skips reprocessing
on the next incremental run — including the gold join. Full refresh clears all streaming state
and recomputes every table from scratch. When in doubt after a data or schema change, use
Full refresh.

## validate_counts.py fails on a PR

The `Assert row counts` CI step runs `scripts/validate_counts.py` against `sdp_pr_<n>`.
Expected counts are defined in `fixtures/expected_counts.json`.

**Check the rejection tables first:**

```sql
SELECT * FROM dataops_lab.sdp_pr_<n>.customers_rejected;
SELECT * FROM dataops_lab.sdp_pr_<n>.orders_rejected;
```

**Common causes:**

| Symptom | Likely cause |
|---|---|
| `customers_silver` fewer rows than expected | A validation rule is incorrectly rejecting valid rows — check `CUSTOMER_RULES` in `customers.py` |
| `customers_rejected` more rows than expected | Bad row added to `data/customers.csv`, or a rule expression is wrong |
| `customer_order_summary` has 0 rows | Gold join failed — check `customers_silver` and `orders_silver` both have data, then check `gold.py` |
| Query failed (not a count mismatch) | SP lacks `CAN USE` on the SQL warehouse, or `DATABRICKS_WAREHOUSE_ID` secret is wrong |

If fixture data was intentionally changed, update `fixtures/expected_counts.json`
to match the new row counts.

## PR cleanup failed or schema not removed

If `cleanup-pr.yml` failed partway through, there may be a stale pipeline or schema in the
workspace. Run cleanup manually inside the devcontainer:

```bash
# Replace <n> with the PR number
databricks bundle destroy \
  -t dev \
  --var=deployment_suffix=pr_<n> \
  --var=target_schema=sdp_pr_<n> \
  --auto-approve --force

databricks schemas delete --force dataops_lab.sdp_pr_<n>
```

## Orphaned pipelines or jobs in the workspace

If a deploy failed before DAB wrote its state file, the pipeline or job it created is not
tracked by `bundle destroy` and will not be removed by `cleanup-pr.yml`. Remove them by
name using the cleanup script:

```bash
# Replace <n> with the PR number
uv run python scripts/cleanup_orphaned_pipeline.py pr_<n>
```

This deletes both `pr_<n>_medallion_pipeline` and `pr_<n>_medallion_operational_job` (and
any DAB dev-prefixed variants like `[dev dataops_lab_sp] pr_<n>_medallion_pipeline`).
Run it once per PR number that has orphaned resources.

Verify in the Databricks UI:
- Pipelines: `pr_<n>_medallion_pipeline` is gone
- Catalog Explorer: `dataops_lab.sdp_pr_<n>` is gone

## Re-deploy dev bundle manually

Use `workflow_dispatch` in GitHub Actions: `Actions → Deploy SDP Pipelines → Run workflow → target: dev`.

This deploys the dev bundle only. The pipeline is not triggered and row counts are not
asserted — those steps are gated on PR events. Use this to push a config change to the
dev pipeline without opening a PR.

## Query the event log for a pipeline run

Open `sql/event_log_runs.sql` in a SQL editor. Replace the `<your-dev-pipeline-id>`
placeholder with your dev pipeline ID, visible in the pipeline URL in the Databricks UI.

The dev pipeline ID is tied to the deploying user. If the dev pipeline was redeployed under
a different identity, the ID will have changed — check the current pipeline URL.

The prod pipeline event log is not accessible to human users. The prod pipeline is owned by
the CI service principal (`dataops-lab-sp`). `event_log()` requires pipeline ownership —
`CAN_VIEW` is not sufficient. Use `system.lakeflow.pipeline_events` for cross-pipeline
observability (requires an account admin to grant `USE SCHEMA` on `system.lakeflow`).

## Check Databricks CLI version

All workflows pin to `v0.298.0`. If you upgrade locally, update the pinned version in all
three places:

- `.github/workflows/deploy.yml`
- `.github/workflows/cleanup-pr.yml`
- `.devcontainer/Dockerfile` (installs CLI at image build time)

Check the version currently active in the container:

```bash
databricks --version
```

A version mismatch between local and CI is a latent risk — a CLI breaking change will surface
in CI before local testing catches it.
