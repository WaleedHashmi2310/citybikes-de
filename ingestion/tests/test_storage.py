from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq
from src.models import NetworkSnapshot, StationSnapshot
from src.storage import LocalBackend


def make_snapshot() -> NetworkSnapshot:
    """Create a minimal NetworkSnapshot for testing."""
    station = StationSnapshot(
        id="test-1",
        name="Test Station",
        latitude=48.8566,
        longitude=2.3522,
        timestamp=datetime(2026, 3, 17, 12, 0, 0, tzinfo=UTC),
        free_bikes=5,
        empty_slots=10,
        network_id="velib",
    )
    return NetworkSnapshot(
        network_id="velib",
        city="Paris",
        country="France",
        stations=[station],
    )


class TestLocalBackend:
    def test_write_creates_parquet_file(self, tmp_path):
        """LocalBackend creates a Parquet file at the correct path."""
        backend = LocalBackend(base_path=str(tmp_path))
        snap = make_snapshot()

        path = backend.write(snap)

        assert Path(path).exists()
        assert path.endswith(".parquet")

    def test_written_file_has_correct_row_count(self, tmp_path):
        """Written Parquet file contains the right number of rows."""
        backend = LocalBackend(base_path=str(tmp_path))
        snap = make_snapshot()

        path = backend.write(snap)
        table = pq.ParquetFile(path).read()

        assert len(table) == 1

    def test_written_file_has_correct_columns(self, tmp_path):
        """Written Parquet file contains all expected columns."""
        backend = LocalBackend(base_path=str(tmp_path))
        snap = make_snapshot()

        path = backend.write(snap)
        table = pq.ParquetFile(path).read()

        assert "free_bikes" in table.column_names
        assert "occupancy_rate" in table.column_names
        assert "network_id" in table.column_names
        assert "ingested_at" in table.column_names

    def test_path_uses_hive_partitioning(self, tmp_path):
        """Output path follows Hive partition format."""
        backend = LocalBackend(base_path=str(tmp_path))
        snap = make_snapshot()

        path = backend.write(snap)

        assert "network_id=velib" in path
        assert "year=2026" in path
        assert "month=03" in path
        assert "day=" in path  # day is dynamic — just check the key exists

    def test_idempotent_write(self, tmp_path):
        """Writing the same snapshot twice overwrites without error."""
        backend = LocalBackend(base_path=str(tmp_path))
        snap = make_snapshot()

        path1 = backend.write(snap)
        path2 = backend.write(snap)

        assert path1 == path2
        assert Path(path2).exists()
