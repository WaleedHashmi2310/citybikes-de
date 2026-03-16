# Architecture & Design Decisions

## Overview

End-to-end data engineering pipeline ingesting European bikeshare station
data from the CityBikes API into a BigQuery data warehouse, orchestrated
by Kestra, transformed by dbt, and visualised in Looker Studio.

## Pipeline flow
```
CityBikes API  ──►  Cloud Run Job (Python)  ──►  GCS raw zone
                                                       │
data.citybik.es ──►  Dataproc Serverless (PySpark) ───┘
  (historical)                                         │
                                            BigQuery external tables
                                                       │
                                                  dbt Core
                                                       │
                                              BigQuery mart
                                                       │
                                            Looker Studio / Power BI
```

## Tech stack

| Component         | Technology              | Why                                              |
|-------------------|-------------------------|--------------------------------------------------|
| Orchestration     | Kestra on Cloud Run     | Single Docker container, no $200/mo Composer     |
| Ingestion         | Python + Pydantic       | Type-safe, testable, portable                    |
| Ingestion compute | Cloud Run Jobs          | Serverless, free tier covers 3× daily runs       |
| Historical load   | PySpark + Dataproc Serverless | One-time 12M row bulk load               |
| Data lake         | Google Cloud Storage    | Cheap, durable, native BigQuery integration      |
| Warehouse         | BigQuery                | Free tier covers this project indefinitely       |
| Transformation    | dbt Core                | Version-controlled SQL, tests, documentation     |
| Infrastructure    | Terraform               | Full reproducibility from scratch                |
| CI/CD             | GitHub Actions          | Lint, test, deploy on every PR                   |
| Visualisation     | Looker Studio           | Free, shareable link persists after GCP expiry   |
| Visualisation     | Power BI                | .pbix committed to repo, works offline           |
| Local dev         | Docker Compose + DuckDB | Full pipeline with zero cloud dependency         |

## Key architectural decisions

### Why not Databricks Community Edition?
CE clusters auto-terminate after 2 hours, cannot be scheduled, and cannot
be triggered programmatically by Kestra. For 9,000 rows/day it is also
massive overkill. Dataproc Serverless is used for the one-time historical
bulk load instead — pay for the minutes it runs, then it's gone.

### Why Cloud Run Jobs instead of always-on compute?
The ingestion job runs 3 times a day and takes ~30 seconds each time.
That is 90 seconds of compute daily. Cloud Run charges per 100ms and
the free tier covers 180,000 vCPU-seconds per month. Cost: $0.

### Why BigQuery external tables for the raw layer?
External tables point directly at GCS Parquet files — zero BigQuery
storage cost. Raw data stays in GCS which is cheaper and more portable.
Only the dbt mart layer uses native BigQuery tables.

### Why insert-overwrite instead of merge for incremental loads?
Each poll is an immutable timestamped snapshot — nothing needs updating.
Insert-overwrite by date partition is idempotent, cheap, and simple.

### Why dbt snapshots (SCD Type 2) for dim_station?
Station capacity changes when operators add or remove docks. Losing that
history means incorrect historical occupancy rate calculations. SCD Type 2
preserves a full audit trail with valid_from / valid_to timestamps.

## Portability after GCP credits expire

Three operational modes designed in from day one:

| Mode | State | What works |
|------|-------|------------|
| A | GCP active | Full live pipeline |
| B | GCP paused | Looker Studio cached view + repo snapshots |
| C | Fully local | Docker Compose + DuckDB, zero cloud needed |

The storage layer is abstracted behind a `StorageBackend` interface.
Switch from GCS to local by changing one environment variable.
