from datetime import UTC, datetime

import pytest
from src.models import NetworkSnapshot, StationExtra, StationSnapshot


def make_station(**kwargs) -> StationSnapshot:
    """Helper that creates a valid StationSnapshot with sensible defaults."""
    defaults = {
        "id": "test-station-1",
        "name": "Test Station",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "timestamp": datetime(2026, 3, 17, 12, 0, 0, tzinfo=UTC),
        "free_bikes": 5,
        "empty_slots": 10,
        "network_id": "velib",
    }
    defaults.update(kwargs)
    return StationSnapshot(**defaults)


class TestTimestampFix:
    def test_invalid_timestamp_fixed(self):
        """Timestamps ending in +00:00Z must be fixed automatically."""
        station = make_station(timestamp="2026-03-17T12:00:00.000000+00:00Z")
        assert station.timestamp.tzinfo is not None

    def test_valid_timestamp_unchanged(self):
        """Valid ISO timestamps must pass through unchanged."""
        station = make_station(timestamp="2026-03-17T12:00:00+00:00")
        assert station.timestamp.year == 2026


class TestDerivedFields:
    def test_capacity_from_empty_slots(self):
        """capacity = free_bikes + empty_slots when slots not in extra."""
        station = make_station(free_bikes=5, empty_slots=10)
        assert station.capacity == 15

    def test_capacity_prefers_extra_slots(self):
        """extra.slots takes priority over derived capacity."""
        station = make_station(
            free_bikes=5,
            empty_slots=10,
            extra=StationExtra(slots=20),
        )
        assert station.capacity == 20

    def test_occupancy_rate(self):
        """occupancy_rate = free_bikes / capacity."""
        station = make_station(free_bikes=6, empty_slots=4)
        assert station.occupancy_rate == 0.6

    def test_occupancy_rate_none_for_dockless(self):
        """Dockless stations have no capacity so occupancy_rate is None."""
        station = make_station(free_bikes=3, empty_slots=None)
        assert station.occupancy_rate is None

    def test_ebike_share(self):
        """ebike_share = ebikes / free_bikes."""
        station = make_station(
            free_bikes=10,
            extra=StationExtra(ebikes=4),
        )
        assert station.ebike_share == 0.4

    def test_is_empty(self):
        station = make_station(free_bikes=0, empty_slots=10)
        assert station.is_empty is True

    def test_is_full(self):
        station = make_station(free_bikes=10, empty_slots=0)
        assert station.is_full is True

    def test_is_offline(self):
        station = make_station(
            free_bikes=0,
            empty_slots=0,
            extra=StationExtra(renting=0, returning=0),
        )
        assert station.is_offline is True

    def test_not_offline_when_has_bikes(self):
        station = make_station(free_bikes=5, empty_slots=5)
        assert station.is_offline is False


class TestValidators:
    def test_negative_free_bikes_rejected(self):
        with pytest.raises(Exception):
            make_station(free_bikes=-1)

    def test_invalid_latitude_rejected(self):
        with pytest.raises(Exception):
            make_station(latitude=91.0)

    def test_invalid_longitude_rejected(self):
        with pytest.raises(Exception):
            make_station(longitude=181.0)


class TestNetworkSnapshot:
    def test_station_count(self):
        stations = [make_station(id=f"s{i}") for i in range(5)]
        snap = NetworkSnapshot(
            network_id="velib",
            city="Paris",
            country="France",
            stations=stations,
        )
        assert snap.station_count == 5

    def test_active_stations_excludes_offline(self):
        online = make_station(id="s1", free_bikes=5, empty_slots=5)
        offline = make_station(
            id="s2",
            free_bikes=0,
            empty_slots=0,
            extra=StationExtra(renting=0, returning=0),
        )
        snap = NetworkSnapshot(
            network_id="velib",
            city="Paris",
            country="France",
            stations=[online, offline],
        )
        assert snap.active_stations == 1
