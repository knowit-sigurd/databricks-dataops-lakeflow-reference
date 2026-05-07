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

### From here I started with milestones instead of weekly/daily tasks

## 2026-04-29 Milestone 1 – SDP testing foundation

### What I observed
I extracted and tested transformation logic from the SDP pipelines.

The repo now has meaningful tests for customer and order transformation behavior, and the tests run successfully in the local/devcontainer setup.

After the changes, the Databricks pipelines still deployed and ran as expected.

### What I learned
SDP pipelines can stay platform-native while still having testable Python logic.

The important separation is:
- Databricks pipeline files define runtime behavior
- reusable transformation functions can be tested locally

This brings the test discipline from the v2 framework into the SDP approach without rebuilding the custom v2 runner.

### Practical conclusion
For SDP projects:
- keep pipeline definitions thin
- test transformation logic locally
- rely on Databricks for pipeline execution and observability

This gives a good balance between local development speed and platform-native runtime behavior.

### Current position
I now have:
- meaningful Spark-based tests in the SDP repo
- local validation of transformation behavior
- Databricks pipeline execution still working
- stronger confidence in the SDP repo as a client-ready reference

Remaining gaps:
- replace hardcoded inline data with file-based ingestion
- decide whether reusable logic should move into `src/`
- add rejected-row persistence if required

## 2026-04-30 Milestone 2 – File-based ingestion for SDP pipelines

### What I observed
I replaced hardcoded inline data in the SDP pipelines with file-based ingestion using CSV files stored in the repository.

- Bronze tables now read from external files instead of Python lists
- Pipelines ran successfully after updating permissions in Databricks
- Validation behavior remained unchanged:
  - dev / PR → invalid rows dropped
  - prod → pipeline fails on invalid data

Local testing in the devcontainer confirmed that Spark can read and process the files correctly.

### What I learned
Moving from inline data to file-based ingestion significantly improves realism and clarity.

I learned that:
- ingestion should be treated as a separate concern from transformation
- file-based inputs better represent real-world pipelines
- permissions in Unity Catalog are critical for successful pipeline execution
- local Spark testing can validate ingestion logic before deployment

I also reinforced that:
- SDP pipelines remain simple even when using external data sources
- transformation logic and validation behavior are unaffected by the ingestion method

### Practical conclusion
For SDP pipelines:
- avoid hardcoded data inside pipeline definitions
- use external files (or later, volumes) for ingestion
- keep bronze layer responsible for reading source data
- keep silver layer focused on validation and transformation

This improves both:
- realism for client demonstrations
- maintainability of the pipeline

### Current position
I now have:
- SDP pipelines reading from external CSV files
- realistic bronze ingestion layer
- working validation behavior across environments
- local and Databricks execution aligned

Remaining gaps:
- move from repo-based files to Unity Catalog volumes or external locations
- implement rejected/quarantine tables if required
- introduce schema evolution handling

## Milestone 3 – Rejected data as SDP extension

### What I observed
I added rejected (quarantine) tables to the SDP pipelines.

- invalid rows are now persisted with rejection reasons
- silver tables contain only valid rows
- SDP expectations still provide validation metrics

The pipelines now produce both:
- validated datasets
- rejected datasets

### What I learned
SDP expectations provide strong observability but do not persist invalid rows.

Rejected rows serve a different purpose:
- business traceability
- debugging and data correction

I learned that the best approach is not to replace SDP validation, but to extend it.

### Practical conclusion
Use a hybrid model:

- SDP expectations for validation and monitoring
- rejected tables for business-level visibility

This combines:
- platform-native simplicity
- practical data engineering needs

### Current position
I now have:
- rejected tables integrated into SDP pipelines
- validation metrics and row-level visibility
- a strong comparison with my v2 approach

Remaining gaps:
- add gold layer (aggregation)
- define cleanup strategy for rejected data
- evaluate how rejected data should be consumed

## Milestone 3 refinement – Cleaner rejected-row and production validation pattern

### What I observed
I removed the artificial quality gate tables and simplified the SDP validation pattern.

The pipeline now behaves differently by quality mode:
- dev / PR keeps silver clean and writes rejected rows
- prod fails directly on invalid silver rows using `expect_or_fail`

This made the pipeline DAG cleaner and easier to explain.

### What I learned
Rejected tables and expectations serve different purposes.

- expectations enforce data quality
- rejected tables support investigation and remediation

Using a separate quality gate table works, but it adds an artificial control-flow table that may make the DAG harder to understand.

### Practical conclusion
The cleaner pattern is:
- use SDP expectations for enforcement
- use rejected tables for visibility
- avoid quality gate tables unless there is a strict requirement to both fail production and persist rejected rows in the same failed run

### Current position
I now have:
- cleaner SDP pipeline DAGs
- rejected-row visibility in dev / PR
- fail-fast production behavior
- better separation between enforcement and investigation

Remaining gaps:
- decide whether rejected rows are required in production failed runs
- add gold layer
- define how rejected rows should be monitored or consumed

## 2026-05-01 Milestone 4 – Gold layer and cross-pipeline dependencies

### What I observed
I extended the SDP pipelines with a Gold layer and introduced cross-table dependencies.

- Added a `customer_order_summary` table combining customer and order data
- Moved from independent pipelines to a single medallion pipeline resource
- Databricks automatically derived execution order based on table dependencies
- Production pipelines now fail before Gold tables are updated when data quality checks fail in Silver

I also implemented file-based ingestion and automated data upload via GitHub Actions.

### What I learned
SDP handles dependencies through data relationships rather than explicit job orchestration.

By using `dlt.read`, Databricks builds the execution DAG automatically across Bronze, Silver, and Gold layers.

I also learned that:
- Gold tables should depend only on validated Silver tables
- data quality failures in upstream tables prevent downstream updates
- this is correct behavior for production pipelines
- bundle deployment may require destructive actions when architecture changes, and `--auto-approve` enables automated cleanup

### Practical conclusion
For SDP pipelines:
- define dependencies declaratively using `dlt.read`
- group related Bronze, Silver, and Gold tables into a single pipeline when they share dependencies
- ensure Gold tables represent business-facing outputs built on validated data
- use `databricks bundle plan` to review changes before deployment

This creates a clean, client-ready medallion architecture.

### Current position
I now have:
- full Bronze → Silver → Gold pipeline
- cross-table dependencies managed by SDP
- file-based ingestion integrated with deployment
- automated deployment with controlled destructive updates

Remaining gaps:
- define strategy for rejected data handling in production
- implement PR pipeline cleanup automation
- refine deployment approval strategy for production environments

## 2026-05-02 Milestone 5 – PR pipeline cleanup automation

### What I observed
I implemented automated cleanup of PR pipelines using GitHub Actions.

- pipelines are created per PR
- pipelines are removed automatically when the PR is closed
- legacy manually created pipelines had to be removed separately

The cleanup workflow uses `databricks bundle destroy` with the same deployment suffix used during pipeline creation.

### What I learned
PR-based pipelines require full lifecycle management, not just deployment.

Without cleanup:
- pipelines accumulate
- workspace becomes cluttered
- operational clarity is reduced

I also learned that:
- bundle-managed pipelines should be the only pipelines in the workspace
- cleanup must align with deployment naming
- `--auto-approve` is acceptable for temporary resources but requires caution

### Practical conclusion
For SDP pipelines:
- use PR-based deployment for validation
- automate cleanup on PR close
- ensure deployment and cleanup use consistent naming

This ensures a clean, predictable workspace and a complete pipeline lifecycle.

### Current position
I now have:
- PR-based pipeline deployment
- automated cleanup of temporary pipelines
- consistent naming and lifecycle management
- clean workspace after PR closure

Remaining gaps:
- optional cleanup of schemas or temporary data
- further hardening of production deployment
- monitoring and alerting integration

## Milestone 6 — Explicit bronze schemas and cleanup branch guard

Two correctness fixes that matter for client credibility.

**inferSchema removed:** Replaced `.option("inferSchema", True)` in both bronze
tables with explicit `StructType` declarations. inferSchema is non-deterministic
and slow — it reads the whole file before the pipeline logic runs. Explicit schema
is the contract between ingestion and everything downstream. Declared `LongType`
for all IDs, `DoubleType` for amount. Known gap: `DecimalType(10,2)` is more
correct for monetary values; left as `DoubleType` for simplicity in this reference.

**Cleanup guard added:** Added `branches: [main]` to the `pull_request` trigger in
`cleanup-pr.yml`. The deploy workflow only fires for PRs targeting `main`, so the
cleanup must be symmetric. Without this guard, closing a PR against any branch
triggers `bundle destroy` on a pipeline that was never deployed.

Pattern: every CI workflow that has a deploy step needs a matching cleanup — and
both must share the same branch scope.


## 2026-05-03 Milestone 7 Item 1 — Removed vestigial test target
The test target in databricks.yml was identical to dev: same workspace, same schema, no behavioral difference. Keeping it implied a staging environment that didn't exist. Removed it from databricks.yml, deploy.yml, and upload_data.sh. Real projects either have a true staging workspace (separate UC catalog/workspace) or they don't — they don't pretend.

## Milestone 7 Item 2 — Removed -t flag from databricks fs cp (incorrect — see Item 3)
Initial diagnosis: -t "$TARGET" was listed as an invalid flag for databricks fs cp. Removed from both cp calls. This turned out to be wrong — see Item 3.

## Milestone 7 Item 3 — Hotfix: restore -t flag to databricks fs cp
Prod deploy broke immediately after Item 2 with "Error: please specify target". Root cause: databricks fs cp, when run inside a directory containing databricks.yml, uses the bundle configuration to resolve which workspace host to connect to. Without -t <target>, the CLI cannot determine the workspace and fails. The -t flag is not a bundle-only flag — it is valid and required for any CLI command that needs workspace context when multiple targets are defined. The $VOLUME path routes data to the right location, but -t tells the CLI which workspace that path lives in. Restored -t "$TARGET" to both cp calls. Real lesson: removing a flag because it "looks wrong" without testing against the actual deployment path is a risk. In CI, a broken upload step can silently pass if the error is swallowed — always confirm data seeding steps independently.

## Milestone 7 Item 4 — PR schema isolation
All PR deploys previously wrote to dataops_lab.sdp_dev.*, meaning concurrent PRs shared state and could overwrite each other's tables. Fixed by emitting target_schema=sdp_pr_<n> from the CI context resolution step and passing it as a bundle variable. The target_schema variable was already wired into databricks.yml from M6 — CI was just never setting it. Added schema drop (databricks schemas delete) to cleanup-pr.yml so schemas don't accumulate. This is the prerequisite for M8 row-count assertions to be meaningful.

## Milestone 7 Item 5 — Source path isolation documented as deliberate choice
All PR deployments share /Volumes/dataops_lab/sdp_dev/raw. Documented this as intentional: source data is static CSV fixtures, contention is on outputs not inputs, and output isolation (schema-per-PR from Item 4) is what matters. Also documented that upload_data.sh prod seeding sdp_prod/raw during deploy is a demo convenience — in a real project the production volume would be populated by Auto Loader, not CI scripts. Updated architecture.md (environment table, deployment model block, Known Limitations) and README.md (environment table, CI/CD table) to reflect the current honest state of the repo. Real lesson: stating what you deliberately did NOT do is as important as stating what you did.

## Milestone 7 Item 6 — README honest promotion model and known limitations
Fixed the "How it works" promotion description to show sdp_pr_<n> and sdp_prod instead of dev. Updated the Cleanup section to include schema drop. Replaced the stale "Final milestone status" block with a Known Limitations section. Real lesson: a README that describes the state from two milestones ago is worse than no README — it actively misleads readers about what the repo does.

## Milestone 8 Item 1 — Pipeline execution in CI
Added `databricks bundle run` after `bundle deploy` for PR events. CI now executes the pipeline and fails the PR if the pipeline update fails. Before this, CI proved only that the bundle config deployed — not that the pipeline ran. `--refresh-all` forces a clean read of fixture data each run. Scoped to PR events only: prod pipeline is managed by the deployment itself. `bundle validate`, `bundle plan`, and `bundle deploy` were already in place; `bundle run` is the step that closes the gap between "config is valid" and "pipeline actually works". Real lesson: a deploy step that never executes the thing it deploys is not CI — it is just syntax checking.

## Milestone 8 Item 2 — Row count assertions after pipeline run
Added `scripts/validate_counts.py` which queries all 7 tables via Databricks SDK statement execution API and asserts expected counts from the fixture CSVs. Called from CI after `bundle run`. A pipeline that runs but produces wrong output now fails the PR. Expected counts: customers_bronze=3, customers_silver=2 (1 rejected), orders_bronze=4, orders_silver=3 (1 rejected), customer_order_summary=2 (customer 99 has no silver match). Service principal requires explicit "Can use" permission on the SQL warehouse — not granted by default even for workspace admins. Real lesson: exit code 0 from a pipeline run proves execution completed, not that the data is correct — row counts are the minimum bar for data correctness.

## Milestone 9 — Rules as single source of truth / expectation bypass fix

**What I built:** Defined `CUSTOMER_RULES` and `ORDER_RULES` as dicts in `customers.py` / `orders.py`. Pipeline decorators, rejected-row logic, and tests all derive from the same dict. Removed the `valid_customers` / `valid_orders` pre-filter bypass that was silencing the expectation engine in dev/PR mode.

**The problem it fixed:** `expect_or_drop` was never seeing invalid rows — they were filtered before the expectation ran. DLT reported 100% pass rate on clean data. Quality metrics were meaningless.

**Key insight:** DLT expectation metrics are the observable signal for data quality in a SDP pipeline. If you pre-filter before the expectation, you destroy that signal. The expectation engine must see the invalid rows to count and route them correctly.

**Rejected-row derivation:** `~F.expr(sql)` inverts a SQL condition into a filter for the rejected table. `CUSTOMER_RULES.items()` drives both the `@expect_fn` decorators and the rejection filter — one change propagates everywhere.

**Orders rules expanded:** Added `valid_order_id` and `valid_customer_id` to `ORDER_RULES`, bringing orders to parity with customers. No fixture rows have null order_id or customer_id, so row counts in CI are unaffected.

**Scope boundary held:** Rules as plain dicts with string values. No `Rule` dataclass, no generic `validate_dataframe` helper, no YAML loading. Adding abstraction here is the v2 trap.

## Milestone 10 — Schema evolution policy and column-add demo

**What I built:** Added `customer_email` to `customers.csv` and `CUSTOMERS_SCHEMA` in `customer_pipeline.py`. Traced it deliberately through the three layers: bronze captures it via the explicit `StructType` declaration; silver promotes it automatically because `enrich_customers` uses `withColumn` (not `select`); gold excludes it because the explicit `.select()` in `build_customer_order_summary` does not name it. Documented the policy in `architecture.md`. Added two tests: one asserting `customer_email` is present in silver output, one asserting it is absent from gold.

**The policy:** Schema changes fall into two categories. Additive nullable columns are safe — declare them in bronze, let them flow to silver, promote to gold only when there is a business output requirement. Everything else (rename, drop, type change) is a breaking change that requires explicit migration. This distinction is what makes a schema change reviewable in a PR rather than a production incident.

**The architectural insight:** The existing code already enforced this correctly without knowing it. Bronze `StructType` is the ingest contract — columns not declared there are silently dropped and never reach silver or gold. Gold's explicit `.select()` is the final promotion gate — new silver columns cannot appear in gold output unless someone deliberately adds them. The milestone made these two invariants visible and machine-verifiable through tests and documentation.

**Validation:** Verified in the Databricks Catalog UI that `customer_email` appears in `customers_bronze` and `customers_silver`, and is absent from `customer_order_summary`. CI passed with all row counts unchanged — adding a column does not change row counts.

**Permissions note:** Browsing PR schema tables in the Catalog UI requires `USE SCHEMA` and `SELECT` granted at the catalog level. Granting on the catalog propagates to all current and future schemas, including dynamically created `sdp_pr_<n>` schemas. One-time setup; in production this would be granted to a group rather than an individual.

**Scope boundary held:** No schema registry, no Auto Loader schema evolution mode, no generic column promotion framework. The `StructType` and `.select()` that were already in the code are the right primitives. Renamed/dropped/type-change patterns are documented in `architecture.md` as breaking changes, not implemented.

## Milestone 11 — Gold join policy and dead standardization fix

Two correctness gaps closed.

**Gold join changed from inner to left.** An inner join silently excludes customers who have not yet placed orders — they pass silver validation but disappear from reporting. The left join with coalesce (`order_count=0`, `total_amount=0.0`) makes the behaviour unambiguous. The decision is documented in `architecture.md` and machine-verified by a test that constructs a customer with no orders and asserts the expected zero counts.

**`standardize_customers` was defined, tested, and never called.** The trim on `customer_name` and `city` was flowing through the test suite cleanly while the pipeline was shipping untrimmed data. Wired it into `customers_silver` by chaining `standardize_customers` before `enrich_customers` in the silver table function. Real lesson: a unit test on an isolated function proves the function works — it does not prove the function is called.

## Milestone 12 — DecimalType for amount

Changed `ORDERS_SCHEMA` `amount` field from `DoubleType` to `DecimalType(10,2)`. `DoubleType` is IEEE 754 floating point — rounding error accumulates across arithmetic operations on financial values. `DecimalType` is exact. This was documented as a known gap since M6.

The explicit `StructType` declaration from M6 is what makes this a safe, one-line change: the type contract is declared in one place, enforced at ingest, and visible in the Unity Catalog schema. Without explicit schema, this change would require verifying every data path. With it, it is a single reviewed line in a PR.

Verified in Databricks Catalog Explorer: `amount` column type shows as `DECIMAL(10,2)` in both `orders_bronze` and `orders_silver`.

## 2026-05-05 Milestone 13 — Production approval gate

**What I built:** Split the single `deploy` job into `deploy-pr` (PR and `workflow_dispatch` events, no gate) and `deploy-prod` (push to main, pauses for manual approval). Wired `environment: production` onto `deploy-prod` with a required reviewer in GitHub repo settings. Received the approval email, clicked through, and confirmed prod deployed cleanly end-to-end.

**Also cleaned up:** `databricks-dev-container/` was tracked as a git commit reference (mode `160000`) — a broken gitlink left over from a nested repo that had its own `.git` directory. Files were never pushed (only the commit SHA was stored), but it showed as a broken submodule on GitHub. Removed from the index with `git rm --cached` and added to `.gitignore`.

**Key insight:** `environment: production` on a GitHub Actions job is the minimum viable prod gate. It pauses execution, sends a notification email to required reviewers, and writes an auditable approval record — no custom scripting needed. The gate sits between `push to main` and actual deployment, so merge does not equal deploy.

**Databricks recommendation noted:** `bundle validate` on the prod target recommended setting `workspace.root_path` explicitly to guarantee only one bundle copy is deployed per identity. Noted as a future improvement; not blocking for a single-operator reference lab.

**GitHub plan prerequisite:** Required reviewer environments require a public repo or a paid plan. Made the repo public as part of this milestone — appropriate for a client reference architecture that contains no hardcoded credentials. Confirmed no sensitive content in tracked files before switching visibility.
## 2026-05-05 Milestone 14 — Monitoring and alerting (documented, not implemented)

Evaluated push-based alerting as a milestone. Decided not to implement it.

**What the repo already covers:** GitHub emails on CI/job failure, the production approval gate creates a mandatory human review before prod runs, Databricks pipeline UI shows execution history and expectation metrics per update, and `validate_counts.py` asserts row correctness on every PR.

**What is genuinely missing:** A prod pipeline triggered outside CI (scheduled run, manual rerun) can fail without anyone knowing. The platform fix is a Databricks notification destination wired to `on-update-failure` — supports Slack, PagerDuty, etc. — but this is workspace admin configuration, not something managed in `databricks.yml` or CI.

**Why not implemented:** This is a single-operator reference lab with static fixture data. Push notifications add operational overhead before there is an operational need. The right time to introduce alerting is when pipelines run on a schedule, source data changes, and consumers need to know when data is stale. Documented the gap and production patterns in `architecture.md` instead.

**Key insight:** Monitoring is an architectural question before it is an implementation question. The right answer depends on who is watching, what they need to know, and how quickly. Adding Slack webhooks to a reference lab answers the "how" before the "why" is established.

**Also added:** Branch protection rules on `main` — requires PR + `CI / ci` passing before merge. Direct pushes blocked for all users including admins. `deploy-pr` runs automatically but is not a required gate (too slow for docs-only changes).

## Post-M9 hotfix — PR schema cleanup was silently failing

After merging M9, stale schemas `sdp_pr_36`, `sdp_pr_37`, `sdp_pr_38` were still visible in the catalog UI. Two bugs in `cleanup-pr.yml`:

1. `databricks schemas delete` was called without `--force` — the CLI refuses to drop a non-empty schema without it, and `|| true` swallowed the error silently so CI showed green.
2. The command was missing `-t dev` — inside a bundle directory the CLI requires a target to resolve the workspace host, same as `databricks fs cp` (re-learned from M7).

Fixed both flags in the cleanup workflow and deleted the three stale schemas manually. Real lesson: `|| true` on a cleanup step hides failures permanently — if cleanup is load-bearing, check it actually ran by inspecting the catalog after the first real PR close.

## 2026-05-05 Post-M14 hotfix — deploy-pr added as required status check

**What I observed:** `bundle run` failed mid-execution with "The specified pipeline was not found." The pipeline had reached PLANNING state. GitHub fires the `pull_request: closed` event immediately on merge, triggering `cleanup-pr.yml` concurrently with the still-running `deploy-pr` job. `bundle destroy` deleted the pipeline while `bundle run` was actively polling it.

**What I learned:** GitHub workflow runs for different events on the same PR execute concurrently by default. There is no built-in ordering guarantee between a `synchronize`-triggered deploy-pr that is still running and a `closed`-triggered cleanup that starts at merge time. The race window exists whenever the PR is merged before deploy-pr finishes.

**What I considered:** GitHub Actions `concurrency` groups — cancelling deploy-pr when cleanup starts for the same PR number. Rejected: this patches the symptom at the workflow layer without addressing the design question underneath it. If a deployment is still running, the PR should not be mergeable.

**What I did:** Added `Deploy SDP Pipelines / deploy-pr` as a required status check alongside `CI / ci` in the branch protection rules on main. GitHub now blocks the merge button until deploy-pr has completed successfully. The cleanup workflow then runs against an idle, finished deployment — no race is possible.

**Practical conclusion:** Required status checks are the correct architectural fix for workflow race conditions caused by concurrent event handling. Concurrency groups are a workaround for a problem that should not exist. Every PR now must wait for the full Databricks pipeline run (~5 min) before merge is allowed — this is the right tradeoff for a repo where deploy-pr is the primary correctness signal.

**Current position:** `main` requires both `CI / ci` (lint + tests) and `Deploy SDP Pipelines / deploy-pr` (deploy + pipeline run + row counts) to pass before merge. Direct pushes blocked including admins. `architecture.md` updated to reflect both checks as required gates.


## M15: DAB State Isolation (2026-05-05)

**What I observed:** With no `root_path` set, all PR deploys wrote to the same bundle state file on the workspace. Closing any PR would destroy whichever pipeline was last deployed, not the one that PR owned. The problem was silent — `bundle destroy` succeeded, just on the wrong target.

**What I learned:** DAB's default state path is shared across all deployments to the same target. `root_path` is the mechanism for isolating it. Without it, parallel PRs are mutually destructive at cleanup time, regardless of how well the pipeline names and schemas are isolated.

**Practical conclusion:** Every multi-branch Databricks bundle needs `root_path` set to a per-deployment path from day one. It is not optional once a second developer or a second open PR exists.

**What I observed (during implementation):** Two additional constraints surfaced during validation. First, `mode: development` enforces that `root_path` starts with `~/` or contains the current username — `/Shared/` was rejected with an explicit error. Second, `/Workspace/Shared/` is world-writable in this workspace, meaning any user could overwrite prod bundle state. Both issues pointed to the same fix: use `~/` for both targets. A third minor issue: hardcoding `/prod` as the suffix on the prod target produced a double `prod/prod` path since `${bundle.target}` already resolves to `prod` — removed the trailing literal.

**Current position:** Each deployment writes state under `~/.bundle/dataops-lab-sdp/<target>/`. The `dev` target appends `${var.deployment_suffix}`, resolving to `~/.bundle/dataops-lab-sdp/dev/pr_<n>` in CI and `~/.bundle/dataops-lab-sdp/dev/dev` locally. The `prod` target resolves to `~/.bundle/dataops-lab-sdp/prod`. In both cases `~` expands to the deploying identity's home — the service principal in CI, the user locally. CLI version is pinned to `>= 0.298.0, < 1.0.0`. The vestigial `[tool.setuptools.packages.find]` block is removed from `pyproject.toml`.

**Remaining gaps:** No two-PR isolation test has been run in CI yet — the two-PR proof described in the acceptance criterion requires opening two PRs simultaneously after this merges.

## M16: CI Toolchain Hygiene (2026-05-05)

**What I observed:** `uv.lock` existed but contained only the project entry with no packages. CI was running `uv pip install -r requirements.txt` with four unpinned packages, bypassing the lockfile entirely. Two deploy steps used bare `pip install databricks-sdk` with no version constraint.

**What I learned:** A lockfile only works if the dependency declarations live in `pyproject.toml` — uv has nothing to lock if dependencies are only in `requirements.txt`. `uv sync --frozen` is the correct CI primitive: it fails if the lockfile is absent or stale, so lockfile drift becomes a visible error rather than a silent version drift.

**Practical conclusion:** `requirements.txt` is a legacy artifact when using uv. All dependencies belong in `pyproject.toml` under `[dependency-groups]`. Delete `requirements.txt` once the migration is done — keeping both creates a two-source-of-truth problem.

**Current position:** All Python dependencies declared in `pyproject.toml` under `[dependency-groups] dev`. `uv.lock` contains pinned transitive dependencies. CI installs via `uv sync --frozen`. Databricks CLI pinned to `v0.298.0` in both deploy workflows. `requirements.txt` removed.

**Remaining gaps:** uv installer itself is not pinned — accepted tradeoff. CLI pin is a URL pin to a specific tag, not a hash — acceptable for a reference repo.


## M17: Code Credibility Cleanup (2026-05-05)

**What I observed:** `customer_key` was an alias of `customer_id` added in `enrich_customers` with no downstream consumer — it was dropped at the gold join. The rejection logic used a `when().when()` chain (equivalent to SQL `CASE WHEN`), which stops at the first matching condition. A row failing both `valid_customer_id` and `valid_customer_name` produced `rejection_reason = "VALID_CUSTOMER_ID"` only.

**What I learned:** `CASE WHEN` semantics are first-match-wins. Collecting all failing reasons requires evaluating each rule independently and combining the results. `concat_ws` with per-rule `when` expressions is the idiomatic Spark fix — it evaluates every condition, and nulls (passing rules) are silently excluded from the concatenation.

**Practical conclusion:** Rejection tables are only useful for diagnosis if they capture the complete failure picture. First-match-only rejection reason forces analysts to fix and reprocess repeatedly instead of fixing all violations at once.

**Current position:** `customer_key` removed from `enrich_customers`. Both `rejected_customers` and `rejected_orders` now produce comma-separated `rejection_reason` values for multi-rule failures. Tests cover the multi-reason case explicitly.

**Remaining gaps:** `rejection_reason` is a string, not an array — filtering in SQL requires `array_contains(split(...))`. Acceptable for now; a schema change to array type would be M-level work with a clear consumer need.

## M18: Observability Queries and Prod Data Fix (2026-05-05, corrected 2026-05-06)

**What I observed (initial failures and actual causes):** Three failures when first attempting `event_log()`:

1. `event_log('<pipeline_id>')` on a SQL warehouse → `PERMISSION_DENIED`. Error message said "use a SHARED cluster instead." Retried on a shared cluster, a serverless notebook, and a serverless SQL warehouse — identical error on all three. The cluster type message was a red herring.
2. `dataops_lab.sdp_dev.event_log` → `TABLE_OR_VIEW_NOT_FOUND` — the event log is not materialized as a schema table.
3. `system.lakeflow.pipeline_events` → `TABLE_OR_VIEW_NOT_FOUND`.

**What the actual causes were:**

For `event_log()`: the prod pipeline (`prod_medallion_pipeline`) was deployed by the CI service principal, which became the pipeline owner. `event_log()` requires pipeline ownership — `CAN_VIEW` is not sufficient. Confirmed by granting `CAN_VIEW` via the CLI; PERMISSION_DENIED persisted. Then tested `event_log()` on the dev pipeline, which is owned by my personal account — it worked immediately on a serverless SQL warehouse.

For `system.lakeflow`: the schema exists in the metastore but requires `USE SCHEMA` granted by an account admin. Workspace admin is insufficient — granting system schema privileges requires account-level access. The workspace is managed by Knowit (not Databricks) — the initial assumption that this was a Databricks-managed training workspace was wrong.

**What I learned:** `event_log()` is accessible in this workspace. The access boundary is pipeline ownership, not workspace type. `CAN_VIEW` on a pipeline is not the same as ownership for this TVF. The "Assigned cluster" error that appeared on every compute type (including shared cluster and serverless) was a misleading error code — the real failure was a permission check on the pipeline identity, not a compute mode check.

**Practical conclusion:** In CI/CD workflows where the service principal deploys pipelines, the service principal becomes the pipeline owner. Human users who need to query `event_log()` must either own the pipeline themselves (local dev deploys) or have the service principal explicitly grant access — and even then, `CAN_VIEW` may not be sufficient. The clean solution for a multi-operator team is to deploy with a service principal and grant that SP's event log access to a dedicated monitoring service account, or use `system.lakeflow` once account admin grants are in place.

**What I observed (prod data fix):** The prod fixture data was a copy of dev data, which contains intentionally bad rows. In dev, `quality_mode=drop` silently routes those rows to rejection tables and the pipeline completes. In prod, `quality_mode=fail` aborts the pipeline on the first invalid row — bronze and rejected tables were created, silver and gold were never written. Fix: separate `data/prod/` fixture files with clean data. `upload_data.sh` now uses `data/prod/` for the prod target and `data/` for dev.

**Current position:** Four SQL files in `sql/`:
- `event_log_runs.sql` — update history per pipeline run (start time, end time, duration, final state)
- `event_log_flow_progress.sql` — per-table row counts and dropped records per update
- `rejection_summary.sql` — rejected row counts grouped by rule and entity (rejection tables, no pipeline ID needed)
- `rejected_rows.sql` — individual rejected rows with business-level rejection reasons

The `event_log()` queries use the dev pipeline ID as the example. Prod pipeline event log is inaccessible — the CI service principal is the owner. Prod fixture data in `data/prod/` is clean. Dev fixture data unchanged, bad rows preserved for rejection demonstration.

**Remaining gaps:** `system.lakeflow.pipeline_events` requires account admin to grant `USE SCHEMA` on `system.lakeflow`. Until that grant is in place, cross-pipeline observability is unavailable. In a client deployment with account admin access, `system.lakeflow` is the right foundation — it surfaces the same data as `event_log()` across all pipelines without requiring per-pipeline ownership.

## M19: Production Hardening (2026-05-06)

**What I observed:** `run_as` in DAB applies to jobs, not pipelines. SDP/Lakeflow pipelines have no `run_as` field. The pipeline owner is the identity that ran `databricks bundle deploy` — in CI, that is the service principal. There is no mechanism to specify a running identity separate from the owner.

**What I learned:** The git.branch constraint I planned was already enforced at the GitHub Actions layer (`if: github.ref_name == 'main'` on the deploy-prod job). The `bundle.git.branch: main` annotation in `databricks.yml` makes the intent explicit in the config itself and surfaces in `bundle validate` output — but it does not block a local `bundle deploy -t prod` from a feature branch. In a single-operator lab that is acceptable. In a team environment, enforcement belongs in CI/CD, not in the bundle config, because DAB has no constraint or assert mechanism.

**What I observed (permissions):** Pipeline ACLs in `databricks.yml` are workspace-level — who can see and trigger the pipeline in the Workflows UI. This is separate from Unity Catalog grants on the output tables. Setting one does not set the other.

**Practical conclusion:** For pipeline identity, the only safe pattern is deploying with a dedicated service principal. If a personal account deploys, that account becomes the pipeline owner. When the person leaves, the ownership is orphaned until the next deploy.

**Current position:** `bundle.git.branch: main` declared in `databricks.yml`. Pipeline permissions block declared for prod target. Architecture.md explains the pipeline identity model and the distinction between workspace ACLs and UC table grants. Git branch enforcement remains at the GitHub Actions layer.

**Remaining gaps:** Workspace groups (`data-engineers`) are not provisioned in this training workspace. In a client deployment, pipeline permissions would reference group names, not user emails. Group provisioning is an IT/identity-provider concern outside the scope of this reference.

## M20: Client Demo Guide (2026-05-06)

**What I built:** Two walkthrough documents — `docs/demo-guide.md` (30-minute technical walkthrough for a data engineering lead) and `docs/demo-guide-exec.md` (10-minute executive overview for a decision-maker). Both are structured around what to show, what to say, and expected questions.

**What I learned:** Writing the demo guide forced prioritisation. Not every feature belongs in a 30-minute demo. The exercise revealed two places where architecture decisions were implicit in the code but not stated as talking points anywhere — the `dlt.read()` dependency model replacing explicit job sequencing, and the two-layer deployment identity model (workspace ACL vs UC table grants). Both became explicit "what to say" notes in the guide.

**Practical conclusion:** A reference repo without a demo guide is a portfolio piece. A reference repo with a demo guide is a sales tool. The guide is the difference between "here is something I built" and "here is how we would deliver this for you." The exec guide serves a different function — it reframes technical decisions as business outcomes without requiring the audience to understand YAML or Python.

**Current position:** `docs/demo-guide.md` covers six sections: architecture overview, code structure and rules, environment and deployment model, pipeline run and event log, data quality queries, CI/CD and promotion model. `docs/demo-guide-exec.md` covers four sections: the problem with custom frameworks, quality enforcement, controlled production deployment, and effort/maintenance. Both include expected client questions per section.

**Remaining gaps:** The guides assume the workspace is already provisioned and pipelines are deployed. First-time setup — catalog creation, volume provisioning, service principal configuration, GitHub secrets — is not covered. That is a separate onboarding document appropriate when handing the repo to a new team.


## 2026-05-06 — M21: Deployment safety cleanup

**What I observed**
- `cleanup-pr.yml` was installing the Databricks CLI from `setup-cli/main` (HEAD), meaning each PR cleanup could silently use a different CLI version than the one validated in deploy.yml.
- `|| true` on the schema delete step suppressed all errors, including genuine failures unrelated to "schema not found". When the schema was actually present and successfully deleted, the step exited 0 silently — confirming the new error-handling path only activates on failure.
- `databricks.yml` prod permissions referenced a personal email address. DAB had deployed it as CAN_MANAGE because a higher manual grant already existed, but the config expressed the wrong pattern.
- Replacing the personal email with `group_name: data-engineers` passed `bundle validate` but failed at deploy time with `Principal: GroupName(data-engineers) does not exist`. `bundle validate` does not check whether principals exist — that check happens in Terraform during `bundle deploy`.
- `bundle.git.branch` at bundle level is metadata only. Enforcement requires `git.branch` under the specific target.
- `workflow_dispatch` in deploy.yml executes only `bundle deploy` — the three subsequent steps (stop pipeline, run pipeline, assert counts) are gated on `github.event_name == 'pull_request'` and silently skip on manual dispatch.

**What I learned**
- Unpinned tool versions in CI are a latent risk even when things appear to work. Version drift is invisible until a breaking change ships.
- `|| true` is appropriate only when an error genuinely does not matter. On a load-bearing cleanup step it converts silent failures into stale state.
- `bundle validate` passes for non-existent principals. Permission errors surface only at deploy time via Terraform — there is no pre-flight check for group or user existence.
- `git.branch` placement matters: bundle level = documentation, target level = DAB enforcement.

**Practical conclusion**
- Pin all CLI versions in all workflows to the same version used in the last known-good deploy.
- Replace `|| true` with explicit not-found detection on any cleanup step that is load-bearing.
- If the target workspace has no provisioned groups, remove the permissions block from the bundle entirely and document that access is granted manually. A permissions block referencing a non-existent group fails silently at validate and loudly at deploy.

**Current position**
- `cleanup-pr.yml` pins CLI to `v0.298.0` and fails explicitly on unexpected schema delete errors.
- `databricks.yml` prod permissions block removed entirely — no group exists in this workspace to reference. Access to the prod pipeline is granted manually via the UI.
- `git.branch: main` is now present under `targets.prod` as well as at bundle level.
- SQL observability files use `<your-dev-pipeline-id>` placeholders.
- `NO_CITIES` in `common.py` has a one-line comment.

**Remaining gaps**
- Prod pipeline permissions are not managed by the bundle. In a client workspace with provisioned groups, the permissions block should reference a group name. Documented in M23 (setup.md).
- Prod has no automated row count assertion. If the pipeline was previously run against an empty volume, a subsequent incremental run silently skips reprocessing gold — DLT streaming state considers it up to date. Discovered during M21 validation: `customers_silver` had 3 rows, `orders_silver` had 4 rows, `customer_order_summary` had 0. Full refresh resolved it. PR deployments catch this via `validate_counts.py`; prod does not.
- Two-PR isolation proof (M22) not yet run.


## 2026-05-07 — M22: Two-PR isolation proof

**What I observed**
- Opened two concurrent PRs (pr_66, pr_67) against main. Both `deploy-pr` jobs completed successfully and independently without any manual coordination.
- Databricks workspace showed two distinct pipelines: `pr_66_medallion_pipeline` and `pr_67_medallion_pipeline`, each with a separate pipeline ID.
- Catalog `dataops_lab` showed two distinct schemas: `sdp_pr_66` and `sdp_pr_67`, each with the full medallion table set (customers_bronze, customers_silver, customers_rejected, orders_bronze, orders_silver, orders_rejected, customer_order_summary). No cross-contamination between schemas.
- Databricks workspace filesystem showed two separate DAB root paths: `.bundle/dataops-lab-sdp/dev/pr_66` and `.bundle/dataops-lab-sdp/dev/pr_67`.
- Closing pr_66 triggered `cleanup-pr.yml`. The cleanup log confirmed `bundle destroy` targeted `/Workspace/Users/.../.bundle/dataops-lab-sdp/dev/pr_66` explicitly and deleted `pr_66_medallion_pipeline`. `sdp_pr_67` and `pr_67_medallion_pipeline` were unaffected.
- Closing pr_67 triggered `cleanup-pr.yml` for the remaining resources. Workspace clean after both closures.
- Neither proof PR was merged to main. The branches were throwaway vehicles; the only deliverable from M22 to main is this documentation.

**What I learned**
- The `root_path` isolation pattern in `databricks.yml` (M15) works end-to-end. It is not just a configuration claim — concurrent PRs genuinely cannot clobber each other's bundle state, pipelines, or output schemas.
- The cleanup hardening from M21 (`--force`, grep-based not-found handling, pinned CLI version) made teardown safe and non-destructive to sibling PRs. A cleanup bug here would have been easy to miss without running the proof.
- `databricks pipelines list` is not a valid CLI command in v0.298.0. UI verification was sufficient — the Databricks UI showed pipeline list, catalog schema tree, and workspace filesystem state clearly enough to confirm all pass conditions without CLI commands.

**Practical conclusion**
- The isolation model is verified by live execution. When demonstrating to clients: two engineers can push PRs simultaneously with no shared state risk. The workspace filesystem, catalog, and pipeline list are all visually inspectable in the UI — no CLI scripting needed for the demo.

**Current position**
- PR pipeline isolation verified by live concurrent execution. `demo-guide.md` wording updated to reflect verified status with specific PR numbers as evidence.

**Remaining gaps**
- Input isolation (raw volume `/Volumes/dataops_lab/sdp_dev/raw`) is not isolated by design — all PR pipelines share the same static fixture input. This is intentional and the correct approach for a reference repo with shared fixture data.
- `validate_counts.py` has hardcoded expected row counts tightly coupled to fixture files. Any fixture change requires a matching code change. Flagged for a future cleanup milestone.


## 2026-05-07 — M23: Setup.md and Runbook.md

**What I built**
Two operational documents: `docs/setup.md` (first-time workspace provisioning — service principal,
Unity Catalog, GitHub secrets, branch protection, devcontainer setup) and `docs/runbook.md`
(day-to-day operations — prod trigger, full refresh decision, validate_counts failures, manual
PR cleanup, event log queries, CLI version pinning). Both linked from `README.md`.

**What I observed**
Writing `setup.md` revealed that two values in `.devcontainer/devcontainer.json` are hardcoded
to the original author's identity: `DATABRICKS_CONFIG_PROFILE` and `DATABRICKS_WAREHOUSE_ID`.
A new engineer opening the container without updating these values would get auth failures with
no obvious cause — neither value is documented anywhere else in the repo.

**What I learned**
A repo is not ready to hand over until someone who has never seen it can provision and operate
it from the documentation alone. Writing `setup.md` as if you were that person surfaces
assumptions that are invisible from inside the working environment. The devcontainer grants are
a good example: they work seamlessly once configured, which is precisely why no one documents
how to configure them.

**Practical conclusion**
Setup documentation should be written before handover, not after the first time a new engineer
gets stuck. The cost of writing it while the context is fresh is low. The cost of reconstructing
it six months later — or leaving a new engineer to reverse-engineer it from the devcontainer.json
— is high.

**Current position**
`docs/setup.md` covers: service principal creation, UC grants, GitHub secrets, production
environment, branch protection, devcontainer setup, and first deploy. `docs/runbook.md` covers:
prod pipeline trigger, full refresh decision, validate_counts failure diagnosis, manual PR
cleanup, manual dev redeploy, event log queries, and CLI version pinning.

**Remaining gaps**
`devcontainer.json` still has hardcoded personal values. Documented in `setup.md` as a manual
update step. Making them configurable via `${localEnv:...}` would remove the step entirely —
candidate for a future cleanup if the repo is handed to a team.


