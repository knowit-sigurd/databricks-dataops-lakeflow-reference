# Architecture

---

## Purpose

This repository explores DataOps patterns using **Databricks-native capabilities**, focusing on:

- Spark Declarative Pipelines (SDP)
- Serverless execution
- Databricks Asset Bundles (DAB)
- Git-driven deployment and promotion

The goal is to compare this approach with a custom DataOps framework (v2 repo).

---

## Architecture overview

The project follows a Databricks-native pipeline model:

```text
Declarative Pipeline (SDP)
    ↓
Databricks Pipeline Engine
    ↓
Serverless Compute
    ↓
Delta Tables (bronze / silver)