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