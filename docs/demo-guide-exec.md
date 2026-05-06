# Demo Guide — Executive Overview

**Audience:** Technical manager or decision-maker evaluating a Databricks-native DataOps approach  
**Duration:** ~10 minutes  
**Prerequisites:** None — no Databricks access required. A browser showing the GitHub repo is sufficient.

---

## Opening frame (1 min)

Most data teams build a custom DataOps framework alongside their pipelines. They write orchestration code, validation logic, promotion scripts, and monitoring tooling — and then maintain all of it indefinitely as the platform evolves beneath it.

This reference demonstrates the alternative: using Databricks platform capabilities directly, so the team writes transformation logic and lets the platform handle the rest.

---

## 1. The problem with custom frameworks (2 min)

**What to show:** `docs/architecture.md`, the comparison table.

| Concern | Custom Python framework | This project |
|---------|------------------------|--------------|
| Orchestration | Custom `run_pipeline` | Databricks pipeline engine |
| Validation | Imperative Python code | `@dlt.expect_or_*` |
| Observability | SQL audit table | Pipeline UI + event log |
| Execution | Notebook / wheel job | Serverless compute |
| Deployment | DAB + GitHub Actions | DAB + GitHub Actions |

**What to say:**

A custom framework starts as a productivity tool and becomes a maintenance burden. Every Databricks platform update — new runtime, new API, changed behaviour — potentially breaks the framework. The team ends up maintaining two things: the business logic and the framework it runs on.

Platform-native means Databricks maintains the orchestration, validation engine, and observability. The team maintains the transformation logic and quality rules. That division is stable — business rules change, platform internals should not require team attention.

**Expected questions:**

- *"Is this just DLT with a wrapper?"* — There is no wrapper. The pipeline files use the Spark Declarative Pipelines API directly. The structure (rules dict, quality mode variable, schema definitions) is a convention, not a framework. Any Databricks data engineer can read and modify it without learning custom tooling.

---

## 2. Quality is enforced, not hoped for (3 min)

**What to show:** Databricks SQL editor — run `sql/rejection_summary.sql`.

**What to say:**

Data quality rules are declared once and enforced at the pipeline level. A row that fails a rule is rejected before it reaches the silver or gold layer. The rejection is captured with the specific rule that failed — not a generic error, but the named constraint: `valid_customer_id`, `valid_customer_name`, etc.

In the development environment, bad rows are captured and the pipeline completes — the team can see what is being rejected and why. In production, the pipeline fails immediately on invalid data with no retries. The data is either correct or the pipeline stops.

This means data quality is not a test that runs separately and can be skipped under deadline pressure. It is part of the pipeline definition. Changing a quality rule is a code change that goes through the same PR and approval process as any other change.

**Expected questions:**

- *"What if the rules are wrong?"* — Changing a rule is a pull request. It goes through code review, CI, a full pipeline run on Databricks, and production approval. There is no way to silently loosen a quality constraint without it appearing in the git history.
- *"What does the team do when rows are rejected?"* — The rejection tables are queryable SQL. The analyst runs `rejected_rows.sql` to see exactly which rows failed and why. The remediation workflow starts from there.

---

## 3. Every production deployment is controlled (3 min)

**What to show:** GitHub → a recent merged PR, then the Actions tab showing a `deploy-prod` run with approval.

**What to say:**

No code reaches production without passing two automated gates and one human gate.

The two automated gates run on every pull request: unit tests plus lint (~1 minute), and a full Databricks pipeline execution with row count assertions (~5 minutes). The merge button is blocked until both pass. This means the pipeline must run successfully on Databricks before any code can merge — not just locally, not just in tests.

The human gate is a GitHub `production` environment. After a PR merges to main, the production deployment pauses and waits for a named reviewer to approve. Every production release has an audit trail: who approved, when, and what commit was deployed.

The result is that the team knows — with certainty — what is running in production, who put it there, and when.

**Expected questions:**

- *"How long does a deployment take?"* — About 5 minutes for the PR pipeline run, then a few minutes for the production deploy after approval. The time is dominated by the Databricks pipeline execution, which is also the correctness proof.
- *"What if we need to deploy urgently?"* — The process does not have a bypass. In a genuine emergency the approval step takes seconds — a reviewer clicks approve. The automated gates always run. That is the point: speed comes from a stable process, not from skipping checks.
- *"What does it cost to run on every PR?"* — Serverless pipeline compute is billed per DBU per second. A full run of this reference pipeline completes in under 2 minutes. At production scale with larger datasets, the fixture size would be reduced for PR pipelines to control cost.

---

## 4. What it takes to build and maintain (1 min)

**What to say:**

This reference repo represents the full pattern: medallion pipeline, data quality enforcement, schema-per-PR isolation, production approval gate, event log observability. It was built incrementally over approximately three months of part-time work.

Adapting it for a specific client domain — replacing the customer/orders model with the client's actual entities and rules — is a 2–4 week engagement for a data engineer familiar with Databricks. The patterns transfer directly; only the business logic changes.

Ongoing maintenance is low. The CI/CD pipeline is self-operating. Platform updates come from Databricks. The team maintains transformation logic and quality rules — the parts that represent actual business knowledge.

**Expected questions:**

- *"Do we need Databricks expertise on the team?"* — Yes, one data engineer who knows Databricks SDP and DAB. The patterns in this repo are standard — they align with Databricks documentation and best practices, so onboarding follows platform learning paths, not internal documentation.
- *"What is not covered here?"* — Scheduled pipeline execution (this demo uses manual and CI-triggered runs), Auto Loader for streaming ingestion from cloud storage, and a staging environment. All three are natural next steps for a production deployment; none require rearchitecting what is here.
