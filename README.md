# databricks-dataops-lab-sdp

A **Databricks-native DataOps learning project** focused on using:

- Databricks Asset Bundles (DAB)
- Lakeflow / Spark Declarative Pipelines (SDP)
- Serverless workflows
- Git-driven promotion

---

## Purpose

This repository explores how to implement DataOps patterns using **platform-native capabilities** instead of custom frameworks.

The goal is to compare:

- custom pipeline framework (v2 repo)
vs
- Databricks-native pipelines (this repo)

---

## Architecture direction

This project follows a **Databricks-native approach**:

- Pipelines defined declaratively (SDP)
- Orchestration handled by Databricks
- Execution on serverless compute
- Deployment via Databricks Asset Bundles
- Promotion controlled through Git

---

## Execution model

This project follows a Databricks-native promotion model:

```text
PR → test (validation)
main → prod

---

## Architecture decision

| Area                   | v2   | SDP        |
| ---------------------- | ---- | ---------- |
| Who controls execution | You  | Databricks |
| Complexity             | High | Low        |
| Flexibility            | High | Medium     |


| Area             | v2          | SDP                 |
| ---------------- | ----------- | ------------------- |
| Validation logic | custom code | expectations        |
| Rejected rows    | ✔           | ❌ (needs extension) |
| Observability    | SQL-based   | UI-based            |


| Area        | v2      | SDP |
| ----------- | ------- | --- |
| Audit table | ✔       | ❌   |
| UI          | ❌       | ✔   |
| Lineage     | limited | ✔   |


| Area          | v2 | SDP         |
| ------------- | -- | ----------- |
| Wheel support | ✔  | not primary |
| DAB usage     | ✔  | ✔           |
| Serverless    | ❌  | ✔           |


| Area              | v2       | SDP                   |
| ----------------- | -------- | --------------------- |
| Multi-pipeline    | registry | independent pipelines |
| Complexity growth | high     | controlled            |
| Team workflow     | harder   | easier                |


If I had to build a new client solution today,
which approach would I choose?
- It depends on the use. Propably SDP approach as primary architecture

This project evaluated two approaches:

- custom DataOps framework (v2)
- Databricks-native pipelines (SDP)

Decision:

SDP is the preferred approach for production systems due to:
- reduced complexity
- built-in observability
- serverless execution
- better alignment with platform capabilities

Custom frameworks should only be used when platform features are insufficient.