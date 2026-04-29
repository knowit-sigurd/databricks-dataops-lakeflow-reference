# Learning Log

## 2026-04-15

### What I worked on
- Created the initial structure for `databricks-dataops-lab-v2`
- Set up local development workflow
- Defined the initial architecture direction
- Prepared the repo for Databricks Free Edition learning

### What I learned
- A clean repo foundation reduces friction later
- It is better to delay CI/CD and deployment automation until the local baseline is stable
- Unity Catalog should be the default target model in v2

### What was unclear
- Exact local setup for Python, virtual environment, and Makefile on macOS
- How much should be prepared before starting Databricks work
- When to introduce DAB and GitHub Actions in v2

### What I want to improve next
- Get the local environment working cleanly
- Finalize bootstrap files
- Start Week 1 with a Databricks-native structure

## 2026-04-15 – Week 1 Day 1

### Focus
Implemented the first Unity Catalog + Delta bronze write using the existing package and notebook structure.

### What I changed
- Kept `src/my_project` as the Python package boundary
- Implemented a real bronze write flow in `src/my_project/ingest.py`
- Updated `notebooks/etl_entry.py` to call package logic instead of only printing readiness
- Added config contract tests for bronze, silver, and gold table names

### What I observed
- The repo structure was already good enough for Databricks-native learning
- The real next step was proving table behavior in Unity Catalog
- Thin notebooks feel minimal, but that is the correct design direction

### Mapping to prior experience
- Config-driven table names map well to traditional DW object naming discipline
- The main change is that Unity Catalog + Delta become the primary operational target
- Git branch + commit now act as the controlled change unit before platform execution

### Good enough decisions
- Used a small seed dataset
- Used `overwrite` for the first learning run
- Avoided DAB, CI/CD, and generic framework abstractions for now

### Next step
- Read from bronze and build the first silver transformation

### Databricks validation result
- Confirmed `workspace.dataops_lab.bronze_customers` was created successfully
- Verified the table contains 3 expected rows
- Confirmed the table is a managed Delta table in Unity Catalog
- Confirmed Delta history shows the initial write with 3 output rows

### Key lessons
- The catalog name must match the actual workspace catalog, not an assumed default like `main`
- In Databricks, imported Python modules can remain stale after Git-folder updates until Python is restarted
- The real output of the pipeline is the governed table object, not the notebook execution itself

## 2026-04-16 – Week 1 Day 2

### Focus
Built first bronze → silver transformation.

### What I did
- Read bronze table using spark.table()
- Applied simple data quality filters
- Standardized values
- Wrote silver Delta table

### What I learned
- Tables are the main interface, not file paths
- Transformation logic belongs in Python modules, not notebooks
- Silver layer represents a contract boundary, not just another table

### Key insight
- This closely maps to staging → cleansed layers in traditional DW, but is simpler and more flexible in implementation

## 2026-04-15 – Week 1 Day 3

### Focus
Added operational logging, row counts, and validation to the bronze → silver pipeline.

### What I changed
- Added reusable logger setup
- Added simple row-count metrics
- Added customer validation checks
- Logged bronze input metrics and silver validation outcome
- Enabled autoreload support for smoother Databricks Git-folder iteration

### What I observed
- Logging and validation make the pipeline feel more operationally realistic
- Row counts and validation outcomes are the first things I would want to inspect as a consultant
- This is closer to DataOps than simple transformation logic alone

### Mapping to prior experience
- Similar to batch control totals and validation reports in traditional DW
- Difference is that logic, execution, and object inspection are more tightly integrated in Databricks

## Week 1 Day 4

### Focus
Introduced idempotency and incremental thinking.

### What I changed
- Changed bronze from overwrite to append
- Introduced deduplication in silver
- Simulated incremental ingestion using dynamic ingest_date

### What I observed
- Bronze grows with each run
- Silver remains stable due to deduplication
- This demonstrates idempotent pipeline behavior

### Key insight
- Bronze represents ingestion history
- Silver represents business truth
- Idempotency is critical for reliable pipelines

### Reflection
I tested append-based bronze ingestion to demonstrate rerun behavior and idempotency.
This was useful for learning, but for my current architecture preference I see bronze more as a controlled raw snapshot layer than a retained ingestion-history layer.

### Current position
- Bronze: latest raw snapshot, overwrite is acceptable
- Silver: validated and stable business-facing layer
- Historical retention should be introduced intentionally, not assumed as part of bronze

## Week 1 summary

### What I achieved
- Built a working Databricks bronze/silver pipeline using Python-first logic and thin notebook entrypoints
- Established a local-first workflow with Git, PRs, GitHub main branch, and Databricks Git folder execution
- Validated Unity Catalog managed Delta tables in Databricks
- Added operational logging, row counts, validation checks, and run summary output

### Key lessons
- The Databricks catalog must reflect actual workspace reality, not assumed defaults
- Imported Python modules in Databricks can stay stale until runtime state is refreshed
- Schema changes in Delta must be handled explicitly
- Bronze/silver layer semantics must be intentional, not copied mechanically
- Logging and validation are essential for operational trust, not just technical correctness

### Current architecture position
- Bronze = latest landed raw snapshot, overwrite is acceptable
- Silver = validated and stable contract layer
- Observability should start simple: logs, counts, validation, Delta history

### What I want to improve next
- Persist run metadata
- Add stronger validation patterns
- Think more explicitly about reruns, incremental loads, and monitoring

## 2026-04-17 – Week 2 Day 1

### Focus
Added local Spark-based tests for transformation and validation logic.

### What I changed
- Added a shared Spark test fixture
- Added tests for silver transformation behavior
- Added tests for validation logic and explicit failure handling
- Kept Databricks execution as a secondary confirmation step

### What I observed
- Local tests give much faster feedback than relying only on Databricks runs
- Testing transformation rules directly increases confidence when changing business logic
- Validation logic is easier to reason about when tested separately from pipeline execution

### Mapping to prior experience
- Similar goal as pre-deployment validation in traditional DW/DataOps
- Difference is that Spark transformation logic can now be tested locally in the repo

### Key takeaway
- Databricks execution proves platform behavior
- Local Spark tests prove transformation and validation behavior
- Both are needed, but they serve different purposes

## 2026-04-20 – Week 2 Day 2

### Focus
Implemented explicit validation strategy with strict vs lenient mode and rejected row handling.

### What I changed
- Added `validation_mode` to config
- Split valid and rejected customer rows explicitly
- Added rejected row table with rejection reason
- Implemented strict mode (fail on rejects)
- Implemented lenient mode (continue with valid rows)

### What I observed
- Validation strategy is an architectural decision, not just a coding detail
- Rejected row persistence makes failures easier to inspect
- Strict vs lenient behavior changes operational semantics significantly

### Mapping to prior experience
- Similar to reject handling and exception tables in traditional DW
- Difference is that the strategy is now easier to test and express directly in code

### Key takeaway
- The important thing is not choosing one universal rule
- The important thing is making the rule explicit, observable, and testable

### Testing refinement
I adjusted `test_transform.py` so that it tests transformation behavior only, not validation/filtering behavior.

This matches the current architecture better:
- `validate.py` owns valid vs rejected row handling
- `transform.py` owns standardization and derivation of the silver contract

## 2026-04-20 – Week 2 Day 3

### Focus
Added a lightweight persisted audit trail for pipeline runs.

### What I changed
- Added `pipeline_run_log` as a Delta audit table
- Persisted one run record per pipeline execution
- Captured both success and failure outcomes
- Stored validation mode, row counts, and error message

### What I observed
- Notebook logs explain a single run
- The audit table gives cross-run visibility
- Rejected rows and run metadata complement each other well

### Mapping to prior experience
- Similar to batch control tables in traditional DW/DataOps
- Simpler to implement directly in the Databricks pipeline code

### Key takeaway
- Operational trust improves when run metadata is stored durably, not only logged

## Week 2 Day 5

### Focus
Refactored pipeline into reusable execution pattern.

### What I changed
- Introduced `run_pipeline()` wrapper
- Separated pipeline definition from execution logic
- Removed duplicated audit and error handling logic

### What I observed
- Pipeline structure became cleaner
- Easier to add new pipelines
- Audit and logging are now consistent across pipelines

### Key insight
- DataOps maturity comes from standardizing execution patterns, not just writing working pipelines

## 2026-04-21 –  Week 3 Day 1

## Week 3 Day 1

### Focus
Introduced proper runtime parameterization and job-based execution.

### What I changed
- Moved parameter handling to notebook layer
- Updated Config to accept runtime parameters cleanly
- Created Databricks Job for pipeline execution

### What I observed
- Behavior is now controlled without code changes
- Pipeline is reusable across scenarios
- Job execution is reproducible and closer to production

### Key insight
- Separating runtime configuration from code is essential for scalable DataOps

## Week 3 Day 2

### Focus
Introduced environment-aware schema strategy.

### What I changed
- Derived schema from environment parameter
- Enabled dev/test/prod separation in one workspace

### What I observed
- Same pipeline can run across environments without code changes
- Data and audit logs are isolated per environment

### Key insight
- Environment separation is a design decision, not a platform constraint

## Week 3 Day 3

### Focus
Refactored configuration into explicit defaults and derived naming.

### What I changed
- Centralized config defaults
- Derived schema and table names through helper methods
- Added tests for environment-specific and custom config behavior

### What I observed
- The pipeline behavior did not change, but configuration became easier to reason about
- This is a necessary step before CI/CD and packaging

### Key insight
- Good configuration design reduces friction in deployment and environment handling

## Week 3 Day 4

### Focus
Introduced packaging mindset and package entrypoint structure.

### What I changed
- Added `__main__.py` as a package entrypoint
- Kept notebook execution as a Databricks-specific runtime adapter
- Clarified the future path from workspace modules to packaged deployment

### What I observed
- The repo now feels more like a deployable artifact than just source code
- Packaging mindset is mainly about structure and separation before it becomes a deployment mechanism

### Key insight
- Workspace/Git-folder execution is good for development
- Packaging is the bridge to repeatable deployment and CI/CD

## Week 3 Day 5

### Focus
Built the first Python wheel and made packaging more concrete.

### What I changed
- Updated packaging config for local wheel build
- Built wheel and source distribution locally
- Inspected the artifact contents

### What I observed
- The wheel is the deployable package artifact, not the whole repo
- The `src/` layout makes more sense when viewed through packaging
- `__main__.py` now feels more concrete as part of the packaged entrypoint

### Key insight
- Packaging is the bridge between source code and deployment
- CI/CD should automate packaging later, not replace understanding of it

## 2026-04-22 – Week 4 Day 1

### Focus
Introduced the first CI skeleton with GitHub Actions.

### What I changed
- Added a GitHub Actions workflow
- Automated formatting, linting, tests, and wheel build
- Included Java setup for Spark-based tests

### What I observed
- CI validates the project in a clean environment
- Spark tests and wheel build now work outside my laptop
- This is the first real automation layer in the project

### Key insight
- CI automates the same quality gates I already run manually
- The point is not to replace understanding, but to standardize verification

## Week 4 Day 2

### Focus
Introduced the first deployment-oriented skeleton.

### What I changed
- Added environment definition docs
- Added job definition doc
- Made deployment intent explicit in the repo
- Connected code, runtime parameters, and environment targets

### What I observed
- Deployment becomes easier to reason about when the target model is visible in the repo
- This is still manual, but much closer to a real deployment design

### Key insight
- A deployment model should be defined before it is automated
- CI/CD should later implement this model, not invent it

## Week 4 Day 3

### Focus
Introduced Databricks Asset Bundles (DAB) preview.

### What I changed
- Added `databricks.yml`
- Defined job as code
- Deployed job manually via CLI

### What I observed
- Job configuration can now be versioned
- Deployment is reproducible
- This replaces manual UI setup

### Key insight
- Asset Bundles are the bridge between code and platform deployment

## Week 4 Day 4

### Focus
Connected CI to deployment using GitHub Actions.

### What I changed
- Added deployment workflow
- Connected GitHub to Databricks via CLI
- Used bundle deployment from CI

### What I observed
- Deployment can now be triggered from GitHub
- No manual CLI required locally
- This completes the first CI/CD loop

### Key insight
- CI validates code
- CD deploys code
- Both should be defined as code

## Week 4 Day 5

### Focus
Implemented promotion strategy across dev, test, and prod.

### What I changed
- Added bundle targets per environment
- Introduced environment-specific variables
- Defined promotion rules in repo documentation

### What I observed
- Same pipeline behaves differently per environment
- Promotion can be controlled via Git and bundle targets

### Key insight
- Promotion is about controlling *when and where* a version runs, not just running code

## Week 4 – Bundle deployment cleanup note

### What I observed
Deploying the bundle from different identities and/or with different effective bundle paths created multiple job entries in Databricks.

### What I learned
Databricks bundle-managed resources are tied not only to the logical job definition, but also to deployment identity and bundle root path.

### Practical conclusion
To avoid duplicate jobs, I should:
- standardize `root_path`
- prefer one canonical deployment identity
- clean up older manual or duplicate jobs once the active bundle-managed job is confirmed

### Current position
I now treat the bundle-managed job deployed through the intended deployment path as the canonical job, and older duplicates as cleanup candidates.

## 2026-04-23 Week 5 – Day 1 – Operational maturity and runtime identity

### What I observed
The bundle-deployed job failed initially with Unity Catalog permission errors when running under the GitHub service principal.

After granting the required permissions, the job ran successfully end-to-end:
- bronze write
- rejected handling
- silver transformation
- duration logging

`pipeline_version` is currently set to `dev` in the deployed job.

### What I learned
Deployment and execution are separate concerns.

A successful bundle deployment does not guarantee runtime success:
- the run identity must have explicit Unity Catalog permissions

The service principal behaves differently from my user identity.

### Practical conclusion
To ensure stable execution:
- grant required permissions to the service principal
- use the bundle-managed job as the canonical runtime entrypoint
- treat deployment (GitHub Actions) and execution (job run) as separate steps

For observability:
- the updated audit model successfully captures runtime duration and failures

### Current position
I now have a working end-to-end flow using:
- GitHub Actions for deployment
- a service-principal job for execution
- audit logging for runtime visibility

Remaining gaps:
- improve `pipeline_version` semantics
- refine failure classification

## Week 5 – Day 2 – Environment-aware deployment and job naming

### What I observed
After updating the bundle configuration and deploying across targets, job names in Databricks now reflect the environment more clearly:

- `dev_customer_etl`
- `test_customer_etl`
- `prod_customer_etl`

`dev` and `test` jobs still include a prefix (`[dev github_service_principal]`), while `prod` appears cleaner.

Runtime behavior matches expectations:
- `dev` succeeds (lenient)
- `test` and `prod` fail due to rejected rows (strict)

---

### What I learned
Job naming and resource clarity are separate from pipeline logic.

Databricks bundle-managed resources can still carry historical or identity-based prefixes depending on how targets are configured and deployed.

Environment-specific behavior should be controlled through:
- bundle targets
- deployment inputs
- runtime configuration

—not through manual job edits in the UI.

---

### Practical conclusion
To improve operational clarity:
- use environment-first naming (`dev_customer_etl`, etc.)
- treat service-principal deployed jobs as canonical
- use GitHub Actions + DAB targets to control environment behavior
- use Favorites in Databricks UI to highlight canonical jobs

Accept that older or prefixed jobs are temporary and can be cleaned up later.

---

### Current position
I now have:

- environment-specific jobs with clear naming
- consistent behavior across dev/test/prod
- a deployment workflow that supports multiple targets
- improved ability to reason about jobs in the Databricks UI

Remaining gaps:
- fully standardize target configuration for consistent naming
- clean up duplicate and legacy jobs

## Week 5 – Day 3 – Failure semantics and retry classification

### What I observed
Pipeline runs now include clearer failure classification and a retryable flag.

- Permission errors are classified as `PERMISSION`
- Data validation failures are classified as `DATA_QUALITY`
- Failed runs in strict environments (test/prod) are marked as not retryable

Successful runs in `dev` remain unchanged.

---

### What I learned
Not all failures should be treated the same.

It is important to distinguish between:
- failures that require fixing data or configuration
- failures that may succeed if retried

Failure classification and retryability are separate concerns and should be explicitly modeled.

---

### Practical conclusion
To improve operational handling:
- classify failures into meaningful categories
- introduce a simple retryable rule based on failure category
- persist this information in the audit table

This enables better decision-making without adding complexity to the pipeline logic.

---

### Current position
I now have:

- structured failure classification (`DATA_QUALITY`, `PERMISSION`, etc.)
- a retryable flag for each failed run
- improved audit data that supports operational decisions

Remaining gaps:
- refine failure categories over time
- introduce retry behavior at job/orchestration level (later)

## Week 5 – Day 4 – Runtime configuration model

### What I observed
Refactoring the configuration model did not change runtime behavior in a visible way.

Jobs still ran as expected:
- `dev` succeeded (lenient)
- `test` and `prod` failed (strict)

I was not able to override parameters manually in the Databricks UI, since the jobs are bundle-managed.

### What I learned
In a bundle-managed setup, runtime behavior is primarily controlled by:
- DAB target configuration
- deployment inputs (GitHub Actions)
- code defaults

—not by manual parameter changes in the Databricks UI.

This means that the “runtime override” concept does not apply in the same way as in interactive or notebook-driven workflows.

### Practical conclusion
The configuration refactor improved internal structure, but did not yet provide practical value in my current workflow.

For this setup:
- environment behavior should be controlled through DAB targets
- parameter overrides should happen through deployment (or CLI), not UI
- manual overrides are not a primary mechanism when using bundle-managed jobs

### Current position
I now have:
- a cleaner and more explicit configuration model in code
- consistent behavior across environments driven by DAB

Remaining gaps:
- clarify how and when runtime overrides should be used in a DAB-based workflow
- align configuration design more closely with actual deployment and execution patterns

## Week 5 – Day 5 – Consolidation and framework clarity

### What I observed
The project now has a complete working DataOps loop:

- local development in VS Code
- Git branch + PR workflow
- CI validation (lint, test, build)
- CD deployment via GitHub Actions and DAB
- environment-specific job execution
- monitoring through `pipeline_run_log`

### What I learned
A working pipeline is not enough.

A reusable DataOps framework requires:
- a clear execution model
- documented environment behavior
- consistent job naming
- observable and explainable runtime behavior

### Practical conclusion
To make the project reusable and easier to explain:
- document the canonical execution flow
- standardize environment behavior (dev/test/prod)
- treat bundle-managed jobs as the only runtime entrypoints
- use the audit table as the foundation for monitoring

This turns the project from a working solution into a structured framework.

### Current position
I now have:
- a clear end-to-end DataOps workflow
- environment-aware deployment and execution
- consistent job naming and identification
- observable pipeline runs with audit metadata

Remaining gaps:
- tie `pipeline_version` to Git commits or tags
- strengthen CI/CD and promotion automation
- extend the framework to support multiple pipelines

## 2026-04-24 Week 6 – Day 1 – Git-driven versioning and production release control

### What I observed
`pipeline_version` is now aligned with Git:

- `dev` and `test` use commit SHA
- `prod` uses Git tags (e.g. `v1.2.0`)

Production deployment is now triggered only by pushing a tag:
- `git tag v1.2.0`
- `git push --tags`

Jobs behave as expected across environments, and `pipeline_run_log` reflects correct version values.

Adding `max_retries: 0` prevented duplicate audit rows on failed runs.

### What I learned
Git tags act as explicit release decisions, not just version labels.

Separating:
- commits (code changes)
- tags (approved releases)

gives strong control over what reaches production.

Versioning must be tied to deployment, not manually set in code or UI.

I also learned that retry behavior can impact audit integrity and must be explicitly controlled.

### Practical conclusion
To ensure proper version traceability and release control:
- use commit SHA for non-production environments
- use Git tags for production deployments
- trigger production deployment only from tagged commits
- disable retries in critical environments to avoid duplicate run logs

This creates a clear and auditable promotion model.

### Current position
I now have:
- full Git-driven version traceability
- controlled production releases via tags
- consistent version visibility in audit logs
- stable audit behavior without duplicate runs

Remaining gaps:
- streamline tagging workflow (reduce manual steps)
- introduce structured release process (e.g. GitHub Releases)
- automate parts of promotion flow while keeping control

## Week 6 – Day 2 – Controlled promotion flow with PR gates

### What I observed
Promotion between environments is now controlled through Git and enforced in the deployment workflow.

- Deploying to `test` from a feature branch is blocked
- Only code merged to `main` can be deployed to `test`
- `prod` deployment is still triggered by Git tags

The workflow now enforces correct promotion behavior automatically.

### What I learned
Promotion is not just about deploying code, but about controlling when and how code moves between environments.

Introducing PR as a gate ensures:
- code is reviewed before reaching `test`
- CI validation is completed before deployment
- `main` becomes a trusted source of truth

I also learned that promotion rules should be enforced in CI/CD, not just documented.

### Practical conclusion
To ensure controlled promotion:
- require PR and CI validation before merging to `main`
- restrict `test` deployments to `main` branch only
- use Git tags to control production releases

This creates a clear and enforceable promotion pipeline.

### Current position
I now have:
- a PR-based promotion gate for `test`
- enforced deployment rules in GitHub Actions
- a clear and controlled flow from dev → test → prod

Remaining gaps:
- automate parts of promotion flow while maintaining control
- introduce more advanced release handling (e.g. approvals, releases)

## Week 6 – Day 3 – CI/CD safety and workflow behavior

### What I observed
CI/CD safety is now implemented through workflow logic and manual enforcement.

- PRs include a checklist and CI validation before merge
- Deployment rules are enforced in GitHub Actions (e.g. test only from `main`)
- Production deployment is triggered only by Git tags

I also observed that invalid Git tags (not matching `v*`) do not trigger any workflow, resulting in no feedback or visible failure.

### What I learned
CI/CD enforcement can be both technical and procedural.

Because branch protection is not enforced in my current GitHub setup, I must rely on:
- PR discipline
- CI validation
- manual checks before merge

I also learned that:
- GitHub Actions only runs workflows when triggers match
- missing triggers result in silent non-execution, not failure

### Practical conclusion
To ensure safe deployment:
- treat CI as a mandatory gate even if not enforced by GitHub
- use PR checklists to enforce discipline
- rely on workflow guards to control promotion

For better visibility:
- consider triggering workflows on all tags and validating tag format inside the workflow

### Current position
I now have:
- CI/CD safety checks in workflows
- PR-based manual enforcement of quality gates
- controlled deployment behavior across environments

Remaining gaps:
- enforce branch protection once organizational GitHub account is available
- improve feedback for invalid deployment triggers (e.g. tag validation)

## 2026-04-25 Week 6 – Day 4 – Artifact-based execution and platform limitations

### What I observed
Attempting to switch from notebook-based execution to wheel-based execution exposed limitations in Databricks Free Edition.

- `python_wheel_task` could not be executed due to lack of supported job compute
- Serverless job compute is not available in this environment
- Notebook-based execution remains the only working runtime option

The wheel build and packaging worked correctly in CI, but could not be fully validated in Databricks.

### What I learned
There is a clear distinction between:
- development/runtime constraints (Free Edition)
- production-ready architecture (job compute + wheel execution)

Artifact-based execution is the correct production pattern, but requires:
- compatible Databricks workspace
- job compute or serverless workflows

I also learned that not all architectural steps can be fully validated in a constrained environment.

### Practical conclusion
For the current setup:
- keep notebook-based execution as the runtime model
- maintain wheel packaging and entrypoint for future use
- document wheel execution as the target production pattern

Avoid overengineering workarounds for platform limitations.

### Current position
I now have:
- a working notebook-based execution model
- a buildable Python wheel artifact
- a package entrypoint ready for future execution

Remaining gaps:
- validate `python_wheel_task` in a proper Databricks environment
- transition from notebook execution to artifact execution when supported

## Week 6 – Day 5 – Multi-pipeline support and framework generalization

### What I observed
The pipeline execution is no longer hardcoded to a single pipeline.

- Pipeline selection is now handled through a registry
- `pipeline_name` is passed as a runtime parameter
- Unknown pipeline names result in controlled failure

Existing pipeline behavior remained unchanged after introducing the registry.

### What I learned
A reusable DataOps framework requires separation between:
- execution logic
- pipeline definitions

Introducing a pipeline registry allows:
- multiple pipelines to share the same execution model
- consistent behavior across pipelines
- controlled extensibility

I also learned that dynamic resolution must include proper error handling to avoid silent failures.

### Practical conclusion
To support multiple pipelines:
- use a registry to map `pipeline_name` to pipeline functions
- pass pipeline name as a runtime parameter
- fail fast on unknown pipelines

This removes hardcoding and enables the framework to scale beyond a single use case.

### Current position
I now have:
- a pipeline registry supporting dynamic pipeline execution
- a reusable execution pattern (`run_pipeline`)
- consistent behavior across pipelines

Remaining gaps:
- add additional pipelines to validate framework scalability
- consider configuration-driven pipeline definitions (future step)

## 2026-04-27 Week 7 – Day 1 – First Spark Declarative Pipeline (SDP)

### What I observed
I successfully implemented and ran my first Spark Declarative Pipeline using serverless compute.

- Pipeline defined using `@dlt.table` and `@dlt.expect`
- Deployed via Databricks Asset Bundles
- Executed through Databricks pipeline UI (not jobs)

I initially got an error requiring a catalog when using serverless, which I resolved by explicitly defining catalog and schema in `databricks.yml`.

The pipeline created:
- `customers_bronze`
- `customers_silver`

Validation behavior is handled automatically by expectations.

### What I learned
Databricks-native pipelines enforce a different model compared to my v2 framework:

- Data must be written to a governed catalog and schema
- Orchestration is handled by the platform
- Validation is declarative (`@dlt.expect`) instead of imperative code
- Execution is pipeline-based, not job-based

I also learned that:
- Serverless pipelines require explicit data governance setup
- Deployment via CLI is sufficient for development before adding CI/CD

### Practical conclusion
For SDP pipelines:
- define data transformations declaratively
- use expectations instead of custom validation logic
- rely on Databricks for orchestration and monitoring
- explicitly configure catalog and schema

Avoid recreating functionality already provided by the platform.

### Current position
I now have:
- a working SDP pipeline in a proper Databricks workspace
- serverless execution configured correctly
- first comparison point against my v2 custom framework

Remaining gaps:
- understand expectation behavior in detail (fail vs drop vs track)
- compare SDP validation with my v2 rejected-row approach
- decide how much of my custom framework should be replaced

## Week 7 – Day 2 – Validation behavior in SDP

### What I observed
I tested different expectation behaviors in SDP:

- `@dlt.expect` → tracks invalid rows but does not remove or fail
- `@dlt.expect_or_drop` → filters out invalid rows and continues
- `@dlt.expect_or_fail` → fails the pipeline on invalid data

The pipeline UI provides visibility into:
- expectation metrics
- number of valid vs invalid rows
- failure reasons

Invalid rows are not persisted automatically in a separate table.

### What I learned
SDP provides built-in data quality handling that overlaps with my v2 validation design.

Compared to v2:
- strict mode ≈ `expect_or_fail`
- lenient mode ≈ `expect_or_drop`
- expectation tracking replaces parts of the audit logic

However, SDP does not provide a rejected table by default, only metrics and logs.

### Practical conclusion
For SDP pipelines:
- use `@dlt.expect_or_drop` as the default pattern
- use `@dlt.expect_or_fail` for strict validation when needed
- rely on pipeline UI and metrics instead of custom audit tables

Avoid recreating rejected-row handling unless there is a clear business requirement.

### Current position
I now have:
- a clear understanding of SDP expectation behavior
- a direct comparison between v2 validation and SDP validation
- a working validation model using platform-native features

Remaining gaps:
- understand how to persist rejected rows if needed
- evaluate how SDP validation integrates with monitoring and lineage
- decide when custom validation logic is still required

## 2026-04-28 Week 7 – Day 3 – Observability and rejected data in SDP

### What I observed
Databricks SDP provides strong built-in observability:

- pipeline execution tracking
- data quality metrics through expectations
- lineage and dependency visualization
- execution logs and failure information

However, SDP does not persist rejected rows by default, only aggregated metrics.

### What I learned
SDP replaces much of my custom observability from the v2 framework, including:
- run tracking
- validation metrics
- failure visibility

But it does not provide row-level visibility of invalid data.

I realized that rejected rows serve a different purpose than observability:
- they provide business-level traceability
- they support debugging and data correction

### Practical conclusion
The best approach is a hybrid model:

- use SDP expectations as the primary validation mechanism
- optionally persist rejected rows as a separate table when needed

This allows me to:
- leverage platform-native observability
- retain useful business-level visibility from my v2 design

### Current position
I now have:
- a clear understanding of SDP observability capabilities
- a comparison with my v2 audit model
- a decision to rely on SDP for monitoring and extend it selectively

Remaining gaps:
- implement rejected row handling as an SDP extension
- evaluate how this integrates with multiple pipelines
- define when rejected tables are required vs optional

## Week 7 – Day 4 – Multiple pipelines and execution model shift

### What I observed
I implemented multiple independent pipelines in SDP and saw that each pipeline manages its own execution and dependencies internally.

Pipelines are no longer executed as a sequence of jobs, but as a graph of data dependencies.

Each pipeline runs independently and defines its own DAG through table relationships.

### What I learned
SDP uses a fundamentally different execution model compared to traditional data warehouse solutions.

Instead of orchestrating jobs in a specific order, SDP derives execution order from data dependencies defined in code.

This removes the need for explicit orchestration within a pipeline, but shifts responsibility to defining correct data relationships.

I also realized that:
- pipelines scale horizontally (more pipelines), not vertically (more steps in one system)
- orchestration still exists, but at a higher level between pipelines, not within them

### Practical conclusion
To work effectively with SDP:
- define dependencies through `dlt.read` instead of job sequencing
- keep pipelines logically independent
- avoid recreating custom orchestration logic inside pipelines

For larger solutions:
- use multiple pipelines
- handle cross-pipeline dependencies separately

### Current position
I now have:
- multiple working SDP pipelines
- understanding of pipeline-level dependency management
- a clear comparison with my v2 registry/orchestration model

Remaining gaps:
- understanding cross-pipeline orchestration patterns
- learning how to coordinate pipelines in larger solutions
- deciding when custom orchestration is still required

## Week 7 – Day 5 – PR-based pipelines and platform limitations

### What I observed
I attempted to implement branch-based pipeline naming to create isolated pipelines per feature branch.

However, Databricks Asset Bundles do not support string transformations (such as replacing `/` in branch names) within variable substitution.

This caused deployment errors, and I reverted to using:

- `${bundle.target}` for pipeline naming

Pipelines now remain environment-based (dev/test/prod).

### What I learned
The idea of PR-based isolated pipelines is valid, but not directly supported through simple bundle variable substitution.

DAB variable handling is intentionally limited and does not support dynamic string manipulation.

I also learned that:
- platform-native tooling defines constraints that influence architecture decisions
- not all CI/CD patterns can be implemented directly in `databricks.yml`
- some logic (such as sanitizing branch names) must be handled outside the bundle, e.g. in GitHub Actions

### Practical conclusion
For now:
- keep environment-based pipeline naming (`dev_customer_pipeline`, etc.)
- avoid overengineering branch-based isolation in `databricks.yml`

For future implementation:
- PR-based pipelines should be implemented via CI/CD (passing sanitized variables)
- naming logic should be handled outside Databricks bundles

### Current position
I now have:
- multiple independent SDP pipelines
- environment-based deployment working correctly
- understanding of limitations in bundle variable substitution

Remaining gaps:
- implement PR-based pipeline isolation via CI/CD variables
- define cleanup strategy for temporary pipelines
- refine team-scale workflow patterns


## Week 8 – Day 1 – Production hardening and architecture decision

### What I observed
I compared my v2 custom DataOps framework with the SDP (Databricks-native) approach across key areas:

- orchestration
- validation
- observability
- deployment
- scalability

The SDP approach provides:
- built-in orchestration
- serverless execution
- native validation through expectations
- strong UI-based observability and lineage

My v2 framework provides:
- full control over execution and validation
- SQL-based observability
- rejected-row handling

### What I learned
The two approaches represent different architectural philosophies:

- v2 = custom-built, flexible, but complex
- SDP = platform-native, simpler, but more opinionated

I learned that:
- many components I built in v2 are already handled by Databricks in SDP
- platform-native solutions reduce complexity and operational overhead
- custom frameworks are only justified when platform capabilities are insufficient

### Practical conclusion
For new projects, SDP should be the default approach.

Use SDP for:
- orchestration
- validation
- observability
- deployment

Extend SDP only when needed, for example:
- persisting rejected rows for business use cases

Keep the v2 framework as:
- a learning reference
- a fallback for non-Databricks environments
- a source of ideas for extensions

### Current position
I now have:
- a working SDP pipeline implementation
- a complete custom DataOps framework (v2) for comparison
- a clear architectural decision for future projects

Decision:
- primary architecture → SDP
- extensions → rejected rows (optional)
- fallback → v2 framework

Remaining gaps:
- optimize developer workflow (local development)
- refine team-scale workflow patterns
- explore local SDP execution using devcontainer

## Week 8 – Day 2 – Local development with devcontainer

### What I observed
I set up a VS Code devcontainer for local Spark development.

- Spark can now run locally
- transformation logic can be tested without deploying to Databricks
- development loop is significantly faster

However, full SDP pipelines cannot be executed locally.

### What I learned
Local development and platform execution are separate concerns:

- local environment is used for fast iteration and testing
- Databricks is used for pipeline execution and observability

I also learned that:
- not all platform features can be replicated locally
- it is important to separate transformation logic from pipeline definitions

### Practical conclusion
Use local development for:
- testing transformations
- validating logic
- fast iteration

Use Databricks for:
- running pipelines
- validating expectations
- monitoring execution

This creates a balanced development workflow.

### Current position
I now have:
- local Spark development environment
- faster iteration loop
- better separation between development and execution

Remaining gaps:
- integrate local development into CI/CD
- refine testing strategy for SDP pipelines

## Week 8 – Day 3 – CI/CD deployment for SDP pipelines

### What I observed
I implemented a deploy workflow for the SDP repository using GitHub Actions.

- Created a new `deploy.yml` workflow
- Triggered deployment manually using `workflow_dispatch`
- Used Databricks CLI with service principal authentication
- Successfully deployed pipelines to the new workspace

The workflow integrates with existing CI, allowing a full flow from:
- local development → CI → deployment → Databricks pipeline execution

### What I learned
Even when using platform-native pipelines (SDP), CI/CD remains a critical part of the architecture.

I learned that:
- GitHub Actions must be explicitly created in each repository
- workflows only appear in GitHub after being committed to the default branch
- deployment logic is simpler for SDP compared to job-based execution
- service principal authentication works consistently across both v2 and SDP setups

### Practical conclusion
For SDP repositories:
- use GitHub Actions to manage deployment via DAB
- keep deployment workflows simple and focused
- use manual triggers (`workflow_dispatch`) during development
- rely on CI for quality validation before deployment

This creates a clean separation between:
- development (local/devcontainer)
- validation (CI)
- execution (Databricks pipelines)

### Current position
I now have:
- a working CI pipeline using `uv`, pytest, and ruff
- a deploy workflow for SDP pipelines
- successful end-to-end deployment from GitHub to Databricks

Remaining gaps:
- automate deployment based on PR or branch events
- refine team workflows for pipeline promotion
- implement PR-based pipeline isolation

## Week 8 – Day 4 – PR-based pipeline deployment

### What I observed
I implemented PR-based pipeline deployment using GitHub Actions.

- pipelines are now deployed automatically on PR creation
- each PR gets a unique pipeline name
- pipelines are isolated and do not conflict

After merging to main, production pipelines are deployed.

### What I learned
Dynamic pipeline behavior should be handled in CI/CD, not in Databricks bundle configuration.

GitHub Actions is the correct place for:
- branch detection
- naming logic
- environment selection

This avoids limitations in DAB variable handling.

### Practical conclusion
To implement PR-based pipelines:
- use GitHub Actions to generate dynamic variables
- pass variables into DAB during deployment
- keep `databricks.yml` simple and static

This results in clean and scalable pipeline management.

### Current position
I now have:
- automatic PR-based pipeline deployment
- isolated pipelines per feature branch
- production deployment tied to main branch

Remaining gaps:
- pipeline cleanup strategy (removing old PR pipelines)
- schema isolation for PR pipelines
- advanced promotion strategies

## Week 8 – Day 4 – PR-based deployment and quality modes

### What I observed
I implemented PR-based deployment for SDP pipelines using GitHub Actions and Databricks Asset Bundles.

The implementation now uses:
- `deployment_suffix` to control pipeline names
- `target_schema` to control schema placement
- `quality_mode` to control data quality behavior

PR and dev deployments write to `sdp_dev`, while production writes to `sdp_prod`.

Pipeline names are now generated from `deployment_suffix`, so PR pipelines can get names like:
- `pr_12_customer_pipeline`

I also introduced different quality behavior:
- dev / PR → bad rows are dropped and the pipeline succeeds
- prod → bad rows fail the pipeline

### What I learned
Dynamic naming and environment behavior should be handled through GitHub Actions variables and DAB variables, not through unsupported string manipulation inside `databricks.yml`.

I also learned that SDP production mode includes built-in retry behavior. This is useful for transient platform failures, but not ideal for deterministic data quality failures.

Data quality failures should usually fail clearly rather than retry repeatedly.

### Practical conclusion
The current pattern is:

- use GitHub Actions to resolve deployment context
- pass deployment variables into DAB
- use stable schemas for dev and prod
- use `quality_mode` to control validation behavior per environment

For production data quality failures:
- disable or reduce automatic retries
- rely on clear failure feedback instead of repeated retries

### Current position
I now have:
- PR-based pipeline deployment
- stable dev/prod schema separation
- environment-specific quality behavior
- better understanding of SDP retry behavior

Remaining gaps:
- confirm final retry settings in `databricks.yml`
- define cleanup strategy for old PR pipelines
- refine production deployment and monitoring patterns

## Week 8 – Day 5 – Production readiness and final architecture

### What I observed
I finalized the SDP pipeline architecture and resolved remaining production issues.

- Disabled retry behavior for data quality failures
- Confirmed correct separation between dev/PR and prod environments
- Verified pipeline behavior:
  - dev/PR → drop invalid rows
  - prod → fail on invalid rows

The architecture is now consistent across:
- naming
- schema
- deployment
- validation

### What I learned
Production-ready pipelines require clear behavior for failure scenarios.

Automatic retries are useful for transient failures, but not for deterministic data quality issues.

I also learned that:
- clean separation of concerns (naming, schema, validation) simplifies architecture
- most custom logic from v2 is not needed when using SDP
- platform-native approaches reduce complexity significantly

### Practical conclusion
The final architecture uses:
- SDP for orchestration and execution
- GitHub Actions for deployment control
- configuration variables for environment behavior

Custom extensions should only be added when the platform does not provide the required functionality.

### Current position
I now have:
- production-ready SDP pipelines
- PR-based deployment model
- controlled validation behavior
- consistent and clean architecture

Remaining gaps:
- pipeline cleanup automation (PR pipelines)
- optional rejected-row persistence if needed
- further team workflow refinement