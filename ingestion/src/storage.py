import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.models import NetworkSnapshot

logger = logging.getLogger(__name__)


# ============================================================
# PyArrow schema — defines the exact Parquet column types
# Must match the Pydantic model fields exactly
# ============================================================
STATION_SCHEMA = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("name", pa.string()),
        pa.field("latitude", pa.float64()),
        pa.field("longitude", pa.float64()),
        pa.field("timestamp", pa.timestamp("us", tz="UTC")),
        pa.field("free_bikes", pa.int32()),
        pa.field("empty_slots", pa.int32()),
        pa.field("network_id", pa.string()),
        pa.field("ingested_at", pa.timestamp("us", tz="UTC")),
        pa.field("capacity", pa.int32()),
        pa.field("occupancy_rate", pa.float64()),
        pa.field("ebike_share", pa.float64()),
        pa.field("is_empty", pa.bool_()),
        pa.field("is_full", pa.bool_()),
        pa.field("is_offline", pa.bool_()),
        pa.field("data_latency_minutes", pa.float64()),
        # Extra fields flattened
        pa.field("extra_uid", pa.string()),
        pa.field("extra_ebikes", pa.int32()),
        pa.field("extra_normal_bikes", pa.int32()),
        pa.field("extra_has_ebikes", pa.bool_()),
        pa.field("extra_slots", pa.int32()),
        pa.field("extra_altitude", pa.float64()),
        pa.field("extra_renting", pa.int32()),
        pa.field("extra_returning", pa.int32()),
    ]
)


def _snapshot_to_table(snapshot: NetworkSnapshot) -> pa.Table:
    """Convert a NetworkSnapshot to a PyArrow Table for Parquet writing."""
    rows = []
    for s in snapshot.stations:
        rows.append(
            {
                "id": s.id,
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "timestamp": s.timestamp,
                "free_bikes": s.free_bikes,
                "empty_slots": s.empty_slots,
                "network_id": s.network_id,
                "ingested_at": s.ingested_at,
                "capacity": s.capacity,
                "occupancy_rate": s.occupancy_rate,
                "ebike_share": s.ebike_share,
                "is_empty": s.is_empty,
                "is_full": s.is_full,
                "is_offline": s.is_offline,
                "data_latency_minutes": s.data_latency_minutes,
                "extra_uid": str(s.extra.uid) if s.extra.uid is not None else None,
                "extra_ebikes": s.extra.ebikes,
                "extra_normal_bikes": s.extra.normal_bikes,
                "extra_has_ebikes": s.extra.has_ebikes,
                "extra_slots": s.extra.slots,
                "extra_altitude": s.extra.altitude,
                "extra_renting": s.extra.renting,
                "extra_returning": s.extra.returning,
            }
        )
    return pa.Table.from_pylist(rows, schema=STATION_SCHEMA)


def _build_path(network_id: str, polled_at: datetime, base: str) -> str:
    """
    Build the output path with Hive-style partitioning.
    Example:
      citybikes/live/network_id=velib/year=2026/month=03/day=17/poll=12/
    This partitioning lets BigQuery and dbt query efficiently by date.
    """
    return (
        f"{base}/citybikes/live"
        f"/network_id={network_id}"
        f"/year={polled_at.year:04d}"
        f"/month={polled_at.month:02d}"
        f"/day={polled_at.day:02d}"
        f"/poll={polled_at.hour:02d}"
        f"/part-0.parquet"
    )


# ============================================================
# Abstract base class — defines the interface both backends share
# ============================================================
class StorageBackend(ABC):
    @abstractmethod
    def write(self, snapshot: NetworkSnapshot) -> str:
        """Write a NetworkSnapshot and return the path it was written to."""


# ============================================================
# Local backend — writes to disk, no GCP needed
# ============================================================
class LocalBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path

    def write(self, snapshot: NetworkSnapshot) -> str:
        path = _build_path(snapshot.network_id, snapshot.polled_at, self.base_path)
        full_path = Path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        table = _snapshot_to_table(snapshot)
        pq.write_table(table, full_path)
        logger.info(f"Written locally: {path} ({len(snapshot.stations)} rows)")
        return path


# ============================================================
# GCS backend — writes to Google Cloud Storage
# ============================================================
class GCSBackend(StorageBackend):
    def __init__(self, bucket_name: str):
        from google.cloud import storage

        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def write(self, snapshot: NetworkSnapshot) -> str:
        import io

        path = _build_path(snapshot.network_id, snapshot.polled_at, "")
        # Remove leading slash for GCS blob path
        blob_path = path.lstrip("/")
        table = _snapshot_to_table(snapshot)
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)
        blob = self.bucket.blob(blob_path)
        blob.upload_from_file(buffer, content_type="application/octet-stream")
        full_path = f"gs://{self.bucket_name}/{blob_path}"
        logger.info(f"Written to GCS: {full_path} ({len(snapshot.stations)} rows)")
        return full_path


# ============================================================
# Factory function — returns the right backend based on env var
# ============================================================
def get_storage_backend() -> StorageBackend:
    """
    Read STORAGE_BACKEND from environment and return the right backend.
    STORAGE_BACKEND=local  → LocalBackend (default, no GCP needed)
    STORAGE_BACKEND=gcs    → GCSBackend (production)
    """
    backend = os.getenv("STORAGE_BACKEND", "local").lower()

    if backend == "gcs":
        bucket = os.getenv("GCS_BUCKET_RAW")
        if not bucket:
            raise ValueError("GCS_BUCKET_RAW must be set when STORAGE_BACKEND=gcs")
        logger.info(f"Using GCS backend: gs://{bucket}")
        return GCSBackend(bucket_name=bucket)

    # Default: local
    base_path = os.getenv("LOCAL_STORAGE_PATH", "/tmp/citybikes")
    logger.info(f"Using local backend: {base_path}")
    return LocalBackend(base_path=base_path)
