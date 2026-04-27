# Architecture

---

## Purpose

This repository is a practical DataOps learning project focused on:

* translating traditional DW/DataOps patterns into Databricks-native implementations
* building a reusable pipeline execution pattern
* establishing a local-first workflow with strong validation, observability, and deployment structure

---

## Architecture overview

The project follows a layered architecture:

```text
Execution Layer (notebooks)
    ↓
Pipeline Runner (run_pipeline)
    ↓
Pipeline Definitions
    ↓
Data Processing (ingest / transform / validate)
    ↓
Delta Tables (bronze / silver / rejected / audit)
```

---

## Design principles

### Python-first design

* Business logic lives in `src/`
* Notebooks act as runtime adapters

### Explicit contracts

* Silver layer defines data contract
* Validation is explicit and testable
* Schema changes are controlled

### Local-first development

* Development happens locally
* Databricks validates runtime behavior
* Git + PR flow controls changes

### Observability by design

* Structured logging
* Explicit validation output
* Persisted run metadata
* Delta history for traceability

### Incremental complexity

* Start simple
* Add structure gradually
* Avoid premature framework design

---

## Data model

### Catalog and schema

* Catalog: `workspace`
* Schema: `dataops_lab_<environment>`

### Tables

| Table              | Purpose           |
| ------------------ | ----------------- |
| bronze_customers   | Raw snapshot      |
| silver_customers   | Validated dataset |
| rejected_customers | Invalid rows      |
| pipeline_run_log   | Audit trail       |

---

## Data layer responsibilities

### Bronze

* Raw snapshot
* Minimal transformation
* Overwrite semantics

### Silver

* Cleaned and standardized
* Validation enforced
* Contract boundary

### Rejected

* Stores invalid rows
* Includes rejection reason

---

## Validation strategy

```text
validation_mode = strict | lenient
```

### Strict

* Reject → fail pipeline

### Lenient

* Reject → store + continue

---

## Pipeline execution model

### `run_pipeline(...)`

Handles:

* logging
* error handling
* audit writing

### Pipeline functions

Define:

* bronze step
* silver step

---

## Observability

### Logs

* step-level visibility
* row counts

### Rejected data

* invalid rows stored

### Audit table

Captures:

* run_id
* timestamp (UTC)
* pipeline_version
* validation_mode
* row counts
* status
* error message

### Delta history

* table-level lineage

---

## Testing strategy

### Transformation tests

* Spark-based
* business logic validation

### Validation tests

* strict vs lenient behavior

### Audit tests

* metadata correctness

### Pipeline tests

* orchestration behavior
* mocked side effects

---

## Deployment-oriented structure

The project separates:

* source code (`src/`)
* runtime adapter (`notebooks/`)
* package artifact (wheel)
* execution target (Databricks Job)
* environment model (dev/test/prod)

---

## Authentication model

CI/CD deployment uses OAuth service credentials:

* client_id
* client_secret

This enables non-user-based deployment.

---

## Promotion model

Promotion is Git-driven:

* dev → feature branches
* test → `main`
* prod → tagged releases

Ensures:

* controlled releases
* environment consistency
* traceable execution

---

## Bundle identity

Bundle-managed resources are defined by:

* bundle name
* target
* deployment identity
* root_path

To avoid duplication:

* root_path is explicitly set
* one deployment identity is preferred
* one job per environment is maintained

---

## Behavior summary

| Environment | Validation | Expected result |
|------------|-----------|---------------|
| dev        | lenient   | succeeds with rejected rows |
| test       | strict    | fails if rejected rows exist |
| prod       | strict    | fails if rejected rows exist |

---

## Failure handling model

Pipeline failures are classified into categories:

- DATA_QUALITY → caused by validation failures (not retryable)
- PERMISSION → caused by access issues (not retryable)
- PLATFORM → caused by Spark/platform issues (retryable)
- PROCESSING → unexpected failures (potentially retryable)

Each run records:
- failure_stage
- failure_category
- retryable flag

This supports operational decision-making and future retry strategies.

---

## Monitoring approach

Monitoring is based on the `pipeline_run_log` Delta table.

Key metrics:
- run status (SUCCESS / FAILED)
- failure category
- rejected row count
- run duration

Monitoring is performed using:
- SQL queries in Databricks
- reusable helper functions in `monitoring.py`

This enables:
- environment comparison
- failure analysis
- runtime trend analysis

---

## Current runtime limitation

In the current Databricks Free Edition environment, the canonical runtime uses a notebook task because job compute / Python wheel task execution is not available.

The production-oriented target pattern remains wheel-based execution using `python_wheel_task`, but this requires a Databricks workspace with compatible job compute.

---

## Current position

The project provides:

* reusable pipeline framework
* validation + rejected handling
* audit logging
* job execution
* environment separation
* packaging foundation
* CI/CD skeleton
* bundle-based deployment

---

## Future direction

Next improvements:

* monitoring and alerting
* failure handling patterns
* promotion automation
* multi-pipeline framework
* config-driven pipelines
