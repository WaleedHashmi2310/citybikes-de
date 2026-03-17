"""
CityBikes DE — Monthly Snapshot DAG

Exports all BigQuery mart tables to GCS as Parquet files.
These snapshots are downloaded and committed to the repo
as the post-GCP-expiry fallback strategy.

Schedule: 1st of every month at 02:00 UTC
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)

default_args = {
    "owner": "citybikes-de",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}

GCP_PROJECT = "citybikes-de"
GCS_BUCKET = "citybikes-snapshots-citybikes-de"
BQ_DATASET = "citybikes_mart"

TABLES = [
    "fact_station_snapshot",
    "fact_station_daily",
    "fact_network_daily",
    "dim_station",
    "dim_network",
    "dim_date",
]


def make_export_config(table: str, export_date: str) -> dict:
    """Build BigQuery export job config for one table."""
    return {
        "extract": {
            "sourceTable": {
                "projectId": GCP_PROJECT,
                "datasetId": BQ_DATASET,
                "tableId": table,
            },
            "destinationUris": [f"gs://{GCS_BUCKET}/snapshots/{export_date}/{table}/*.parquet"],
            "destinationFormat": "PARQUET",
        }
    }


with DAG(
    dag_id="citybikes_monthly_snapshot",
    description="Export BigQuery mart tables to GCS Parquet snapshots",
    schedule="0 2 1 * *",
    start_date=datetime(2026, 3, 1),
    catchup=False,
    default_args=default_args,
    tags=["citybikes", "snapshot", "monthly"],
) as dag:

    export_date = "{{ ds[:7] }}"  # YYYY-MM format

    previous_task = None
    for table in TABLES:
        export_task = BigQueryInsertJobOperator(
            task_id=f"export_{table}",
            configuration=make_export_config(table, export_date),
            project_id=GCP_PROJECT,
            gcp_conn_id="google_cloud_default",
        )

        if previous_task:
            previous_task >> export_task
        previous_task = export_task
