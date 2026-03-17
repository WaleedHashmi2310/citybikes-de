"""
CityBikes DE Pipeline — Main DAG

Orchestrates the full CityBikes data pipeline:
  1. Trigger Cloud Run ingestion job (fetches API data → GCS)

Phase 3 will add:
  2. dbt staging models
  3. dbt mart models

Schedule: 3x daily at 08:00, 13:00, 19:00 UTC
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.cloud_run import (
    CloudRunExecuteJobOperator,
)

# ============================================================
# DAG configuration
# ============================================================
default_args = {
    "owner": "citybikes-de",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="citybikes_pipeline",
    description="CityBikes DE — fetch bikeshare data from 4 European cities",
    schedule="0 8,13,19 * * *",
    start_date=datetime(2026, 3, 18),
    catchup=False,
    default_args=default_args,
    tags=["citybikes", "ingestion", "production"],
) as dag:

    # --------------------------------------------------------
    # Task 1: Trigger Cloud Run ingestion job
    # Fetches from CityBikes API → validates → writes Parquet to GCS
    # --------------------------------------------------------
    run_ingestion = CloudRunExecuteJobOperator(
        task_id="run_citybikes_ingestion",
        project_id="citybikes-de",
        region="europe-west3",
        job_name="citybikes-ingestion",
        gcp_conn_id="google_cloud_default",
        deferrable=True,
    )

    # Task dependency chain
    # Phase 3 will extend this:
    # run_ingestion >> run_dbt_staging >> run_dbt_marts
    run_ingestion
