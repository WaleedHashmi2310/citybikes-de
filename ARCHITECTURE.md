# Architecture & Design Decisions

## Overview

End-to-end data engineering pipeline ingesting European bikeshare station
data from the CityBikes API into a BigQuery data warehouse, orchestrated
by Apache Airflow on Astronomer Astro, transformed by dbt, and visualised
in Looker Studio.

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

| Component         | Technology                    | Why                                          |
|-------------------|-------------------------------|----------------------------------------------|
| Orchestration     | Apache Airflow on Astro       | Industry standard, free managed tier, GCP native operators |
| Ingestion         | Python + Pydantic             | Type-safe, testable, portable                |
| Ingestion compute | Cloud Run Jobs                | Serverless, free tier covers 3× daily runs   |
| Historical load   | PySpark + Dataproc Serverless | One-time 12M row bulk load                   |
| Data lake         | Google Cloud Storage          | Cheap, durable, native BigQuery integration  |
| Warehouse         | BigQuery                      | Free tier covers this project indefinitely   |
| Transformation    | dbt Core                      | Version-controlled SQL, tests, documentation |
| Infrastructure    | Terraform                     | Full reproducibility from scratch            |
| CI/CD             | GitHub Actions                | Lint, test, deploy on every PR               |
| Visualisation     | Looker Studio                 | Free, shareable link persists after GCP expiry |
| Visualisation     | Power BI                      | .pbix committed to repo, works offline       |
| Local dev         | Astro CLI + DuckDB            | Full pipeline with zero cloud dependency     |

## Key architectural decisions

### Why Airflow over Kestra?
Kestra proved incompatible with Cloud Run's health check model due to its
long Java startup time (2-3 minutes) exceeding Cloud Run's timeout window.
Airflow on Astronomer Astro provides a permanently running managed scheduler
with native GCP operators, free tier, and broader industry recognition.

### Why Astronomer Astro over Cloud Composer?
Cloud Composer (managed Airflow on GCP) costs ~$200/month minimum.
Astronomer Astro's free tier provides a fully managed Airflow deployment
that runs indefinitely outside GCP — meaning it survives GCP credit expiry.

### Why Cloud Run Jobs for ingestion?
The ingestion job runs 3 times a day and takes ~30 seconds each time.
Cloud Run charges per 100ms. The free tier covers 180,000 vCPU-seconds
per month. Cost: $0.

### Why BigQuery external tables for the raw layer?
External tables point directly at GCS Parquet files — zero BigQuery
storage cost. Raw data stays in GCS (cheaper, portable).

### Why insert-overwrite for incremental loads?
Each poll is an immutable timestamped snapshot — nothing needs updating.
Insert-overwrite by date partition is idempotent, cheap, and simple.

### Why dbt snapshots (SCD Type 2) for dim_station?
Station capacity changes when operators add or remove docks.
SCD Type 2 preserves a full audit trail with valid_from/valid_to timestamps.

## Portability after GCP credits expire

| Mode | State | What works |
|------|-------|------------|
| A | GCP active | Full live pipeline |
| B | GCP paused | Looker Studio cached + repo snapshots + Astro still runs |
| C | Fully local | Astro local dev + DuckDB, zero cloud needed |

Note: Airflow on Astro free tier continues running even after GCP credits
expire — the scheduler keeps working, it just has no job to trigger.
