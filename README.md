# databricks-dataops-lab-v2

A practical **Databricks DataOps learning and reference project**, evolving toward a reusable, client-ready DataOps framework.

---

## Project status (v2 baseline)

This version of the project represents a completed learning phase focused on:

- custom DataOps pipeline framework
- CI/CD with GitHub Actions
- promotion model (dev/test/prod)
- audit logging and monitoring
- multi-pipeline support

This is kept as a reference implementation.

Next phase (v3) explores Databricks-native patterns using:
- Lakeflow Spark Declarative Pipelines
- serverless workflows
- platform-native orchestration

---

## Purpose

This repository is used to:

* build hands-on experience with Databricks and Unity Catalog
* translate traditional DW/DataOps practices into cloud-native patterns
* establish a **practical, testable DataOps workflow**
* evolve into a reusable project template for client work

---

## Architecture (high-level)

The project follows a **Python-first, Databricks-native design**:

* Business logic lives in `src/`
* Notebooks are thin execution entrypoints
* Data is organized using **bronze / silver**
* Unity Catalog tables are the primary interface
* Delta Lake is used for all storage

👉 See `docs/architecture.md` for full details

---

## Repository structure

```text
src/my_project/        → Python business logic
notebooks/             → Thin Databricks entrypoints
tests/                 → Local pytest + Spark tests
docs/                  → Architecture and learning log
databricks/            → Deployment and bundle resources
```

---

## Working approach

This project follows a **local-first DataOps workflow**:

1. Develop locally in VS Code
2. Validate with:

   * `ruff format --check`
   * `ruff check`
   * `pytest`
3. Commit and push to feature branch
4. Create and merge PR to `main`
5. Pull latest in Databricks Git folder
6. Execute and validate in Databricks

---

## Data model

* Catalog: `workspace`
* Schema: `dataops_lab_<environment>`

### Tables

* `bronze_customers` → raw snapshot
* `silver_customers` → validated contract layer
* `rejected_customers` → invalid rows with reason
* `pipeline_run_log` → audit trail

---

## Pipeline execution pattern

The project uses a reusable execution model:

* `run_pipeline(...)` → handles logging, audit, error handling
* pipeline-specific functions → define transformation logic

This separates:

* execution concerns
* business logic

---

## Validation and data quality

Two modes are supported:

* **Strict**

  * pipeline fails on invalid data
* **Lenient**

  * invalid rows stored
  * valid rows continue

Rejected rows are stored in a dedicated Delta table.

---

## Observability

The pipeline includes:

* structured logging
* row count metrics
* validation output
* audit table (`pipeline_run_log`)
* Delta history (`DESCRIBE HISTORY`)

---

## Execution modes

The project supports two execution patterns:

* Databricks notebook entrypoint (`etl_entry.py`)
* Python package entrypoint (`python -m my_project`)

---

## Packaging

The project supports building a Python wheel:

```bash
python -m build
```

This prepares the project for artifact-based deployment.

---

## CI

GitHub Actions validates:

* formatting (`ruff format`)
* linting (`ruff`)
* tests (`pytest`)
* packaging (`python -m build`)

---

## Deployment

Deployment is defined using Databricks Asset Bundles:

* `databricks.yml` defines jobs as code
* GitHub Actions runs:

```bash
databricks bundle deploy
```

---

## Authentication (CI/CD)

Deployment uses OAuth-based authentication:

Required GitHub secrets:

* `DATABRICKS_HOST`
* `DATABRICKS_CLIENT_ID`
* `DATABRICKS_CLIENT_SECRET`

---

## Promotion strategy

The project follows a simple promotion model:

* **dev**

  * feature branches
  * lenient validation

* **test**

  * `main`
  * strict validation

* **prod**

  * tagged versions
  * strict validation

---

## Execution model (canonical)

This project follows a controlled DataOps execution model:

1. Develop locally in VS Code
2. Commit to feature branch
3. Create PR and merge to `main`
4. Deploy using GitHub Actions (Databricks Asset Bundles)
5. Run environment-specific job in Databricks:
   - dev → lenient
   - test → strict
   - prod → strict
6. Validate results using:
   - Delta tables
   - pipeline_run_log
   - monitoring queries

Notebook execution is used for development only.
Databricks Jobs are the canonical runtime.

---

## Deployment model

Deployment is managed through GitHub Actions and Databricks Asset Bundles.

- Deployment is triggered manually using workflow_dispatch
- Target environment is selected (dev, test, prod)
- Each target applies environment-specific configuration

Deployment does NOT trigger execution.

Execution is performed separately via Databricks Jobs.

---

## Current maturity

The project currently includes:

* reusable pipeline framework
* validation strategy
* rejected data handling
* audit trail
* job execution
* environment separation
* packaging
* CI/CD skeleton
* bundle-based deployment

---

## Known limitations

- Job parameters cannot be edited in Databricks UI for bundle-managed jobs
- Runtime behavior is controlled via DAB targets and deployment inputs
- `pipeline_version` is currently simplified and not tied to Git commits or tags
- Duplicate jobs may exist due to earlier bundle identity/path changes

---

## Key principles

- Code defines logic
- DAB defines deployment
- Jobs define execution
- Git defines promotion
- Delta tables define state

## Goal

To become a **practical, reusable DataOps framework for Databricks**, grounded in real-world consulting patterns.
